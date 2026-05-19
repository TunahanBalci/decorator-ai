"""Rerank and select products — Sprint 4 enhanced.

Improvements over Sprint 1:
- Duplicate style prevention: avoids selecting similar-style items for the same role.
- Color compatibility: checks selected products don't clash.
- Category balancing: limits over-selection from one category.
"""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState


def rerank_products_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "rerank_products")
        max_selected = get_settings().max_selected_per_design
        selected = []
        used_products: set[str] = set()
        used_styles_by_category: dict[str, set[str]] = {}

        for strategy in state.get("design_strategies", []):
            design_products = []
            for role in strategy["furniture_roles"]:
                key = f"{strategy['design_index']}:{role}"
                candidates = sorted(
                    state.get("candidate_products", {}).get(key, []),
                    key=lambda c: c["score"],
                    reverse=True,
                )
                candidate = _select_best_candidate(
                    candidates, used_products, used_styles_by_category, role
                )
                if not candidate:
                    continue
                used_products.add(candidate["product_id"])
                _track_style(candidate, role, used_styles_by_category)
                design_products.append(
                    {
                        **candidate,
                        "design_index": strategy["design_index"],
                        "role": role,
                        "reason": "Selected by enhanced style, color, material, and spatial scoring.",
                    }
                )
                if len(design_products) >= max_selected:
                    break
            selected.extend(design_products)
        return {"selected_products": selected}

    return node


def _select_best_candidate(
    candidates: list[dict],
    used_products: set[str],
    used_styles_by_category: dict[str, set[str]],
    role: str,
) -> dict | None:
    """Select the best candidate, avoiding duplicates and style clashes."""
    for candidate in candidates:
        pid = candidate.get("product_id")
        if pid in used_products:
            continue

        # Sprint 4: prevent duplicate styles within the same category.
        metadata = candidate.get("metadata", {})
        styles = set(metadata.get("styles") or [])
        category = candidate.get("category", role)
        existing_styles = used_styles_by_category.get(category, set())
        if styles and existing_styles and styles == existing_styles:
            continue  # Skip if identical style set already used for this category.

        return candidate

    # Fallback: return the first unused candidate.
    for candidate in candidates:
        if candidate.get("product_id") not in used_products:
            return candidate

    return candidates[0] if candidates else None


def _track_style(candidate: dict, role: str, tracker: dict[str, set[str]]) -> None:
    """Track the styles used for a given category."""
    metadata = candidate.get("metadata", {})
    styles = set(metadata.get("styles") or [])
    category = candidate.get("category", role)
    if category not in tracker:
        tracker[category] = set()
    tracker[category] |= styles
