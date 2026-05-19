import json
from pathlib import Path

import structlog
from sqlalchemy.orm import Session

from app.ai.vertex_client import VertexAIClient, load_prompt
from app.core.config import get_settings
from app.storage.local_storage import LocalImageStorage
from app.utils.geometry import clamp_polygon_to_image
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState

logger = structlog.get_logger(__name__)


def _polygon_for(index: int, width: int = 1280, height: int = 720) -> list[list[float]]:
    """Deterministic fallback polygon grid."""
    x = 220 + (index % 3) * 260
    y = 430 + (index // 3) * 90
    return clamp_polygon_to_image(
        [[x, y], [x + 220, y], [x + 240, y + 120], [x - 20, y + 120]], width, height
    )


def plan_placements_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "plan_placements")
        settings = get_settings()
        selected = state.get("selected_products", [])

        if not selected:
            return {"placement_plan": {"placements": []}, "selected_products": []}

        if settings.mock_ai or not settings.vertex_project_id:
            logger.info("plan_placements_mock")
            return _mock_placements(state)

        # Real AI placement planning
        logger.info("plan_placements_vertex_ai")
        try:
            return _ai_placements(state, settings)
        except Exception as exc:
            logger.warning("plan_placements_ai_failed_fallback", error=str(exc))
            return _mock_placements(state)

    return node


def _ai_placements(state: DesignWorkflowState, settings) -> dict:
    client = VertexAIClient(settings)
    prompt_template = load_prompt("placement_planning.md")
    room_analysis = state.get("room_analysis", {})
    selected = state.get("selected_products", [])

    # Build a compact product list for the prompt
    product_summaries = []
    for p in selected:
        product_summaries.append({
            "product_id": p["product_id"],
            "role": p["role"],
            "name": p.get("name", ""),
            "category": p.get("category", ""),
            "visual_weight": p.get("metadata", {}).get("visual_weight"),
            "spatial_feel": p.get("metadata", {}).get("spatial_feel"),
        })

    prompt = (
        f"{prompt_template}\n\n"
        f"Room analysis:\n{json.dumps(room_analysis, indent=2)}\n\n"
        f"Selected products:\n{json.dumps(product_summaries, indent=2)}\n"
    )

    # Include room image if available
    images: list[Path] = []
    room_image_path = state.get("room_image_path", "")
    if room_image_path:
        storage = LocalImageStorage(settings)
        resolved = storage.resolve_room_image(room_image_path)
        if resolved.exists():
            images.append(resolved)

    from pydantic import BaseModel, Field
    from app.schemas.ai_outputs import ProductPlacement

    class PlacementPlanResponse(BaseModel):
        placements: list[ProductPlacement] = Field(default_factory=list)

    result = client.generate_json(
        prompt, PlacementPlanResponse, images=images or None, model_tier="pro"
    )

    # Merge AI placements back into selected_products
    placement_map = {str(p.product_id): p for p in result.placements}
    for product in selected:
        placement = placement_map.get(str(product["product_id"]))
        if placement:
            product["polygon"] = placement.target_polygon
        else:
            # Fallback: assign a generic polygon
            idx = selected.index(product)
            product["polygon"] = _polygon_for(idx)

    placements = [p.model_dump(mode="json") for p in result.placements]
    # Fill in any missing placements
    placed_ids = {str(p.product_id) for p in result.placements}
    for i, product in enumerate(selected):
        if str(product["product_id"]) not in placed_ids:
            placements.append({
                "product_id": product["product_id"],
                "role": product["role"],
                "placement_type": "new",
                "target_polygon": product["polygon"],
                "depth_order": i,
                "confidence": 0.4,
                "notes": "Fallback placement — AI did not assign a position.",
            })

    return {"placement_plan": {"placements": placements}, "selected_products": selected}


def _mock_placements(state: DesignWorkflowState) -> dict:
    selected = state.get("selected_products", [])
    placements = []
    counters: dict[int, int] = {}
    for product in selected:
        design_index = int(product["design_index"])
        slot = counters.get(design_index, 0)
        counters[design_index] = slot + 1
        polygon = _polygon_for(slot)
        product["polygon"] = polygon
        placements.append({
            "product_id": product["product_id"],
            "role": product["role"],
            "placement_type": "new",
            "target_polygon": polygon,
            "depth_order": slot,
            "confidence": 0.6,
        })
    return {"placement_plan": {"placements": placements}, "selected_products": selected}
