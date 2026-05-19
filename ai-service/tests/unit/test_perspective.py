"""Tests for Sprint 2 perspective-aware rendering utilities."""

from pathlib import Path

from PIL import Image

from app.utils.perspective import (
    anchor_bottom_center,
    apply_perspective_skew,
    compute_furniture_dimensions,
    compute_perspective_scale,
    generate_shadow,
)


# ---------------------------------------------------------------------------
# compute_perspective_scale
# ---------------------------------------------------------------------------


def test_scale_at_top_returns_min_scale() -> None:
    """y=0.0 (top of image, farthest from camera) → min_scale."""
    assert compute_perspective_scale(0.0, min_scale=0.35, max_scale=1.2) == 0.35


def test_scale_at_bottom_returns_max_scale() -> None:
    """y=1.0 (bottom of image, closest to camera) → max_scale."""
    assert compute_perspective_scale(1.0, min_scale=0.35, max_scale=1.2) == 1.2


def test_scale_at_midpoint_returns_interpolated() -> None:
    """y=0.5 should return the midpoint of the scale range."""
    scale = compute_perspective_scale(0.5, min_scale=0.4, max_scale=1.0)
    assert abs(scale - 0.7) < 1e-9


def test_scale_clamped_below_zero() -> None:
    """Negative y values are clamped to 0.0 → min_scale."""
    assert compute_perspective_scale(-0.3, min_scale=0.3, max_scale=1.0) == 0.3


def test_scale_clamped_above_one() -> None:
    """y > 1.0 is clamped to 1.0 → max_scale."""
    assert compute_perspective_scale(1.5, min_scale=0.3, max_scale=1.0) == 1.0


def test_scale_monotonically_increases_with_y() -> None:
    """Scale should increase as y increases (closer objects are larger)."""
    scales = [
        compute_perspective_scale(y, min_scale=0.3, max_scale=1.2)
        for y in [0.0, 0.25, 0.5, 0.75, 1.0]
    ]
    for i in range(len(scales) - 1):
        assert scales[i] < scales[i + 1]


# ---------------------------------------------------------------------------
# compute_furniture_dimensions
# ---------------------------------------------------------------------------


def test_dimensions_at_unit_scale() -> None:
    """scale=1.0 should return the default width."""
    w, h = compute_furniture_dimensions(1.0, default_width=200, aspect_ratio=2.0)
    assert w == 200
    assert h == 100


def test_dimensions_at_half_scale() -> None:
    w, h = compute_furniture_dimensions(0.5, default_width=200, aspect_ratio=1.0)
    assert w == 100
    assert h == 100


def test_dimensions_never_zero() -> None:
    w, h = compute_furniture_dimensions(0.001, default_width=10, aspect_ratio=1.0)
    assert w >= 1
    assert h >= 1


# ---------------------------------------------------------------------------
# anchor_bottom_center
# ---------------------------------------------------------------------------


def test_anchor_centers_horizontally() -> None:
    """Furniture should be centered on the placement x-coordinate."""
    paste_x, paste_y = anchor_bottom_center(
        placement_x_px=500,
        placement_y_px=400,
        furniture_width=100,
        furniture_height=80,
        image_width=1000,
        image_height=800,
    )
    assert paste_x == 450  # 500 - 100/2
    assert paste_y == 320  # 400 - 80


def test_anchor_clamped_to_left_edge() -> None:
    """Furniture near the left edge should not go negative."""
    paste_x, _ = anchor_bottom_center(
        placement_x_px=10,
        placement_y_px=400,
        furniture_width=100,
        furniture_height=50,
        image_width=1000,
        image_height=800,
    )
    assert paste_x == 0


def test_anchor_clamped_to_right_edge() -> None:
    """Furniture near the right edge should not exceed image width."""
    paste_x, _ = anchor_bottom_center(
        placement_x_px=990,
        placement_y_px=400,
        furniture_width=100,
        furniture_height=50,
        image_width=1000,
        image_height=800,
    )
    assert paste_x <= 900  # 1000 - 100


def test_anchor_clamped_to_top_edge() -> None:
    """Furniture placed very high shouldn't go above the canvas."""
    _, paste_y = anchor_bottom_center(
        placement_x_px=500,
        placement_y_px=20,
        furniture_width=100,
        furniture_height=100,
        image_width=1000,
        image_height=800,
    )
    assert paste_y == 0


def test_anchor_clamped_to_bottom_edge() -> None:
    """Furniture placed at the very bottom should stay within bounds."""
    _, paste_y = anchor_bottom_center(
        placement_x_px=500,
        placement_y_px=800,
        furniture_width=100,
        furniture_height=50,
        image_width=1000,
        image_height=800,
    )
    assert paste_y >= 0
    assert paste_y + 50 <= 800


