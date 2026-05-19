import pytest
from pydantic import ValidationError

from app.schemas.design_job import DesignOut, ProductCard
from app.schemas.room import RoomDimensions, UserPreferences
from app.utils.store_names import normalize_store_name_from_url


def test_room_dimensions_requires_cm() -> None:
    assert RoomDimensions(unit="cm").unit == "cm"
    with pytest.raises(ValidationError):
        RoomDimensions(unit="m")


def test_preferences_defaults() -> None:
    prefs = UserPreferences()
    assert prefs.mode == "auto_design"
    assert prefs.colors == []
    assert prefs.ignore_existing_furniture is None



def test_product_card_includes_frontend_mapping_fields() -> None:
    card = ProductCard(
        product_id="00000000-0000-0000-0000-000000000001",
        external_id="sku-1",
        name="Oak Coffee Table",
        category="coffee_table",
        brand="IKEA",
        store_name="IKEA",
        role="coffee_table",
        source_url="https://www.ikea.com.tr/urun/oak-table",
        score=0.91,
    )

    assert card.brand == "IKEA"
    assert card.store_name == "IKEA"
    assert card.role == "coffee_table"
    assert card.source_url == "https://www.ikea.com.tr/urun/oak-table"
    assert card.score == 0.91


def test_design_out_exposes_final_render_fields() -> None:
    design = DesignOut(
        design_id="00000000-0000-0000-0000-000000000002",
        title="Overlay Render",
        style="modern",
        summary="Rendered from catalog furniture.",
        original_image_url="rooms/input.png",
        final_rendered_image_url="generated/job/design_1_composite.png",
        render_method="png_overlay_perspective",
        selected_product_id="00000000-0000-0000-0000-000000000001",
        selected_product_image_url="products/chair.png",
        placement_coordinate={"x": 0.5, "y": 0.82},
    )

    assert design.final_rendered_image_url == "generated/job/design_1_composite.png"
    assert design.debug_mask_url is None


def test_normalize_store_name_from_source_url() -> None:
    assert normalize_store_name_from_url("https://www.ikea.com.tr/urun/x") == "IKEA"
    assert normalize_store_name_from_url("https://www.vivense.com/urun/x") == "Vivense"
    assert (
        normalize_store_name_from_url("https://www.istikbal.com.tr/urun/x")
        == "İstikbal"
    )
    assert normalize_store_name_from_url("https://example.com/urun/x") == "Mağaza"
    assert normalize_store_name_from_url(None) == "Mağaza"
