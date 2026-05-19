import structlog
from qdrant_client.http import models

from app.core.config import get_settings
from app.vector.qdrant import get_qdrant_client

logger = structlog.get_logger(__name__)


def ensure_product_collection() -> None:
    """Create or recreate the product collection with named vectors.

    Named vectors:
        - "text": 768-dim from text-embedding-005 (semantic search)
        - "image": 1408-dim from multimodalembedding@001 (visual similarity)
    """
    settings = get_settings()
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection_products

    expected_config = {
        "text": settings.qdrant_text_vector_size,
        "image": settings.qdrant_image_vector_size,
    }

    collections = {c.name for c in client.get_collections().collections}

    if collection_name in collections:
        info = client.get_collection(collection_name)
        vectors_config = info.config.params.vectors

        # Check if it's a named-vector collection with correct sizes
        needs_recreate = False
        if isinstance(vectors_config, models.VectorParams):
            # Old single-vector collection — must recreate
            needs_recreate = True
        else:
            for name, expected_size in expected_config.items():
                existing = vectors_config.get(name)
                if existing is None or existing.size != expected_size:
                    needs_recreate = True
                    break

        if needs_recreate:
            logger.warning(
                "qdrant_collection_mismatch",
                action="recreating_collection",
            )
            client.delete_collection(collection_name)
        else:
            return

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "text": models.VectorParams(
                size=settings.qdrant_text_vector_size,
                distance=models.Distance.COSINE,
            ),
            "image": models.VectorParams(
                size=settings.qdrant_image_vector_size,
                distance=models.Distance.COSINE,
            ),
        },
    )
    logger.info(
        "qdrant_collection_created",
        name=collection_name,
        text_size=settings.qdrant_text_vector_size,
        image_size=settings.qdrant_image_vector_size,
    )
