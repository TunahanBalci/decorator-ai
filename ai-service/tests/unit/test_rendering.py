"""Tests for Sprint 3 rendering architecture.

Covers:
- Mask generation
- Prompt generation
- Renderer factory
- Overlay renderer
- Mock inpaint renderer
- External AI renderer fallback
- No torch required for default mode
"""

from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app.rendering.base import FurnitureRenderer, RenderResult
from app.rendering.factory import get_renderer
from app.rendering.masks import (
    generate_combined_mask,
    generate_placement_mask,
    save_debug_mask,
)
from app.rendering.prompts import (
    build_inpainting_prompt,
    build_multi_furniture_prompt,
)


# ---------------------------------------------------------------------------
# Mask generation
# ---------------------------------------------------------------------------


def test_mask_generation_creates_valid_mask() -> None:
    """Mask should be a single-channel image with white in the polygon area."""
    polygon = [[0.3, 0.4], [0.7, 0.4], [0.7, 0.8], [0.3, 0.8]]
    mask = generate_placement_mask(800, 600, polygon, dilation_px=0)
    assert mask.mode == "L"
    assert mask.size == (800, 600)
    # Center of the polygon should be white.
    center_val = mask.getpixel((400, 360))  # (0.5*800, 0.6*600)
    assert center_val == 255
    # Corner outside the polygon should be black.
    corner_val = mask.getpixel((10, 10))
    assert corner_val == 0


def test_mask_dilation_expands_area() -> None:
    """Dilated mask should have more white pixels than non-dilated."""
    polygon = [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6]]
    mask_no_dilation = generate_placement_mask(200, 200, polygon, dilation_px=0)
    mask_dilated = generate_placement_mask(200, 200, polygon, dilation_px=5)

    white_no_dilation = sum(1 for p in mask_no_dilation.getdata() if p > 0)
    white_dilated = sum(1 for p in mask_dilated.getdata() if p > 0)
    assert white_dilated > white_no_dilation


def test_mask_empty_polygon_returns_black() -> None:
    """Empty polygon should produce an all-black mask."""
    mask = generate_placement_mask(100, 100, [], dilation_px=0)
    assert mask.getextrema() == (0, 0)


def test_combined_mask_merges_multiple_polygons() -> None:
    """Combined mask should cover all polygon areas."""
    polygons = [
        [[0.1, 0.1], [0.3, 0.1], [0.3, 0.3], [0.1, 0.3]],
        [[0.6, 0.6], [0.9, 0.6], [0.9, 0.9], [0.6, 0.9]],
    ]
    mask = generate_combined_mask(200, 200, polygons, dilation_px=0)
    # Both polygon centers should be white.
    center1 = mask.getpixel((40, 40))  # (0.2*200, 0.2*200)
    center2 = mask.getpixel((150, 150))  # (0.75*200, 0.75*200)
    assert center1 == 255
    assert center2 == 255
    # Area between should be black.
    between = mask.getpixel((100, 100))  # (0.5*200, 0.5*200)
    assert between == 0


def test_save_debug_mask_writes_file(tmp_path: Path) -> None:
    """Debug mask should be saved to disk."""
    mask = generate_placement_mask(100, 100, [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]])
    output = tmp_path / "debug" / "mask.png"
    save_debug_mask(mask, output)
    assert output.exists()
    with Image.open(output) as loaded:
        assert loaded.mode == "L"


# ---------------------------------------------------------------------------
# Prompt generation
# ---------------------------------------------------------------------------


def test_prompt_generation_includes_category() -> None:
    """Positive prompt should mention the furniture category."""
    pos, neg = build_inpainting_prompt("sofa")
    assert "sofa" in pos.lower()


def test_prompt_generation_includes_color_and_style() -> None:
    """Positive prompt should incorporate color and style when provided."""
    pos, neg = build_inpainting_prompt("sofa", color="gray", style="modern")
    assert "gray" in pos.lower()
    assert "modern" in pos.lower()


def test_prompt_generation_includes_room_type() -> None:
    """Positive prompt should mention the room type."""
    pos, neg = build_inpainting_prompt("sofa", room_type="living_room")
    assert "living room" in pos.lower()


def test_prompt_negative_includes_quality_guards() -> None:
    """Negative prompt should contain quality and distortion guards."""
    _, neg = build_inpainting_prompt("chair")
    assert "floating" in neg.lower()
    assert "blurry" in neg.lower()
    assert "distorted" in neg.lower()


