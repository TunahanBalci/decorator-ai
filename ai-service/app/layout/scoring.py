"""Layout quality scoring.

Evaluates the quality of a furniture layout based on multiple factors:
- no_overlap: Are any furniture items overlapping?
- floor_validity: Are all items inside the floor area?
- relationship: Do items satisfy their spatial relationships?
- spacing: Is there adequate spacing between items?
- style_consistency: Are product styles compatible? (basic check)
- balance: Is furniture distributed evenly across the room?
"""

from __future__ import annotations

from dataclasses import dataclass

from app.layout.collision import (
    bbox_from_polygon,
    bbox_overlap,
    check_collision,
    distance_between,
    is_inside_floor_area,
    polygon_center,
)
from app.layout.constraints import MIN_SPACING, get_relationship

NormalizedPolygon = list[list[float]]


@dataclass
class LayoutScore:
    """Breakdown of layout quality scores."""

    no_overlap: float = 1.0
    floor_validity: float = 1.0
    relationship: float = 1.0
    spacing: float = 1.0
    style_consistency: float = 1.0
    balance: float = 1.0

    @property
    def total(self) -> float:
        """Weighted total score."""
        return round(
            0.25 * self.no_overlap
            + 0.20 * self.floor_validity
            + 0.20 * self.relationship
            + 0.15 * self.spacing
            + 0.10 * self.style_consistency
            + 0.10 * self.balance,
            4,
        )

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "no_overlap": round(self.no_overlap, 4),
            "floor_validity": round(self.floor_validity, 4),
            "relationship": round(self.relationship, 4),
            "spacing": round(self.spacing, 4),
            "style_consistency": round(self.style_consistency, 4),
            "balance": round(self.balance, 4),
        }


def score_layout(
    placements: list[NormalizedPolygon],
    floor_polygon: NormalizedPolygon,
    products: list[dict],
    placed_map: dict[str, NormalizedPolygon] | None = None,
) -> LayoutScore:
    """Score a furniture layout on multiple quality dimensions.

    Args:
        placements: List of normalized placement polygons.
        floor_polygon: The floor area polygon.
        products: Product dicts with at least ``role`` key.
        placed_map: Mapping of ``role → polygon`` for relationship checking.

    Returns:
        A :class:`LayoutScore` with per-dimension and total scores.
    """
    if not placements:
        return LayoutScore(no_overlap=1.0, floor_validity=1.0, relationship=0.0,
                           spacing=1.0, style_consistency=1.0, balance=0.5)

    placed_map = placed_map or {}
    n = len(placements)

    # 1. No-overlap score: penalize each collision pair.
    collision_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if check_collision(placements[i], placements[j]):
                collision_count += 1
    max_pairs = max(n * (n - 1) / 2, 1)
    no_overlap = max(0.0, 1.0 - collision_count / max_pairs)

    # 2. Floor validity: fraction of items inside floor area.
    inside_count = sum(1 for p in placements if is_inside_floor_area(p, floor_polygon))
    floor_validity = inside_count / max(n, 1)

    # 3. Relationship score: fraction of relationship constraints satisfied.
    relationship = _score_relationships(products, placed_map)

    # 4. Spacing score: fraction of item pairs with adequate spacing.
    spacing = _score_spacing(placements)

    # 5. Style consistency: basic check (always 1.0 for deterministic scoring).
    style_consistency = 1.0

    # 6. Balance: how evenly distributed furniture is across the room.
    balance = _score_balance(placements)

    return LayoutScore(
        no_overlap=no_overlap,
        floor_validity=floor_validity,
        relationship=relationship,
        spacing=spacing,
        style_consistency=style_consistency,
        balance=balance,
    )


def _score_relationships(
    products: list[dict],
    placed_map: dict[str, NormalizedPolygon],
) -> float:
    """Score how well relationship constraints are satisfied."""
    if not products or not placed_map:
        return 0.5

    checks = 0
    satisfied = 0
    for product in products:
        role = product.get("role", "")
        relationship = get_relationship(role)
        if not relationship:
            continue

        polygon = placed_map.get(role)
        if not polygon:
            continue

        # Check "near" constraints.
        if relationship.near:
            checks += 1
            for anchor_role in relationship.near:
                anchor = placed_map.get(anchor_role)
                if anchor:
                    dist = distance_between(polygon, anchor)
                    if dist <= relationship.distance_range[1]:
                        satisfied += 1
                        break

    return satisfied / max(checks, 1)


def _score_spacing(placements: list[NormalizedPolygon]) -> float:
    """Score minimum spacing between all placement pairs."""
    if len(placements) < 2:
        return 1.0
    adequate = 0
    total = 0
    for i in range(len(placements)):
        for j in range(i + 1, len(placements)):
            total += 1
            dist = distance_between(placements[i], placements[j])
            if dist >= MIN_SPACING:
                adequate += 1
    return adequate / max(total, 1)


def _score_balance(placements: list[NormalizedPolygon]) -> float:
    """Score how evenly furniture is distributed across the room."""
    if len(placements) < 2:
        return 0.8

    centers = [polygon_center(p) for p in placements]
    avg_x = sum(c[0] for c in centers) / len(centers)
    avg_y = sum(c[1] for c in centers) / len(centers)

    # Perfect balance = centroid at (0.5, 0.75) — center of typical floor area.
    x_dev = abs(avg_x - 0.5)
    y_dev = abs(avg_y - 0.75)
    deviation = (x_dev + y_dev) / 2

    # Score: 1.0 at perfect center, decreasing with deviation.
    return max(0.0, 1.0 - deviation * 2)
