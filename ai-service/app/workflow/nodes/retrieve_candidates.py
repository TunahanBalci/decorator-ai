from sqlalchemy.orm import Session

from app.schemas.ai_outputs import ProductRetrievalIntent
from app.vector.product_search import search_products
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState


def retrieve_candidates_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "retrieve_candidates")
        prefs = state.get("user_preferences", {})
        room_analysis = state.get("room_analysis", {})
        room_dimensions = state.get("room_dimensions", {})
        candidate_products: dict[str, list[dict]] = {}
        intents = []
        for strategy in state.get("design_strategies", []):
            for role in strategy["furniture_roles"]:
                intent = ProductRetrievalIntent(
                    role=role,
                    category=role,
                    styles=[prefs["design_style"]] if prefs.get("design_style") else [],
                    material=[prefs["material"]] if prefs.get("material") else [],
                    colors=prefs.get("colors") or [],
                    temperature=prefs.get("temperature"),
                    room_types=[room_analysis.get("room_type", "living_room")],
                    query_text=f"{strategy.get('style', '')} {role}".strip(),
                    **_dimension_bounds(role, room_dimensions),
                )
                key = f"{strategy['design_index']}:{role}"
                intents.append(intent.model_dump())
                candidate_products[key] = [
                    c.model_dump(mode="json")
                    for c in search_products(db, intent, room_image_path=state.get("room_image_path"))
                ]
        return {"retrieval_intents": intents, "candidate_products": candidate_products}

    return node



def _dimension_bounds(role: str, room_dimensions: dict) -> dict:
    room_width = room_dimensions.get("current_wall_length_cm")
    room_depth = room_dimensions.get("room_depth_cm")
    room_height = room_dimensions.get("ceiling_height_cm")

    max_width = float(room_width) * 0.82 if room_width else None
    max_depth = float(room_depth) * 0.72 if room_depth else None
    max_height = float(room_height) * 0.95 if room_height else None

    minimums = {
        "sofa": (120, 60, 55),
        "armchair": (55, 50, 55),
        "chair": (40, 40, 45),
        "dining_chair": (40, 40, 45),
        "office_chair": (45, 45, 55),
        "coffee_table": (45, 35, 20),
        "side_table": (28, 25, 25),
        "console_table": (70, 25, 45),
        "tv_unit": (80, 25, 35),
        "dining_table": (80, 60, 55),
        "bed": (90, 180, 40),
        "wardrobe": (70, 35, 120),
        "dresser": (55, 30, 55),
        "nightstand": (28, 25, 30),
        "bookshelf": (40, 20, 80),
        "desk": (70, 45, 55),
        "rug": (80, 80, None),
        "curtain": (50, None, 120),
        "mirror": (30, None, 40),
        "wall_art": (25, None, 25),
        "plant_pot": (15, 15, 15),
        "lamp": (15, 15, 20),
        "floor_lamp": (20, 20, 80),
        "pendant_lamp": (15, 15, 15),
        "storage_unit": (45, 25, 45),
    }
    min_width, min_depth, min_height = minimums.get(role, (None, None, None))
    return {
        "min_width_cm": min_width,
        "min_depth_cm": min_depth,
        "min_height_cm": min_height,
        "max_width_cm": max_width,
        "max_depth_cm": max_depth,
        "max_height_cm": max_height,
    }
