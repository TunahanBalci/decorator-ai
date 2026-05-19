"""Furniture relationship constraints.

Defines spatial relationships between furniture types (e.g. coffee_table near
sofa, nightstand near bed).  The layout planner uses these rules to place
secondary furniture relative to anchor pieces.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Anchor furniture — placed first, defines the room's layout backbone.
ANCHOR_ROLES = {"sofa", "bed", "desk", "dining_table"}

# Render order — large/ground items first, decorative items last.
RENDER_ORDER = {
    "rug": 0,
    "bed": 1, "sofa": 1, "desk": 1, "dining_table": 1,
    "coffee_table": 2, "nightstand": 2, "side_table": 2,
    "console_table": 2, "tv_unit": 2, "dresser": 2, "wardrobe": 2,
    "armchair": 2, "office_chair": 2, "chair": 2, "dining_chair": 2,
    "bookshelf": 3, "storage_unit": 3,
    "floor_lamp": 4, "lamp": 4, "pendant_lamp": 4,
    "plant_pot": 5, "mirror": 5, "wall_art": 5, "curtain": 5,
}


@dataclass
class FurnitureRelationship:
    """Describes how a furniture piece should relate to other furniture."""

    near: list[str] = field(default_factory=list)
    under: list[str] = field(default_factory=list)
    facing: list[str] = field(default_factory=list)
    prefer_wall: bool = False
    distance_range: tuple[float, float] = (0.03, 0.15)  # normalized units


# Relationship rules: role → how it should relate to other furniture.
FURNITURE_RELATIONSHIPS: dict[str, FurnitureRelationship] = {
    "coffee_table": FurnitureRelationship(
        near=["sofa", "armchair"],
        distance_range=(0.04, 0.12),
    ),
    "side_table": FurnitureRelationship(
        near=["sofa", "armchair", "bed"],
        distance_range=(0.02, 0.10),
    ),
    "nightstand": FurnitureRelationship(
        near=["bed"],
        distance_range=(0.02, 0.20),
    ),
    "floor_lamp": FurnitureRelationship(
        near=["sofa", "armchair", "desk"],
        distance_range=(0.03, 0.14),
    ),
    "lamp": FurnitureRelationship(
        near=["nightstand", "desk", "side_table"],
        distance_range=(0.01, 0.06),
    ),
    "rug": FurnitureRelationship(
        under=["sofa", "coffee_table", "bed", "dining_table"],
    ),
    "tv_unit": FurnitureRelationship(
        facing=["sofa"],
        prefer_wall=True,
    ),
    "console_table": FurnitureRelationship(
        prefer_wall=True,
    ),
    "desk": FurnitureRelationship(
        prefer_wall=True,
    ),
    "bookshelf": FurnitureRelationship(
        prefer_wall=True,
    ),
    "wardrobe": FurnitureRelationship(
        prefer_wall=True,
    ),
    "storage_unit": FurnitureRelationship(
        prefer_wall=True,
    ),
    "office_chair": FurnitureRelationship(
        near=["desk"],
        distance_range=(0.02, 0.08),
    ),
    "chair": FurnitureRelationship(
        near=["desk", "dining_table"],
        distance_range=(0.02, 0.10),
    ),
    "dining_chair": FurnitureRelationship(
        near=["dining_table"],
        distance_range=(0.02, 0.08),
    ),
    "mirror": FurnitureRelationship(
        prefer_wall=True,
    ),
    "wall_art": FurnitureRelationship(
        prefer_wall=True,
    ),
}


# Minimum spacing between any two furniture pieces (normalized units).
MIN_SPACING = 0.03

# Minimum walkway clearance (normalized units, ~8% of image width).
MIN_WALKWAY_CLEARANCE = 0.08


def get_render_order(role: str) -> int:
    """Return the render priority for a furniture role (lower = rendered first)."""
    return RENDER_ORDER.get(role, 3)


def is_anchor(role: str) -> bool:
    """Check if a role is an anchor (placed first)."""
    return role in ANCHOR_ROLES


def get_relationship(role: str) -> FurnitureRelationship | None:
    """Get the relationship constraints for a given role."""
    return FURNITURE_RELATIONSHIPS.get(role)
