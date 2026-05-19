"""Tests for Sprint 4 layout planning engine.

Covers:
- Zone division (living room, bedroom, office)
- Collision detection
- Relationship-based placement
- Layout planner (anchor-first, secondary near anchor)
- Layout scoring
- Multiple layout generation
- Fallback behavior
"""

from app.layout.collision import (
    bbox_from_polygon,
    bbox_overlap,
    check_all_collisions,
    check_collision,
    distance_between,
    has_minimum_spacing,
    is_inside_floor_area,
)
from app.layout.constraints import (
    ANCHOR_ROLES,
    get_relationship,
    get_render_order,
    is_anchor,
)
from app.layout.planner import LayoutPlanner
from app.layout.scoring import LayoutScore, score_layout
from app.layout.zones import divide_into_zones


FLOOR = [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]]


# ---------------------------------------------------------------------------
# Zone division
# ---------------------------------------------------------------------------


def test_living_room_zones() -> None:
    zones = divide_into_zones(FLOOR, "living_room")
    labels = [z.label for z in zones]
    assert "seating_zone" in labels
    assert "table_zone" in labels
    assert "walkway" in labels


def test_bedroom_zones() -> None:
    zones = divide_into_zones(FLOOR, "bedroom")
    labels = [z.label for z in zones]
    assert "bed_zone" in labels
    assert any("nightstand" in l for l in labels)


def test_office_zones() -> None:
    zones = divide_into_zones(FLOOR, "office")
    labels = [z.label for z in zones]
    assert "desk_zone" in labels
    assert "chair_zone" in labels


def test_unknown_room_type_uses_living_room() -> None:
    zones = divide_into_zones(FLOOR, "unknown_type")
    labels = [z.label for z in zones]
    assert "seating_zone" in labels


# ---------------------------------------------------------------------------
# Collision detection
# ---------------------------------------------------------------------------


def test_collision_overlapping_polygons() -> None:
    a = [[0.3, 0.5], [0.6, 0.5], [0.6, 0.8], [0.3, 0.8]]
    b = [[0.4, 0.6], [0.7, 0.6], [0.7, 0.9], [0.4, 0.9]]
    assert check_collision(a, b) is True


def test_collision_non_overlapping_polygons() -> None:
    a = [[0.1, 0.5], [0.3, 0.5], [0.3, 0.7], [0.1, 0.7]]
    b = [[0.6, 0.5], [0.8, 0.5], [0.8, 0.7], [0.6, 0.7]]
    assert check_collision(a, b) is False


def test_check_all_collisions_finds_pairs() -> None:
    a = [[0.1, 0.5], [0.4, 0.5], [0.4, 0.8], [0.1, 0.8]]
    b = [[0.3, 0.6], [0.6, 0.6], [0.6, 0.9], [0.3, 0.9]]  # overlaps with a
    c = [[0.7, 0.5], [0.9, 0.5], [0.9, 0.7], [0.7, 0.7]]  # no overlap
    collisions = check_all_collisions([a, b, c])
    assert (0, 1) in collisions
    assert len(collisions) == 1


def test_is_inside_floor_area() -> None:
    polygon = [[0.3, 0.6], [0.5, 0.6], [0.5, 0.8], [0.3, 0.8]]
    assert is_inside_floor_area(polygon, FLOOR) is True


def test_is_outside_floor_area() -> None:
    polygon = [[0.3, 0.1], [0.5, 0.1], [0.5, 0.3], [0.3, 0.3]]
    assert is_inside_floor_area(polygon, FLOOR) is False


def test_has_minimum_spacing_ok() -> None:
    a = [[0.1, 0.6], [0.2, 0.6], [0.2, 0.7], [0.1, 0.7]]
    b = [[0.5, 0.6], [0.6, 0.6], [0.6, 0.7], [0.5, 0.7]]
    assert has_minimum_spacing(a, [b], min_gap=0.03) is True


def test_bbox_overlap_disjoint() -> None:
    assert bbox_overlap((0, 0, 0.3, 0.3), (0.5, 0.5, 1.0, 1.0)) == 0.0


