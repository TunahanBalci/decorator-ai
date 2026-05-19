from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import PlacementValidationError
from app.db.repositories.product_repository import ProductRepository
from app.storage.local_storage import LocalImageStorage
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState


def validate_result_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "validate_result")
        selected_products = state.get("selected_products", [])
        if not selected_products:
            raise PlacementValidationError("No catalog products were selected for the design")

        generated_design_indices = {
            int(image.get("design_index"))
            for image in state.get("generated_images", [])
            if image.get("design_index") is not None and image.get("path")
        }
        selected_design_indices = {
            int(product.get("design_index"))
            for product in selected_products
            if product.get("design_index") is not None
        }
        if not selected_design_indices:
            raise PlacementValidationError("Selected products are missing design indices")
        if not generated_design_indices.intersection(selected_design_indices):
            raise PlacementValidationError("No rendered design image was produced")

        product_repo = ProductRepository(db)
        storage = LocalImageStorage()
        for product in selected_products:
            has_required_placement = (
                product.get("product_id") and product.get("role") and product.get("polygon")
            )
            if not has_required_placement:
                raise PlacementValidationError(
                    "Selected product is missing required placement fields"
                )
            if not product.get("name") or not product.get("category"):
                raise PlacementValidationError("Selected product is missing catalog metadata")
            catalog_product = product_repo.get(UUID(str(product["product_id"])))
            if catalog_product is None:
                raise PlacementValidationError("Selected product does not exist in catalog")
            if product.get("category") and product["category"] != catalog_product.category:
                raise PlacementValidationError("Selected product category does not match catalog")
            image_path = product.get("image_path")
            if not image_path:
                raise PlacementValidationError("Selected product is missing a product image")
            if not _product_image_available(storage, image_path):
                raise PlacementValidationError("Selected product image is not available")
        return {}

    return node


def _product_image_available(storage: LocalImageStorage, image_path: str) -> bool:
    if image_path.startswith(("http://", "https://")):
        return True
    for path in (
        storage.resolve_product_image(image_path),
        (storage.settings.local_image_root / image_path).resolve(),
        (storage.settings.product_embedding_image_root / image_path).resolve(),
    ):
        if path.exists():
            return True
    return False
