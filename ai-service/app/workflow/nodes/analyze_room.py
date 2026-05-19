import structlog
from sqlalchemy.orm import Session

from app.ai.vertex_client import VertexAIClient, load_prompt
from app.core.config import get_settings
from app.schemas.ai_outputs import RoomAnalysisResult
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState

logger = structlog.get_logger(__name__)


def analyze_room_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "analyze_room")
        settings = get_settings()

        if settings.mock_ai or not settings.vertex_project_id:
            logger.info("analyze_room_mock")
            floor_polygon = [[260, 430], [1020, 430], [1120, 700], [160, 700]]
            prefs = state.get("user_preferences", {})
            result = RoomAnalysisResult(
                room_type="living_room",
                detected_styles=[prefs.get("design_style") or "unknown"],
                color_palette=prefs.get("colors") or [],
                temperature=prefs.get("temperature"),
                lighting="unknown",
                existing_furniture=[],
                existing_objects=[],
                architectural_context={
                    "room_type": "living_room",
                    "floor_area": floor_polygon,
                    "lighting": "unknown",
                    "perspective": {},
                    "empty_room_style_hint": prefs.get("design_style"),
                },
                available_placement_zones=[
                    {"label": "central_floor", "polygon": floor_polygon}
                ],
                constraints={},
                confidence=0.65,
            )
            return {"room_analysis": result.model_dump()}

        # Real Vertex AI room analysis
        logger.info("analyze_room_vertex_ai")
        from pathlib import Path

        client = VertexAIClient(settings)
        prompt_template = load_prompt("room_analysis.md")
        room_dims = state.get("room_dimensions", {})
        prefs = state.get("user_preferences", {})

        prompt = (
            f"{prompt_template}\n\n"
            "System config:\n"
            f"ignore_existing_furniture: {settings.ignore_existing_furniture}\n"
            f"remove_existing_furniture: {settings.remove_existing_furniture}\n\n"
            f"Room dimensions: {room_dims}\n"
            f"User preferences: {prefs}\n"
        )

        # Try to include the room image if it exists locally
        from app.storage.local_storage import LocalImageStorage
        images: list[Path] = []
        room_image_path = state.get("room_image_path", "")
        storage = LocalImageStorage(settings)
        resolved = storage.resolve_room_image(room_image_path)
        if resolved.exists():
            images.append(resolved)

        result = client.generate_json(
            prompt,
            RoomAnalysisResult,
            images=images or None,
            model_tier="pro",
        )
        analysis = result.model_dump()
        if settings.ignore_existing_furniture:
            analysis["design_uses_existing_objects"] = False
        return {"room_analysis": analysis}

    return node
