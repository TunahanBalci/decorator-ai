from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import PlacementValidationError
from app.workflow.nodes.create_design_strategies import _mock_strategies
from app.workflow.nodes.retrieve_candidates import retrieve_candidates_node
from app.workflow.nodes.validate_result import validate_result_node


def test_existing_chair_does_not_force_chair_recommendation() -> None:
    result = _mock_strategies(
        {"design_style": "scandinavian"},
        1,
        {
            "room_type": "living_room",
            "existing_objects": [{"label": "armchair"}],
            "existing_furniture": [{"label": "armchair"}],
        },
    )

    roles = result["design_strategies"][0]["furniture_roles"]
    assert roles == ["sofa", "coffee_table", "rug", "floor_lamp"]
    assert "armchair" not in roles


def test_visible_bed_does_not_force_bed_for_living_room_goal() -> None:
    result = _mock_strategies(
        {"design_style": "modern"},
        1,
        {
            "architectural_context": {"room_type": "living_room"},
            "existing_objects": [{"label": "bed"}],
        },
    )

    assert "bed" not in result["design_strategies"][0]["furniture_roles"]


def test_retrieve_candidates_ignores_room_image_when_existing_furniture_ignored() -> None:
    captured = {}

    def fake_search_products(db, intent, room_image_path=None):
        captured["room_image_path"] = room_image_path
        captured["room_types"] = intent.room_types
        return []

    settings = SimpleNamespace(ignore_existing_furniture=True, max_candidates_per_item=10)
    state = {
        "room_image_path": "rooms/with-visible-chair.png",
        "room_dimensions": {},
        "user_preferences": {},
        "room_analysis": {
            "room_type": "bedroom",
            "architectural_context": {"room_type": "living_room"},
            "existing_objects": [{"label": "bed"}],
        },
        "design_strategies": [
            {"design_index": 1, "style": "modern", "furniture_roles": ["sofa"]}
        ],
        "job_id": str(uuid4()),
    }

    with patch("app.workflow.nodes.retrieve_candidates.get_settings", return_value=settings):
        with patch(
            "app.workflow.nodes.retrieve_candidates.search_products",
            side_effect=fake_search_products,
        ):
            retrieve_candidates_node(MagicMock())(state)

    assert captured["room_image_path"] is None
    assert captured["room_types"] == ["living_room"]


def test_validate_result_rejects_invented_product() -> None:
    product_id = uuid4()
    node = validate_result_node(MagicMock())

    with patch("app.workflow.nodes.validate_result.LocalImageStorage"):
        with patch("app.workflow.nodes.validate_result.ProductRepository") as repo_cls:
            repo_cls.return_value.get.return_value = None
            with pytest.raises(PlacementValidationError, match="does not exist"):
                node(
                    {
                        "job_id": str(uuid4()),
                        "generated_images": [
                            {"design_index": 1, "path": "generated/job/design.png"}
                        ],
                        "selected_products": [
                            {
                                "design_index": 1,
                                "product_id": str(product_id),
                                "name": "Invented Sofa",
                                "role": "sofa",
                                "category": "sofa",
                                "image_path": "products/sofa.png",
                                "polygon": [[0.2, 0.5], [0.6, 0.5], [0.6, 0.8], [0.2, 0.8]],
                            }
                        ],
                    }
                )


def test_validate_result_accepts_dataset_product_with_image() -> None:
    product_id = uuid4()
    catalog_product = SimpleNamespace(category="sofa")
    node = validate_result_node(MagicMock())

    with patch("app.workflow.nodes.validate_result.LocalImageStorage"):
        with patch("app.workflow.nodes.validate_result.ProductRepository") as repo_cls:
            with patch(
                "app.workflow.nodes.validate_result._product_image_available",
                return_value=True,
            ):
                repo_cls.return_value.get.return_value = catalog_product
                node(
                    {
                        "job_id": str(uuid4()),
                        "generated_images": [
                            {"design_index": 1, "path": "generated/job/design.png"}
                        ],
                        "selected_products": [
                            {
                                "design_index": 1,
                                "product_id": str(product_id),
                                "name": "Dataset Sofa",
                                "role": "sofa",
                                "category": "sofa",
                                "image_path": "products/sofa.png",
                                "polygon": [[0.2, 0.5], [0.6, 0.5], [0.6, 0.8], [0.2, 0.8]],
                            }
                        ],
                    }
                )