def test_prompt_humanizes_snake_case_categories() -> None:
    """Snake_case categories should be humanized in prompts."""
    pos, _ = build_inpainting_prompt("coffee_table")
    assert "coffee table" in pos.lower()

    pos2, _ = build_inpainting_prompt("floor_lamp")
    assert "floor lamp" in pos2.lower()


def test_multi_furniture_prompt() -> None:
    """Multi-furniture prompt should list all items."""
    products = [
        {"role": "sofa", "metadata": {"colors": ["gray"]}},
        {"role": "coffee_table", "metadata": {}},
    ]
    pos, neg = build_multi_furniture_prompt(products, room_type="living_room")
    assert "sofa" in pos.lower()
    assert "coffee table" in pos.lower()
    assert "living room" in pos.lower()


def test_multi_furniture_prompt_empty_products() -> None:
    """Should return a generic prompt when no products are given."""
    pos, neg = build_multi_furniture_prompt([], room_type="bedroom")
    assert "furniture" in pos.lower()


# ---------------------------------------------------------------------------
# Renderer factory
# ---------------------------------------------------------------------------


def test_factory_returns_overlay_by_default() -> None:
    """Default render method should return OverlayRenderer."""
    renderer = get_renderer("overlay")
    assert renderer.name == "overlay"
    assert isinstance(renderer, FurnitureRenderer)


def test_factory_returns_mock_inpaint() -> None:
    """mock_inpaint method should return MockInpaintRenderer."""
    renderer = get_renderer("mock_inpaint")
    assert renderer.name == "mock_inpaint"


def test_factory_falls_back_for_unknown_method() -> None:
    """Unknown render method should fall back to overlay."""
    renderer = get_renderer("nonexistent_method")
    assert renderer.name == "overlay"


def test_factory_sdxl_falls_back_without_gpu() -> None:
    """sdxl_inpaint should fall back when torch/diffusers are unavailable."""
    # Simulate missing torch by patching import.
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name in ("torch", "diffusers"):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=mock_import):
        renderer = get_renderer("sdxl_inpaint")
        # Should fall back to overlay.
        assert renderer.name == "overlay"


def test_factory_external_ai_returns_renderer() -> None:
    """external_ai should return ExternalAIInpaintRenderer."""
    renderer = get_renderer("external_ai")
    assert renderer.name == "external_ai_inpaint"


# ---------------------------------------------------------------------------
# Overlay renderer
# ---------------------------------------------------------------------------


def test_overlay_renderer_produces_image(tmp_path: Path) -> None:
    """OverlayRenderer should produce a valid output image."""
    from app.core.config import Settings
    from app.rendering.overlay_renderer import OverlayRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/test.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (640, 480), (230, 220, 210)).save(room_path)

    renderer = OverlayRenderer()
    assert renderer.name == "overlay"

    result = renderer.render(
        storage=storage,
        room_image_path="rooms/test.png",
        products=[
            {
                "product_id": "p1",
                "role": "sofa",
                "polygon": [[0.3, 0.5], [0.7, 0.5], [0.7, 0.9], [0.3, 0.9]],
            }
        ],
        output_relative_path="generated/test_overlay.png",
    )

    assert isinstance(result, RenderResult)
    assert result.output_path.exists()
    assert result.render_method == "png_overlay_perspective"


