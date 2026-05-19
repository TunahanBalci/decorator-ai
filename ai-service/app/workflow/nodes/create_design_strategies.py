import json

import structlog
from sqlalchemy.orm import Session

from app.ai.vertex_client import VertexAIClient, load_prompt
from app.core.config import get_settings
from app.schemas.ai_outputs import DesignStrategy
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState

logger = structlog.get_logger(__name__)

DEFAULT_ROLES = ["coffee_table", "rug", "floor_lamp"]
SUPPORTED_ROLES = {
    "dining_table",
    "dining_chair",
    "wardrobe",
    "dresser",
    "nightstand",
    "console_table",
    "mirror",
    "bed",
    "coffee_table",
    "sofa",
    "armchair",
    "bookshelf",
    "tv_unit",
    "floor_lamp",
    "carpet",
    "rug",
    "side_table",
    "desk",
    "storage_unit",
}
ROOM_DEFAULT_ROLES = {
    "living_room": ["sofa", "coffee_table", "rug", "floor_lamp"],
    "bedroom": ["bed", "nightstand", "dresser", "rug"],
    "dining_room": ["dining_table", "dining_chair", "console_table"],
    "office": ["desk", "bookshelf", "floor_lamp"],
}


def create_design_strategies_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "create_design_strategies")
        settings = get_settings()
        prefs = state.get("user_preferences", {})
        room_analysis = state.get("room_analysis", {})
        count = int(state.get("requested_design_count") or 1)

        if settings.mock_ai or not settings.vertex_project_id:
            logger.info("create_design_strategies_mock")
            return _mock_strategies(prefs, count, room_analysis)

        # Real AI strategy generation
        logger.info("create_design_strategies_vertex_ai")
        client = VertexAIClient(settings)
        prompt_template = load_prompt("design_strategy.md")

        prompt_room_analysis = _strategy_room_analysis(
            room_analysis,
            settings.ignore_existing_furniture,
        )
        prompt = (
            f"{prompt_template}\n\n"
            f"Room analysis:\n{json.dumps(prompt_room_analysis, indent=2)}\n\n"
            f"User preferences:\n{json.dumps(prefs, indent=2)}\n\n"
            f"Ignore existing furniture: {settings.ignore_existing_furniture}\n\n"
            f"Requested design count: {count}\n"
        )

        from pydantic import BaseModel, Field

        class DesignStrategiesResponse(BaseModel):
            strategies: list[DesignStrategy] = Field(alias="strategies", default_factory=list)

            class Config:
                populate_by_name = True

            @classmethod
            def _try_parse(cls, data):
                """Handle both list and object responses from AI."""
                if isinstance(data, list):
                    return cls(strategies=data)
                return cls.model_validate(data)

        try:
            from app.utils.json_utils import extract_json_object

            parts = [{"text": prompt}]
            text = client._stream_generate(
                parts, temperature=0.4, response_mime_type="application/json", model_tier="pro"
            )
            parsed = extract_json_object(text)
            if isinstance(parsed, list):
                strategies = [DesignStrategy.model_validate(s) for s in parsed]
            else:
                strategy_items = parsed.get("strategies", parsed.get("designs", [parsed]))
                strategies = [DesignStrategy.model_validate(s) for s in strategy_items]
        except Exception as exc:
            logger.warning("design_strategy_ai_failed_fallback", error=str(exc))
            return _mock_strategies(prefs, count, room_analysis)

        sanitized = [_sanitize_strategy(s, room_analysis, prefs) for s in strategies[:count]]
        return {"design_strategies": [s.model_dump() for s in sanitized]}

    return node


def _mock_strategies(prefs: dict, count: int, room_analysis: dict | None = None) -> dict:
    room_type = _room_type(room_analysis or {})
    requested = [
        role for role in prefs.get("requested_furniture_types", []) if role in SUPPORTED_ROLES
    ]
    roles = requested or ROOM_DEFAULT_ROLES.get(room_type, DEFAULT_ROLES)
    strategies = []
    for index in range(1, count + 1):
        strategy = DesignStrategy(
            design_index=index,
            title=f"{(prefs.get('design_style') or 'Balanced').title()} Design {index}",
            style=prefs.get("design_style") or "balanced",
            furniture_roles=roles,
            notes=prefs.get("extra_preferences"),
        )
        strategies.append(strategy.model_dump())
    return {"design_strategies": strategies}


def _strategy_room_analysis(room_analysis: dict, ignore_existing: bool) -> dict:
    if not ignore_existing:
        return room_analysis
    return {
        "room_type": _room_type(room_analysis),
        "architectural_context": room_analysis.get("architectural_context") or {},
        "available_placement_zones": room_analysis.get("available_placement_zones") or [],
        "constraints": room_analysis.get("constraints") or {},
        "lighting": room_analysis.get("lighting"),
        "color_palette": room_analysis.get("color_palette") or [],
        "detected_styles": room_analysis.get("detected_styles") or [],
        "existing_objects_ignored": True,
    }


def _room_type(room_analysis: dict) -> str:
    architectural_context = room_analysis.get("architectural_context") or {}
    return architectural_context.get("room_type") or room_analysis.get("room_type") or "living_room"


def _sanitize_strategy(
    strategy: DesignStrategy,
    room_analysis: dict,
    prefs: dict,
) -> DesignStrategy:
    roles = [role for role in strategy.furniture_roles if role in SUPPORTED_ROLES]
    if not roles:
        roles = ROOM_DEFAULT_ROLES.get(_room_type(room_analysis), DEFAULT_ROLES)
    return DesignStrategy(
        design_index=strategy.design_index,
        title=strategy.title,
        style=strategy.style or prefs.get("design_style") or "balanced",
        furniture_roles=roles,
        notes=strategy.notes,
    )
