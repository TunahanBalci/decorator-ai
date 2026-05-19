import json

import structlog
from sqlalchemy.orm import Session

from app.ai.vertex_client import VertexAIClient, load_prompt
from app.core.config import get_settings
from app.schemas.ai_outputs import DesignStrategy
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState

logger = structlog.get_logger(__name__)

DEFAULT_ROLES = ["coffee_table", "carpet", "floor_lamp"]


def create_design_strategies_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "create_design_strategies")
        settings = get_settings()
        prefs = state.get("user_preferences", {})
        room_analysis = state.get("room_analysis", {})
        count = int(state.get("requested_design_count") or 1)

        if settings.mock_ai or not settings.vertex_project_id:
            logger.info("create_design_strategies_mock")
            return _mock_strategies(prefs, count)

        # Real AI strategy generation
        logger.info("create_design_strategies_vertex_ai")
        client = VertexAIClient(settings)
        prompt_template = load_prompt("design_strategy.md")

        prompt = (
            f"{prompt_template}\n\n"
            f"Room analysis:\n{json.dumps(room_analysis, indent=2)}\n\n"
            f"User preferences:\n{json.dumps(prefs, indent=2)}\n\n"
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
                strategies = [DesignStrategy.model_validate(s) for s in parsed.get("strategies", parsed.get("designs", [parsed]))]
        except Exception as exc:
            logger.warning("design_strategy_ai_failed_fallback", error=str(exc))
            return _mock_strategies(prefs, count)

        return {"design_strategies": [s.model_dump() for s in strategies[:count]]}

    return node


def _mock_strategies(prefs: dict, count: int) -> dict:
    roles = prefs.get("requested_furniture_types") or DEFAULT_ROLES
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