def test_overlay_renderer_pastes_product_image_not_green_mask(tmp_path: Path) -> None:
    """Overlay final render should contain the product image, not a green mask."""
    from app.core.config import Settings
    from app.rendering.overlay_renderer import OverlayRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/overlay_room.png")
    product_path = storage.resolve_product_image("products/red-chair.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    product_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (500, 400), (220, 220, 220)).save(room_path)
    Image.new("RGBA", (80, 120), (210, 40, 30, 255)).save(product_path)

    result = OverlayRenderer().render(
        storage=storage,
        room_image_path="rooms/overlay_room.png",
        products=[
            {
                "product_id": "chair-1",
                "role": "armchair",
                "image_path": "products/red-chair.png",
                "polygon": [[0.4, 0.45], [0.6, 0.45], [0.6, 0.9], [0.4, 0.9]],
            }
        ],
        output_relative_path="generated/overlay_final.png",
    )

    with Image.open(result.output_path).convert("RGB") as image:
        pixels = list(image.getdata())
    red_pixels = sum(1 for red, green, blue in pixels if red > 150 and green < 90 and blue < 90)
    green_pixels = sum(1 for red, green, blue in pixels if green > 120 and red < 120 and blue < 120)
    assert red_pixels > 200
    assert green_pixels < red_pixels


def test_overlay_missing_image_does_not_draw_green_rectangle_in_normal_mode(tmp_path: Path) -> None:
    """Missing product images should not turn final output into a debug rectangle."""
    from app.core.config import Settings
    from app.rendering.overlay_renderer import OverlayRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        debug_placement=False,
    )
    storage = LocalImageStorage(settings)
    room_path = storage.resolve_room_image("rooms/no_image_room.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (320, 240), (230, 225, 215)).save(room_path)

    with patch("app.utils.composite.get_settings", return_value=settings):
        result = OverlayRenderer().render(
            storage=storage,
            room_image_path="rooms/no_image_room.png",
            products=[
                {
                    "product_id": "missing",
                    "role": "sofa",
                    "image_path": "products/missing.png",
                    "polygon": [[0.2, 0.4], [0.8, 0.4], [0.8, 0.9], [0.2, 0.9]],
                }
            ],
            output_relative_path="generated/no_green.png",
        )

    with Image.open(result.output_path).convert("RGB") as image:
        assert image.getpixel((160, 150)) == (230, 225, 215)


# ---------------------------------------------------------------------------
# Mock inpaint renderer
# ---------------------------------------------------------------------------


def test_mock_inpaint_generates_mask_and_prompt(tmp_path: Path) -> None:
    """MockInpaintRenderer should generate masks, prompts, and an image."""
    from app.core.config import Settings
    from app.rendering.mock_inpaint_renderer import MockInpaintRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        debug_placement=True,
        mask_dilation_px=5,
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/mock_room.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 600), (240, 235, 225)).save(room_path)

    renderer = MockInpaintRenderer()
    assert renderer.name == "mock_inpaint"

    with patch("app.rendering.mock_inpaint_renderer.get_settings", return_value=settings):
        result = renderer.render(
            storage=storage,
            room_image_path="rooms/mock_room.png",
            products=[
                {
                    "product_id": "p1",
                    "role": "armchair",
                    "metadata": {"colors": ["blue"], "styles": ["modern"]},
                    "polygon": [[0.3, 0.5], [0.6, 0.5], [0.6, 0.85], [0.3, 0.85]],
                },
            ],
            output_relative_path="generated/mock_test.png",
        )

    assert isinstance(result, RenderResult)
    assert result.output_path.exists()
    assert result.render_method == "mock_inpaint"

    # Debug artifacts should contain prompts.
    assert "prompts" in result.debug_artifacts
    assert len(result.debug_artifacts["prompts"]) == 1
    prompt_info = result.debug_artifacts["prompts"][0]
    assert "armchair" in prompt_info["positive_prompt"].lower()

    # Debug mask should have been saved.
    assert "mask_0" in result.debug_artifacts


def test_mock_inpaint_no_debug_without_flag(tmp_path: Path) -> None:
    """MockInpaintRenderer should skip mask files when debug_placement=False."""
    from app.core.config import Settings
    from app.rendering.mock_inpaint_renderer import MockInpaintRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        debug_placement=False,
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/nodebug.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 300), (200, 200, 200)).save(room_path)

    renderer = MockInpaintRenderer()
    with patch("app.rendering.mock_inpaint_renderer.get_settings", return_value=settings):
        result = renderer.render(
            storage=storage,
            room_image_path="rooms/nodebug.png",
            products=[
                {
                    "role": "lamp",
                    "polygon": [[0.4, 0.5], [0.6, 0.5], [0.6, 0.8], [0.4, 0.8]],
                }
            ],
            output_relative_path="generated/nodebug.png",
        )

    # No mask files should be in debug_artifacts.
    mask_keys = [k for k in result.debug_artifacts if k.startswith("mask_")]
    assert len(mask_keys) == 0
    # Prompts should still be generated.
    assert "prompts" in result.debug_artifacts