def test_distance_between_polygons() -> None:
    a = [[0.1, 0.6], [0.2, 0.6], [0.2, 0.7], [0.1, 0.7]]
    b = [[0.8, 0.6], [0.9, 0.6], [0.9, 0.7], [0.8, 0.7]]
    dist = distance_between(a, b)
    assert dist > 0.5


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


def test_sofa_is_anchor() -> None:
    assert is_anchor("sofa") is True
    assert is_anchor("coffee_table") is False


def test_coffee_table_relationship() -> None:
    rel = get_relationship("coffee_table")
    assert rel is not None
    assert "sofa" in rel.near


def test_nightstand_relationship() -> None:
    rel = get_relationship("nightstand")
    assert rel is not None
    assert "bed" in rel.near


def test_desk_prefers_wall() -> None:
    rel = get_relationship("desk")
    assert rel is not None
    assert rel.prefer_wall is True


def test_render_order() -> None:
    assert get_render_order("rug") < get_render_order("sofa")
    assert get_render_order("sofa") < get_render_order("floor_lamp")


# ---------------------------------------------------------------------------
# Layout planner — living room
# ---------------------------------------------------------------------------


def test_living_room_layout() -> None:
    products = [
        {"product_id": "s1", "role": "sofa"},
        {"product_id": "ct1", "role": "coffee_table"},
        {"product_id": "fl1", "role": "floor_lamp"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=products,
        floor_polygon=FLOOR,
    )

    assert len(plans) == 1
    plan = plans[0]
    assert len(plan.placements) == 3
    assert plan.layout_score >= 0.50

    roles = {p.role for p in plan.placements}
    assert "sofa" in roles
    assert "coffee_table" in roles

    # No collisions among placements.
    polygons = [p.polygon for p in plan.placements]
    assert check_all_collisions(polygons) == []


def test_living_room_coffee_table_near_sofa() -> None:
    products = [
        {"product_id": "s1", "role": "sofa"},
        {"product_id": "ct1", "role": "coffee_table"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=products,
        floor_polygon=FLOOR,
    )
    plan = plans[0]
    placed = {p.role: p.polygon for p in plan.placements}
    if "sofa" in placed and "coffee_table" in placed:
        dist = distance_between(placed["sofa"], placed["coffee_table"])
        assert dist < 0.3, f"coffee_table should be near sofa, got distance={dist}"


# ---------------------------------------------------------------------------
# Layout planner — bedroom
# ---------------------------------------------------------------------------


def test_bedroom_layout() -> None:
    products = [
        {"product_id": "b1", "role": "bed"},
        {"product_id": "ns1", "role": "nightstand"},
        {"product_id": "r1", "role": "rug"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "bedroom"},
        products=products,
        floor_polygon=FLOOR,
    )
    plan = plans[0]
    assert len(plan.placements) >= 2
    assert plan.layout_score >= 0.50

    polygons = [p.polygon for p in plan.placements]
    assert check_all_collisions(polygons) == []


def test_bedroom_nightstand_near_bed() -> None:
    products = [
        {"product_id": "b1", "role": "bed"},
        {"product_id": "ns1", "role": "nightstand"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "bedroom"},
        products=products,
        floor_polygon=FLOOR,
    )
    plan = plans[0]
    placed = {p.role: p.polygon for p in plan.placements}
    if "bed" in placed and "nightstand" in placed:
        dist = distance_between(placed["bed"], placed["nightstand"])
        assert dist < 0.3, f"nightstand should be near bed, got distance={dist}"


# ---------------------------------------------------------------------------
# Layout planner — office
# ---------------------------------------------------------------------------


def test_office_layout() -> None:
    products = [
        {"product_id": "d1", "role": "desk"},
        {"product_id": "c1", "role": "office_chair"},
        {"product_id": "bs1", "role": "bookshelf"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "office"},
        products=products,
        floor_polygon=FLOOR,
    )
    plan = plans[0]
    assert len(plan.placements) >= 2
    assert plan.layout_score >= 0.50

    polygons = [p.polygon for p in plan.placements]
    assert check_all_collisions(polygons) == []


def test_office_chair_near_desk() -> None:
    products = [
        {"product_id": "d1", "role": "desk"},
        {"product_id": "c1", "role": "office_chair"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "office"},
        products=products,
        floor_polygon=FLOOR,
    )
    plan = plans[0]
    placed = {p.role: p.polygon for p in plan.placements}
    if "desk" in placed and "office_chair" in placed:
        dist = distance_between(placed["desk"], placed["office_chair"])
        assert dist < 0.3, f"chair should be near desk, got distance={dist}"


# ---------------------------------------------------------------------------
# Layout scoring
# ---------------------------------------------------------------------------


def test_layout_score_no_collisions() -> None:
    placements = [
        [[0.1, 0.6], [0.3, 0.6], [0.3, 0.8], [0.1, 0.8]],
        [[0.6, 0.6], [0.8, 0.6], [0.8, 0.8], [0.6, 0.8]],
    ]
    result = score_layout(placements, FLOOR, [{"role": "sofa"}, {"role": "lamp"}])
    assert result.no_overlap == 1.0
    assert result.floor_validity == 1.0
    assert result.total >= 0.50


def test_layout_score_penalizes_overlap() -> None:
    placements = [
        [[0.3, 0.6], [0.6, 0.6], [0.6, 0.9], [0.3, 0.9]],
        [[0.4, 0.7], [0.7, 0.7], [0.7, 1.0], [0.4, 1.0]],
    ]
    result = score_layout(placements, FLOOR, [{"role": "sofa"}, {"role": "table"}])
    assert result.no_overlap < 1.0


def test_layout_score_penalizes_outside_floor() -> None:
    placements = [
        [[0.3, 0.1], [0.5, 0.1], [0.5, 0.3], [0.3, 0.3]],
    ]
    result = score_layout(placements, FLOOR, [{"role": "desk"}])
    assert result.floor_validity < 1.0


def test_layout_score_dict_output() -> None:
    result = LayoutScore(no_overlap=0.9, floor_validity=1.0, relationship=0.8)
    d = result.to_dict()
    assert "total" in d
    assert "no_overlap" in d
    assert d["no_overlap"] == 0.9


# ---------------------------------------------------------------------------
# Multiple layout variations
# ---------------------------------------------------------------------------


def test_multiple_layouts_generated() -> None:
    products = [
        {"product_id": "s1", "role": "sofa"},
        {"product_id": "ct1", "role": "coffee_table"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=products,
        floor_polygon=FLOOR,
        num_layouts=3,
    )
    assert len(plans) == 3
    names = {p.variation_name for p in plans}
    assert len(names) == 3  # Each variation should have a unique name.


def test_each_variation_has_score() -> None:
    products = [
        {"product_id": "s1", "role": "sofa"},
        {"product_id": "fl1", "role": "floor_lamp"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=products,
        floor_polygon=FLOOR,
        num_layouts=2,
    )
    for plan in plans:
        assert plan.layout_score > 0
        assert plan.variation_name != ""


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_products_returns_empty_plan() -> None:
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=[],
        floor_polygon=FLOOR,
    )
    assert len(plans) == 1
    assert len(plans[0].placements) == 0


def test_planner_handles_unknown_role() -> None:
    products = [{"product_id": "x1", "role": "exotic_item"}]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=products,
        floor_polygon=FLOOR,
    )
    # Should either place or reject — no crash.
    assert len(plans) == 1


def test_render_order_in_placements() -> None:
    products = [
        {"product_id": "fl1", "role": "floor_lamp"},
        {"product_id": "s1", "role": "sofa"},
        {"product_id": "r1", "role": "rug"},
    ]
    planner = LayoutPlanner()
    plans = planner.plan(
        room_analysis={"room_type": "living_room"},
        products=products,
        floor_polygon=FLOOR,
    )
    plan = plans[0]
    orders = [p.render_order for p in plan.placements]
    assert orders == sorted(orders), "Placements should be ordered by render_order"
