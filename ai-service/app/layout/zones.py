"""Room zone division.

Divides the available floor polygon into functional zones based on room type.
Zones are represented as normalized bounding boxes and are used by the layout
planner to assign furniture to appropriate areas.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Zone:
    """A functional area within a room."""

    label: str
    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2) normalized
    priority: int = 0  # higher = placed first
    preferred_roles: list[str] = field(default_factory=list)


def divide_into_zones(
    floor_polygon: list[list[float]],
    room_type: str,
) -> list[Zone]:
    """Divide the floor area into functional zones by room type.

    Args:
        floor_polygon: Normalized floor polygon ``[[x,y], ...]``.
        room_type: One of ``living_room``, ``bedroom``, ``office``.

    Returns:
        List of :class:`Zone` objects, ordered by placement priority.
    """
    if not floor_polygon:
        floor_polygon = [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]]

    xs = [p[0] for p in floor_polygon]
    ys = [p[1] for p in floor_polygon]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    layout_fn = _ROOM_LAYOUTS.get(room_type, _living_room_zones)
    return layout_fn(x_min, y_min, x_max, y_max)


# ---------------------------------------------------------------------------
# Room-specific zone layouts
# ---------------------------------------------------------------------------


def _living_room_zones(x1: float, y1: float, x2: float, y2: float) -> list[Zone]:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    return [
        Zone("seating_zone", (x1 + 0.03, mid_y, mid_x + 0.10, y2 - 0.05),
             priority=3, preferred_roles=["sofa", "armchair"]),
        Zone("table_zone", (mid_x - 0.10, mid_y + 0.08, mid_x + 0.10, y2 - 0.10),
             priority=2, preferred_roles=["coffee_table", "side_table"]),
        Zone("accent_zone", (x2 - 0.20, y1 + 0.02, x2 - 0.02, y2 - 0.05),
             priority=1, preferred_roles=["floor_lamp", "plant_pot", "bookshelf"]),
        Zone("media_zone", (mid_x - 0.15, y1 + 0.02, mid_x + 0.15, y1 + 0.20),
             priority=2, preferred_roles=["tv_unit", "console_table"]),
        Zone("rug_zone", (x1 + 0.10, mid_y + 0.02, x2 - 0.10, y2 - 0.05),
             priority=0, preferred_roles=["rug"]),
        Zone("walkway", (x1, y2 - 0.08, x2, y2),
             priority=-1, preferred_roles=[]),
    ]


def _bedroom_zones(x1: float, y1: float, x2: float, y2: float) -> list[Zone]:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    return [
        Zone("bed_zone", (x1 + 0.10, y1 + 0.05, x2 - 0.10, mid_y + 0.15),
             priority=3, preferred_roles=["bed"]),
        Zone("nightstand_zone_left", (x1 + 0.02, mid_y - 0.10, x1 + 0.18, mid_y + 0.10),
             priority=2, preferred_roles=["nightstand"]),
        Zone("nightstand_zone_right", (x2 - 0.18, mid_y - 0.10, x2 - 0.02, mid_y + 0.10),
             priority=2, preferred_roles=["nightstand"]),
        Zone("dresser_zone", (x1 + 0.05, y2 - 0.25, x2 - 0.05, y2 - 0.05),
             priority=1, preferred_roles=["dresser", "wardrobe", "storage_unit"]),
        Zone("rug_zone", (x1 + 0.15, mid_y, x2 - 0.15, y2 - 0.10),
             priority=0, preferred_roles=["rug"]),
        Zone("walkway", (x1, y2 - 0.08, x2, y2),
             priority=-1, preferred_roles=[]),
    ]


def _office_zones(x1: float, y1: float, x2: float, y2: float) -> list[Zone]:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    return [
        Zone("desk_zone", (x1 + 0.05, y1 + 0.05, mid_x + 0.15, mid_y + 0.05),
             priority=3, preferred_roles=["desk"]),
        Zone("chair_zone", (x1 + 0.10, mid_y, mid_x + 0.10, mid_y + 0.25),
             priority=2, preferred_roles=["office_chair", "chair"]),
        Zone("storage_zone", (x2 - 0.25, y1 + 0.05, x2 - 0.02, y2 - 0.10),
             priority=1, preferred_roles=["bookshelf", "storage_unit", "wardrobe"]),
        Zone("accent_zone", (x1 + 0.02, mid_y + 0.10, x1 + 0.18, y2 - 0.05),
             priority=0, preferred_roles=["floor_lamp", "plant_pot"]),
        Zone("walkway", (x1, y2 - 0.08, x2, y2),
             priority=-1, preferred_roles=[]),
    ]


_ROOM_LAYOUTS = {
    "living_room": _living_room_zones,
    "bedroom": _bedroom_zones,
    "office": _office_zones,
}