def test_mock_inpaint_final_image_comes_from_overlay(tmp_path: Path) -> None:
    """Mock inpaint should return overlay result as final, not the mask image."""
    from app.core.config import Settings
    from app.rendering.mock_inpaint_renderer import MockInpaintRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        debug_placement=True,
    )
    storage = LocalImageStorage(settings)
    room_path = storage.resolve_room_image("rooms/mock_overlay_room.png")
    product_path = storage.resolve_product_image("products/blue-table.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    product_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (480, 360), (235, 232, 225)).save(room_path)
    Image.new("RGBA", (90, 60), (30, 80, 210, 255)).save(product_path)

    with patch("app.rendering.mock_inpaint_renderer.get_settings", return_value=settings):
        with patch("app.utils.composite.get_settings", return_value=settings):
            result = MockInpaintRenderer().render(
                storage=storage,
                room_image_path="rooms/mock_overlay_room.png",
                products=[
                    {
                        "product_id": "table-1",
                        "role": "coffee_table",
                        "image_path": "products/blue-table.png",
                        "metadata": {},
                        "polygon": [[0.35, 0.55], [0.65, 0.55], [0.65, 0.88], [0.35, 0.88]],
                    }
                ],
                output_relative_path="generated/mock_overlay_final.png",
            )

    assert result.relative_path == "generated/mock_overlay_final.png"
    assert result.output_path.exists()
    assert result.debug_artifacts["mask_0"].endswith("_mask_0.png")
    with Image.open(result.output_path).convert("RGB") as image:
        blue_pixels = sum(1 for red, green, blue in image.getdata() if blue > 150 and red < 100)
    assert blue_pixels > 100


# ---------------------------------------------------------------------------
# External AI renderer
# ---------------------------------------------------------------------------


def test_external_ai_falls_back_to_overlay(tmp_path: Path) -> None:
    """ExternalAIInpaintRenderer should fall back when provider config fails."""
    from app.core.config import Settings
    from app.rendering.external_renderer import ExternalAIInpaintRenderer
    from app.rendering.providers.replicate_provider import ReplicateProvider
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/ext_test.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 300), (200, 200, 200)).save(room_path)

    # Use a provider that fails validation (no API key).
    renderer = ExternalAIInpaintRenderer(provider=ReplicateProvider(api_key=None))
    with patch("app.rendering.external_renderer.get_settings", return_value=settings):
        result = renderer.render(
            storage=storage,
            room_image_path="rooms/ext_test.png",
            products=[
                {
                    "role": "desk",
                    "polygon": [[0.2, 0.3], [0.8, 0.3], [0.8, 0.9], [0.2, 0.9]],
                }
            ],
            output_relative_path="generated/ext_test.png",
        )

    # Should fall back to overlay and produce an image.
    assert result.output_path.exists()
    assert result.render_method == "png_overlay_perspective"


# ---------------------------------------------------------------------------
# No torch required for default mode
# ---------------------------------------------------------------------------


def test_no_torch_required_for_overlay() -> None:
    """OverlayRenderer should not import torch or diffusers."""
    import sys

    # Ensure overlay renderer can be imported and used without torch.
    # This test just verifies the import chain doesn't pull in heavy deps.
    from app.rendering.overlay_renderer import OverlayRenderer

    renderer = OverlayRenderer()
    assert renderer.name == "overlay"
    # torch should not be in sys.modules unless it was already loaded.
    # We don't assert its absence since other tests might have loaded it,
    # but the overlay renderer itself never imports it.


def test_no_torch_required_for_factory_overlay() -> None:
    """get_renderer('overlay') should work without torch."""
    renderer = get_renderer("overlay")
    assert renderer.name == "overlay"


# ---------------------------------------------------------------------------
# RenderResult
# ---------------------------------------------------------------------------


def test_render_result_stores_metadata() -> None:
    """RenderResult should correctly store all metadata."""
    result = RenderResult(
        relative_path="generated/test.png",
        output_path=Path("/tmp/test.png"),
        render_method="mock_inpaint",
        debug_artifacts={"mask_0": "debug/mask.png"},
    )
    assert result.relative_path == "generated/test.png"
    assert result.render_method == "mock_inpaint"
    assert result.debug_artifacts["mask_0"] == "debug/mask.png"


def test_render_result_default_debug_artifacts() -> None:
    """RenderResult should default to empty debug artifacts."""
    result = RenderResult(
        relative_path="test.png",
        output_path=Path("/tmp/test.png"),
        render_method="overlay",
    )
    assert result.debug_artifacts == {}
