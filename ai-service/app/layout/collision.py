"""Collision detection and spacing enforcement.

Provides functions to check whether furniture placements overlap, remain
inside the floor area, and maintain minimum spacing.  Used by the layout
planner to reject invalid placements.
"""

from __future__ import annotations

import math

NormalizedPolygon = list[list[float]]


def bbox_from_polygon(polygon: NormalizedPolygon) -> tuple[float, float, float, float]:
    """Extract axis-aligned bounding box from a polygon.

    Returns:
        ``(x1, y1, x2, y2)`` where ``(x1, y1)`` is top-left.
    """
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_overlap(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    """Compute IoU-style overlap ratio between two axis-aligned bounding boxes.

    Returns:
        Overlap ratio in ``[0.0, 1.0]``.  0 means no overlap.
    """
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix1 >= ix2 or iy1 >= iy2:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    area_a = max((ax2 - ax1) * (ay2 - ay1), 1e-9)
    area_b = max((bx2 - bx1) * (by2 - by1), 1e-9)
    smaller_area = min(area_a, area_b)
    return intersection / smaller_area


def check_collision(
    polygon_a: NormalizedPolygon,
    polygon_b: NormalizedPolygon,
    threshold: float = 0.05,
) -> bool:
    """Check if two placement polygons collide (overlap above threshold).

    Args:
        polygon_a: First normalized placement polygon.
        polygon_b: Second normalized placement polygon.
        threshold: Minimum overlap ratio to consider a collision.

    Returns:
        ``True`` if the placements collide.
    """
    if not polygon_a or not polygon_b:
        return False
    return bbox_overlap(bbox_from_polygon(polygon_a), bbox_from_polygon(polygon_b)) > threshold


def check_all_collisions(
    placements: list[NormalizedPolygon],
) -> list[tuple[int, int]]:
    """Find all colliding pairs among a list of placements.

    Returns:
        List of ``(i, j)`` index pairs that collide.
    """
    collisions = []
    for i in range(len(placements)):
        for j in range(i + 1, len(placements)):
            if check_collision(placements[i], placements[j]):
                collisions.append((i, j))
    return collisions


def is_inside_floor_area(
    polygon: NormalizedPolygon,
    floor_polygon: NormalizedPolygon,
) -> bool:
    """Check if a placement polygon is reasonably inside the floor area.

    Uses the bottom-center point (floor contact) of the furniture for
    the check, consistent with how placement validation works.

    Args:
        polygon: Furniture placement polygon (normalized).
        floor_polygon: Floor area polygon (normalized).

    Returns:
        ``True`` if the furniture's floor contact is inside the floor area.
    """
    if not polygon or not floor_polygon:
        return False
    # Bottom-center = average of bottom two points.
    bottom_points = sorted(polygon, key=lambda p: p[1], reverse=True)[:2]
    contact_x = sum(p[0] for p in bottom_points) / len(bottom_points)
    contact_y = sum(p[1] for p in bottom_points) / len(bottom_points)
    return _point_in_polygon(contact_x, contact_y, floor_polygon)


def has_minimum_spacing(
    polygon: NormalizedPolygon,
    others: list[NormalizedPolygon],
    min_gap: float = 0.03,
) -> bool:
    """Check if a placement has minimum spacing from all other placements.

    Args:
        polygon: The placement to check.
        others: Existing placements.
        min_gap: Minimum distance between bbox edges (normalized units).

    Returns:
        ``True`` if spacing is sufficient for all other placements.
    """
    if not polygon:
        return True
    bbox_a = bbox_from_polygon(polygon)
    for other in others:
        if not other:
            continue
        bbox_b = bbox_from_polygon(other)
        dist = _bbox_edge_distance(bbox_a, bbox_b)
        if dist < min_gap and bbox_overlap(bbox_a, bbox_b) == 0:
            # Close but not overlapping — spacing violation.
            return False
    return True


def polygon_center(polygon: NormalizedPolygon) -> tuple[float, float]:
    """Compute the centroid of a polygon."""
    if not polygon:
        return 0.5, 0.75
    cx = sum(p[0] for p in polygon) / len(polygon)
    cy = sum(p[1] for p in polygon) / len(polygon)
    return cx, cy


def distance_between(
    polygon_a: NormalizedPolygon,
    polygon_b: NormalizedPolygon,
) -> float:
    """Euclidean distance between the centroids of two polygons."""
    cx_a, cy_a = polygon_center(polygon_a)
    cx_b, cy_b = polygon_center(polygon_b)
    return math.sqrt((cx_a - cx_b) ** 2 + (cy_a - cy_b) ** 2)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _point_in_polygon(x: float, y: float, polygon: NormalizedPolygon) -> bool:
    """Ray-casting point-in-polygon test."""
    inside = False
    prev = polygon[-1]
    for curr in polygon:
        xi, yi = curr
        xj, yj = prev
        if (yi > y) != (yj > y):
            x_intersect = (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
            if x < x_intersect:
                inside = not inside
        prev = curr
    return inside


def _bbox_edge_distance(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    """Minimum distance between two axis-aligned bounding box edges."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    dx = max(ax1 - bx2, bx1 - ax2, 0.0)
    dy = max(ay1 - by2, by1 - ay2, 0.0)
    return math.sqrt(dx * dx + dy * dy)
