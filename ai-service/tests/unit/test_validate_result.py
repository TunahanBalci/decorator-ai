from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import PlacementValidationError
from app.workflow.nodes.validate_result import validate_result_node


def test_validate_result_rejects_no_selected_products() -> None:
    node = validate_result_node(MagicMock())

    with pytest.raises(PlacementValidationError, match="No catalog products"):
        node({"job_id": str(uuid4()), "selected_products": [], "generated_images": []})


def test_validate_result_rejects_missing_rendered_image() -> None:
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
                with pytest.raises(PlacementValidationError, match="No rendered design image"):
                    node(
                        {
                            "job_id": str(uuid4()),
                            "generated_images": [],
                            "selected_products": [
                                _selected_product(product_id, design_index=1)
                            ],
                        }
                    )


def test_validate_result_accepts_non_empty_rendered_design() -> None:
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
                        "selected_products": [_selected_product(product_id, design_index=1)],
                    }
                )


def _selected_product(product_id, design_index: int) -> dict:
    return {
        "design_index": design_index,
        "product_id": str(product_id),
        "name": "Dataset Sofa",
        "role": "sofa",
        "category": "sofa",
        "image_path": "products/sofa.png",
        "polygon": [[0.2, 0.5], [0.6, 0.5], [0.6, 0.8], [0.2, 0.8]],
    }
