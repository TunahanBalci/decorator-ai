"""Layout planner — multi-furniture placement engine.

Orchestrates the placement of multiple furniture items in a room using:
1. Room zone analysis (from :mod:`app.layout.zones`)
2. Anchor-first placement strategy
3. Relationship-based secondary placement (from :mod:`app.layout.constraints`)
4. Collision detection (from :mod:`app.layout.collision`)
5. Layout quality scoring (from :mod:`app.layout.scoring`)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import structlog

from app.layout.collision import (
    check_collision,
    distance_between,
    is_inside_floor_area,
    polygon_center,
)
from app.layout.constraints import (
    ANCHOR_ROLES,
    MIN_SPACING,
    FurnitureRelationship,
    get_relationship,
    get_render_order,
    is_anchor,
)
from app.layout.zones import Zone, divide_into_zones

logger = structlog.get_logger(__name__)

NormalizedPolygon = list[list[float]]


@dataclass
class PlannedPlacement:
    """A single furniture placement decided by the planner."""

    product_id: str
    role: str
    polygon: NormalizedPolygon
    zone_label: str
    placement_reason: str
    render_order: int
    confidence: float = 0.75


@dataclass
class LayoutPlan:
    """Complete layout result from the planner."""

    placements: list[PlannedPlacement] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    variation_name: str = "balanced"
    layout_score: float = 0.0


class LayoutPlanner:
    """Plans multi-furniture layouts using zone analysis and relationship rules.

    Usage::

        planner = LayoutPlanner()
        plan = planner.plan(
            room_analysis={"room_type": "living_room", ...},
            products=[{"product_id": "p1", "role": "sofa", ...}, ...],
            floor_polygon=[[0,0.5],[1,0.5],[1,1],[0,1]],
        )
    """

    def plan(
        self,
        *,
        room_analysis: dict,
        products: list[dict],
        floor_polygon: NormalizedPolygon | None = None,
        num_layouts: int = 1,
    ) -> list[LayoutPlan]:
        """Generate one or more layout variations.

        Args:
            room_analysis: Room analysis dict with ``room_type``, etc.
            products: Selected products with ``product_id``, ``role``, metadata.
            floor_polygon: Normalized floor polygon.  Falls back to default.
            num_layouts: Number of layout variations to generate.

        Returns:
            List of :class:`LayoutPlan` objects, each with placements and score.
        """
        room_type = room_analysis.get("room_type", "living_room")
        if not floor_polygon:
            floor_polygon = [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]]

        zones = divide_into_zones(floor_polygon, room_type)
        existing = self._extract_existing_furniture(room_analysis)

        variations = _VARIATIONS[:num_layouts]
        plans = []
        for var_name, var_offset in variations:
            plan = self._generate_single_layout(
                products=products,
                zones=zones,
                floor_polygon=floor_polygon,
                existing=existing,
                variation_name=var_name,
                offset=var_offset,
            )
            plans.append(plan)

        return plans

    def _generate_single_layout(
        self,
        *,
        products: list[dict],
        zones: list[Zone],
        floor_polygon: NormalizedPolygon,
        existing: list[NormalizedPolygon],
        variation_name: str,
        offset: float,
    ) -> LayoutPlan:
        """Generate a single layout variation."""
        plan = LayoutPlan(variation_name=variation_name)
        placed_polygons: list[NormalizedPolygon] = list(existing)
        placed_map: dict[str, NormalizedPolygon] = {}  # role → polygon

        # Sort: anchors first, then by render order.
        sorted_products = sorted(
            products,
            key=lambda p: (0 if is_anchor(p.get("role", "")) else 1, get_render_order(p.get("role", ""))),
        )

        for product in sorted_products:
            role = product.get("role", "")
            product_id = str(product.get("product_id", ""))

            # Find the best zone for this role.
            target_zone = self._find_zone(role, zones)

            # Try to place within the zone.
            polygon = self._place_in_zone(
                role=role,
                zone=target_zone,
                floor_polygon=floor_polygon,
                placed_polygons=placed_polygons,
                placed_map=placed_map,
                offset=offset,
            )

            if polygon and is_inside_floor_area(polygon, floor_polygon):
                placement = PlannedPlacement(
                    product_id=product_id,
                    role=role,
                    polygon=polygon,
                    zone_label=target_zone.label if target_zone else "fallback",
                    placement_reason=self._placement_reason(role, target_zone, placed_map),
                    render_order=get_render_order(role),
                )
                plan.placements.append(placement)
                placed_polygons.append(polygon)
                placed_map[role] = polygon
            else:
                plan.rejected.append({
                    "product_id": product_id,
                    "role": role,
                    "reason": "no_valid_position_found",
                })

        # Sort placements by render order for output.
        plan.placements.sort(key=lambda p: p.render_order)

        # Score the layout.
        from app.layout.scoring import score_layout
        score_result = score_layout(
            placements=[p.polygon for p in plan.placements],
            floor_polygon=floor_polygon,
            products=[{"role": p.role} for p in plan.placements],
            placed_map=placed_map,
        )
        plan.layout_score = score_result.total

        return plan

    def _find_zone(self, role: str, zones: list[Zone]) -> Zone | None:
        """Find the best zone for a furniture role."""
        # Prefer zones that list this role in preferred_roles.
        for zone in sorted(zones, key=lambda z: z.priority, reverse=True):
            if role in zone.preferred_roles:
                return zone
        # Fallback: any non-walkway zone.
        for zone in zones:
            if zone.label != "walkway":
                return zone
        return zones[0] if zones else None

    def _place_in_zone(
        self,
        *,
        role: str,
        zone: Zone | None,
        floor_polygon: NormalizedPolygon,
        placed_polygons: list[NormalizedPolygon],
        placed_map: dict[str, NormalizedPolygon],
        offset: float,
    ) -> NormalizedPolygon | None:
        """Find a valid position within a zone, respecting constraints."""
        from app.utils.placement import placement_polygon_for_point

        relationship = get_relationship(role)

        # If this role has a "near" relationship, place relative to anchor.
        if relationship and relationship.near:
            polygon = self._place_near_anchor(
                role, relationship, placed_map, floor_polygon, placed_polygons, offset
            )
            if polygon:
                return polygon

        # Otherwise, place within the zone's bbox.
        if zone:
            zx1, zy1, zx2, zy2 = zone.bbox
            # Try multiple candidate positions within the zone.
            candidates = [
                ((zx1 + zx2) / 2 + offset * 0.05, (zy1 + zy2) / 2),
                ((zx1 + zx2) / 2, zy2 - 0.05 + offset * 0.03),
                (zx1 + (zx2 - zx1) * 0.3 + offset * 0.04, (zy1 + zy2) / 2),
                (zx1 + (zx2 - zx1) * 0.7 - offset * 0.02, zy2 - 0.08),
            ]
            for cx, cy in candidates:
                cx = max(0.05, min(0.95, cx))
                cy = max(0.15, min(0.95, cy))
                polygon = placement_polygon_for_point(cx, cy, role)
                if self._is_valid_placement(polygon, floor_polygon, placed_polygons):
                    return polygon

        # Fallback: try several grid positions.
        for cx in [0.3, 0.5, 0.7, 0.25, 0.75]:
            for cy in [0.75, 0.82, 0.88, 0.70]:
                adjusted_cx = max(0.05, min(0.95, cx + offset * 0.03))
                polygon = placement_polygon_for_point(adjusted_cx, cy, role)
                if self._is_valid_placement(polygon, floor_polygon, placed_polygons):
                    return polygon

        return None

    def _place_near_anchor(
        self,
        role: str,
        relationship: FurnitureRelationship,
        placed_map: dict[str, NormalizedPolygon],
        floor_polygon: NormalizedPolygon,
        placed_polygons: list[NormalizedPolygon],
        offset: float,
    ) -> NormalizedPolygon | None:
        """Place furniture near an already-placed anchor piece."""
        from app.layout.collision import bbox_from_polygon
        from app.utils.placement import placement_polygon_for_point, _role_size

        # Get the secondary furniture's own half-width.
        sec_w, sec_h = _role_size(role)
        sec_half_w = sec_w / 2

        for anchor_role in relationship.near:
            anchor_polygon = placed_map.get(anchor_role)
            if not anchor_polygon:
                continue

            anchor_cx, anchor_cy = polygon_center(anchor_polygon)
            ax1, ay1, ax2, ay2 = bbox_from_polygon(anchor_polygon)
            anchor_half_w = (ax2 - ax1) / 2
            anchor_half_h = (ay2 - ay1) / 2
            min_dist, max_dist = relationship.distance_range

            # Total horizontal clearance: anchor edge + secondary half-width + gap.
            h_clear = anchor_half_w + sec_half_w + 0.02
            # Use anchor's BOTTOM edge y for floor-contact alignment.
            anchor_floor_y = ay2

            # Try positions around the anchor, offset from its EDGES.
            offsets = [
                (h_clear + offset * 0.02, anchor_floor_y),                        # right
                (-h_clear - offset * 0.02, anchor_floor_y),                       # left
                (0.0, anchor_floor_y + sec_h + 0.02),                             # below
                (h_clear, anchor_floor_y - anchor_half_h * 0.3),                   # diag right
                (-h_clear, anchor_floor_y - anchor_half_h * 0.3),                  # diag left
            ]
            for dx, floor_y in offsets:
                cx = max(0.05, min(0.95, anchor_cx + dx))
                cy = max(0.15, min(0.95, floor_y))
                polygon = placement_polygon_for_point(cx, cy, role)
                if self._is_valid_placement(polygon, floor_polygon, placed_polygons):
                    dist = distance_between(polygon, anchor_polygon)
                    if dist <= max_dist:
                        return polygon

        return None

    def _is_valid_placement(
        self,
        polygon: NormalizedPolygon,
        floor_polygon: NormalizedPolygon,
        placed_polygons: list[NormalizedPolygon],
    ) -> bool:
        """Check if a placement is valid (no collisions, inside floor)."""
        if not is_inside_floor_area(polygon, floor_polygon):
            return False
        for existing in placed_polygons:
            if check_collision(polygon, existing):
                return False
        return True

    def _placement_reason(
        self,
        role: str,
        zone: Zone | None,
        placed_map: dict[str, NormalizedPolygon],
    ) -> str:
        """Generate a human-readable placement reason."""
        relationship = get_relationship(role)
        if relationship and relationship.near:
            for anchor in relationship.near:
                if anchor in placed_map:
                    return f"Placed near {anchor}"
        if zone:
            return f"Placed in {zone.label}"
        return "Fallback placement"

    def _extract_existing_furniture(
        self, room_analysis: dict
    ) -> list[NormalizedPolygon]:
        """Extract existing furniture polygons from room analysis."""
        existing = []
        for item in room_analysis.get("existing_furniture", []):
            polygon = item.get("polygon")
            if polygon and len(polygon) >= 3:
                existing.append(polygon)
        return existing


# Layout variation definitions: (name, offset_factor).
_VARIATIONS = [
    ("balanced", 0.0),
    ("cozy", 0.5),
    ("minimalist", -0.3),
    ("spacious", -0.6),
    ("eclectic", 0.8),
]