# ---------------------------------------------------------------------------
# generate_shadow
# ---------------------------------------------------------------------------


def test_shadow_returns_rgba_image() -> None:
    """Shadow output should be an RGBA image."""
    furniture = Image.new("RGBA", (100, 80), (200, 100, 50, 200))
    shadow = generate_shadow(furniture, opacity=0.5, blur_radius=10, y_offset=5)
    assert shadow.mode == "RGBA"


def test_shadow_dimensions_include_offset() -> None:
    """Shadow image should be taller than the furniture by y_offset."""
    furniture = Image.new("RGBA", (100, 80), (200, 100, 50, 200))
    shadow = generate_shadow(furniture, opacity=0.5, blur_radius=5, y_offset=12)
    assert shadow.width == 100
    assert shadow.height == 80 + 12


def test_shadow_opacity_scales_alpha() -> None:
    """Shadow with opacity=0 should be fully transparent."""
    furniture = Image.new("RGBA", (50, 50), (0, 0, 0, 255))
    shadow = generate_shadow(furniture, opacity=0.0, blur_radius=0, y_offset=0)
    # All alpha values should be 0.
    alpha = shadow.split()[3]
    assert alpha.getextrema() == (0, 0)


def test_shadow_does_not_crash_with_transparent_furniture() -> None:
    """Shadow generation should handle fully transparent furniture."""
    furniture = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    shadow = generate_shadow(furniture, opacity=0.5, blur_radius=10, y_offset=5)
    assert shadow.size[0] == 100
    assert shadow.size[1] == 85


def test_shadow_with_zero_blur_radius() -> None:
    """Shadow should still work with blur_radius=0."""
    furniture = Image.new("RGBA", (60, 40), (100, 100, 100, 180))
    shadow = generate_shadow(furniture, opacity=0.4, blur_radius=0, y_offset=8)
    assert shadow.mode == "RGBA"
    assert shadow.size == (60, 48)


# ---------------------------------------------------------------------------
# apply_perspective_skew
# ---------------------------------------------------------------------------


def test_skew_center_returns_unchanged() -> None:
    """Furniture at x=0.5 (center) should receive no visible skew."""
    furniture = Image.new("RGBA", (100, 80), (200, 100, 50, 200))
    skewed = apply_perspective_skew(furniture, normalized_x=0.5, max_skew_pixels=12.0)
    assert skewed.size == furniture.size


def test_skew_does_not_crash_at_extremes() -> None:
    """Skew should handle x=0.0 and x=1.0 without errors."""
    furniture = Image.new("RGBA", (100, 80), (200, 100, 50, 200))
    left = apply_perspective_skew(furniture, normalized_x=0.0, max_skew_pixels=15.0)
    right = apply_perspective_skew(furniture, normalized_x=1.0, max_skew_pixels=15.0)
    assert left.mode == "RGBA"
    assert right.mode == "RGBA"


def test_skew_preserves_image_size() -> None:
    """Output should have the same dimensions as input."""
    furniture = Image.new("RGBA", (120, 90), (50, 200, 100, 255))
    skewed = apply_perspective_skew(furniture, normalized_x=0.2, max_skew_pixels=10.0)
    assert skewed.size == furniture.size


# ---------------------------------------------------------------------------
# End-to-end integration: scale → anchor → shadow → paste
# ---------------------------------------------------------------------------


def test_full_rendering_pipeline_produces_valid_image() -> None:
    """Simulate the full Sprint 2 rendering pipeline on a synthetic image."""
    room = Image.new("RGBA", (800, 600), (245, 241, 234, 255))
    furniture = Image.new("RGBA", (100, 80), (180, 120, 60, 230))

    # Compute scale for a furniture placed at y=0.75 (moderately close).
    scale = compute_perspective_scale(0.75, min_scale=0.35, max_scale=1.2)
    assert 0.35 < scale < 1.2

    aspect = 100 / 80
    fw, fh = compute_furniture_dimensions(scale, default_width=200, aspect_ratio=aspect)
    assert fw > 0 and fh > 0

    resized = furniture.resize((fw, fh), Image.Resampling.LANCZOS)

    # Anchor at bottom-center.
    px, py = anchor_bottom_center(400, 450, fw, fh, 800, 600)
    assert 0 <= px <= 800 - fw
    assert 0 <= py <= 600 - fh

    # Shadow.
    shadow = generate_shadow(resized, opacity=0.4, blur_radius=10, y_offset=8)
    sx = max(0, min(px, 800 - shadow.width))
    sy = max(0, min(py, 600 - shadow.height))
    room.alpha_composite(shadow, (sx, sy))
    room.alpha_composite(resized, (px, py))

    # Final image should still be 800×600 RGBA.
    assert room.size == (800, 600)
    assert room.mode == "RGBA"
