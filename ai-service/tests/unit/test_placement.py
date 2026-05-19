from pathlib import Path

from PIL import Image

from app.core.config import Settings
from app.storage.local_storage import LocalImageStorage
from app.utils.composite import render_placeholder_composite
from app.utils.placement import (
    build_floor_placements,
    draw_placement_debug_image,
    normalized_to_pixel_polygon,
    pixel_to_normalized_polygon,
    point_inside_floor,
    polygon_center,
    validate_placement_polygon,
)


def test_coordinate_conversion_round_trips_sample_room_image(tmp_path: Path) -> None:
    _write_image(tmp_path / "sample-room-1.png", size=(1000, 500))
    polygon = [[250, 300], [750, 300], [750, 450], [250, 450]]

    normalized = pixel_to_normalized_polygon(polygon, 1000, 500)
    assert normalized == [[0.25, 0.6], [0.75, 0.6], [0.75, 0.9], [0.25, 0.9]]
    assert normalized_to_pixel_polygon(normalized, 1000, 500) == polygon


def test_build_floor_placements_rejects_invalid_points_and_accepts_floor_points(
    tmp_path: Path,
) -> None:
    _write_image(tmp_path / "sample-room-2.png", size=(1200, 800))
    products = [
        {"product_id": "p1", "role": "coffee_table"},
        {"product_id": "p2", "role": "floor_lamp"},
    ]
    room_analysis = {
        "available_placement_zones": [
            {
                "label": "central_floor",
                "polygon": [[0.0, 0.55], [1.0, 0.55], [1.0, 1.0], [0.0, 1.0]],
            }
        ],
        "existing_furniture": [
            {"label": "sofa", "polygon": [[0.24, 0.62], [0.42, 0.62], [0.42, 0.80], [0.24, 0.80]]}
        ],
    }

    placements, debug = build_floor_placements(products, 1200, 800, room_analysis)

    assert len(placements) == 2
    assert debug["rejected"]
    assert debug["rejected"][0]["reasons"] == ["overlaps_existing_furniture"]
    for placement in placements:
        center = polygon_center(placement["target_polygon"])
        assert point_inside_floor(center, debug["floor_polygon"])


def test_invalid_placement_points_are_rejected() -> None:
    floor = [[0.0, 0.50], [1.0, 0.50], [1.0, 1.0], [0.0, 1.0]]

    valid, reasons = validate_placement_polygon(
        [[0.20, 0.10], [0.40, 0.10], [0.40, 0.30], [0.20, 0.30]],
        floor,
    )

    assert not valid
    assert "center_not_on_floor" in reasons


def test_debug_image_and_placeholder_composite_are_written_for_sample_room(tmp_path: Path) -> None:
    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
    )
    storage = LocalImageStorage(settings)
    room_path = storage.resolve_room_image("rooms/sample-room-3.png")
    product_path = storage.resolve_product_image("products/chair.png")
    _write_image(room_path, size=(640, 480), color=(245, 241, 234))
    _write_image(product_path, size=(80, 80), color=(90, 130, 110))

    products = [
        {
            "product_id": "p1",
            "role": "armchair",
            "image_path": "products/chair.png",
            "polygon": [[0.35, 0.55], [0.55, 0.55], [0.55, 0.85], [0.35, 0.85]],
        }
    ]
    debug = {
        "image_width": 640,
        "image_height": 480,
        "floor_polygon": [[0, 0.5], [1, 0.5], [1, 1], [0, 1]],
        "accepted": [{"target_polygon": products[0]["polygon"]}],
        "rejected": [],
    }
    debug_path = storage.resolve_generated_image("generated/debug/sample-placement.png")
    draw_placement_debug_image(room_path, debug_path, debug)
    relative_path, composite_path = render_placeholder_composite(
        storage=storage,
        room_image_path="rooms/sample-room-3.png",
        products=products,
        output_relative_path="generated/sample-composite.png",
    )

    assert debug_path.exists()
    assert relative_path == "generated/sample-composite.png"
    assert composite_path.exists()
    with Image.open(composite_path) as composite:
        assert composite.size == (640, 480)
        # Sprint 2: furniture is perspective-scaled and bottom-center anchored.
        # The composite should differ from the blank room somewhere in the
        # placement region (normalized polygon spans 0.35–0.55 x, 0.55–0.85 y).
        # Check a pixel near the bottom-center anchor area.
        center_x = int(0.45 * 640)  # ~288
        floor_y = int(0.85 * 480)   # ~408  — bottom of polygon
        # The furniture or its shadow should have altered at least one nearby pixel.
        region_changed = False
        for dy in range(-40, 10):
            px = composite.getpixel((center_x, max(0, min(floor_y + dy, 479))))
            if px != (245, 241, 234):
                region_changed = True
                break
        assert region_changed, "Composite should differ from blank room in the placement region"


def test_composite_output_with_transparent_furniture(tmp_path: Path) -> None:
    """Verify composite file is created with a transparent-background furniture PNG."""
    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
    )
    storage = LocalImageStorage(settings)
    room_path = storage.resolve_room_image("rooms/test-room.png")
    product_path = storage.resolve_product_image("products/lamp.png")

    # Room: solid color.
    _write_image(room_path, size=(800, 600), color=(230, 225, 215))
    # Furniture: RGBA with partial transparency (simulates a real product cutout).
    product_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (60, 120), (200, 180, 160, 200)).save(product_path)

    products = [
        {
            "product_id": "p2",
            "role": "floor_lamp",
            "image_path": "products/lamp.png",
            "polygon": [[0.40, 0.50], [0.52, 0.50], [0.52, 0.90], [0.40, 0.90]],
        }
    ]
    relative_path, composite_path = render_placeholder_composite(
        storage=storage,
        room_image_path="rooms/test-room.png",
        products=products,
        output_relative_path="generated/test-composite.png",
    )
    assert composite_path.exists()
    with Image.open(composite_path) as img:
        assert img.size == (800, 600)


def _write_image(
    path: Path,
    size: tuple[int, int],
    color: tuple[int, int, int] = (200, 200, 200),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)

