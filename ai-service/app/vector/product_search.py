import structlog
from pathlib import Path
from qdrant_client.http import models
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.product import Product
from app.db.repositories.product_repository import ProductRepository
from app.schemas.ai_outputs import ProductRetrievalIntent
from app.schemas.product import ProductCandidate
from app.utils.scoring import score_product
from app.vector.qdrant import get_qdrant_client

logger = structlog.get_logger(__name__)


def product_to_candidate(product: Product, intent: ProductRetrievalIntent, semantic_score: float = 0.0) -> ProductCandidate:
    primary = next((img for img in product.images if img.is_primary), product.images[0] if product.images else None)
    score = score_product(product, intent, semantic_score)
    return ProductCandidate(
        product_id=product.id,
        external_id=product.external_id,
        name=product.name,
        category=product.category,
        source_url=product.source_url,
        image_path=primary.relative_path if primary else None,
        semantic_score=semantic_score,
        score=score,
        metadata={
            "styles": product.styles or [],
            "colors": product.colors or [],
            "material": product.material or [],
            "temperature": product.temperature,
            "room_types": product.room_types or [],
            "width_cm": float(product.width_cm) if product.width_cm is not None else None,
            "depth_cm": float(product.depth_cm) if product.depth_cm is not None else None,
            "height_cm": float(product.height_cm) if product.height_cm is not None else None,
            "visual_weight": product.visual_weight,
            "spatial_feel": product.spatial_feel,
            "quality_tier": product.quality_tier,
        },
    )


def build_filter_payload(intent: ProductRetrievalIntent) -> dict:
    payload = {"must": [{"key": "category", "match": {"value": intent.category}}, {"key": "is_active", "match": {"value": True}}]}
    if not intent.is_group_allowed:
        payload["must"].append({"key": "is_group", "match": {"value": False}})
    for field in ("styles", "material", "colors", "room_types"):
        values = getattr(intent, field)
        if values:
            payload["must"].append({"key": field, "match": {"any": values}})
    if intent.temperature:
        payload["must"].append({"key": "temperature", "match": {"value": intent.temperature}})
    dimension_filters = (
        ("width_cm", intent.min_width_cm, intent.max_width_cm),
        ("depth_cm", intent.min_depth_cm, intent.max_depth_cm),
        ("height_cm", intent.min_height_cm, intent.max_height_cm),
    )
    for field, minimum, maximum in dimension_filters:
        range_filter = {}
        if minimum is not None:
            range_filter["gte"] = minimum
        if maximum is not None:
            range_filter["lte"] = maximum
        if range_filter:
            payload["must"].append({"key": field, "range": range_filter})
    return payload


def search_products(
    db: Session,
    intent: ProductRetrievalIntent,
    limit: int | None = None,
    room_image_path: str | None = None,
) -> list[ProductCandidate]:
    """Search products using hybrid text + image similarity.

    When `room_image_path` is provided, the search also embeds the room image
    and combines text + visual similarity scores for better results.
    """
    settings = get_settings()
    effective_limit = limit or settings.max_candidates_per_item
    use_vertex = bool(settings.vertex_project_id) and not settings.mock_ai

    if use_vertex:
        try:
            return _hybrid_search(db, intent, effective_limit, room_image_path)
        except Exception as exc:
            logger.warning("hybrid_search_failed_fallback_to_sql", error=str(exc))

    # Fallback: SQL-based search
    products = ProductRepository(db).fallback_search(intent, effective_limit)
    return sorted(
        [product_to_candidate(product, intent, 0.0) for product in products],
        key=lambda candidate: candidate.score,
        reverse=True,
    )


def _hybrid_search(
    db: Session,
    intent: ProductRetrievalIntent,
    limit: int,
    room_image_path: str | None = None,
) -> list[ProductCandidate]:
    """Hybrid search combining text vectors and image vectors.

    Strategy:
    1. Always search the "text" vector (text-embedding-005, 768-dim)
    2. If a room image is available, also search the "image" vector
       (multimodalembedding@001, 1408-dim) for visual similarity
    3. Merge results: text_score * 0.6 + image_score * 0.4
    """
    from uuid import UUID
    from app.ai.vertex_client import VertexAIClient

    settings = get_settings()
    client = VertexAIClient(settings)
    qdrant = get_qdrant_client()
    filter_payload = build_filter_payload(intent)

    # --- Text search ---
    query_text_vectors = client.embed_texts([intent.query_text])
    if not query_text_vectors:
        raise RuntimeError("Failed to embed query text")
    text_query_vector = query_text_vectors[0]

    text_results = qdrant.query_points(
        collection_name=settings.qdrant_collection_products,
        query=text_query_vector,
        using="text",
        query_filter=models.Filter(**filter_payload),
        limit=limit,
    ).points

    if not text_results:
        # Retry without filters
        text_results = qdrant.query_points(
            collection_name=settings.qdrant_collection_products,
            query=text_query_vector,
            using="text",
            limit=limit,
        ).points

    # Build text scores map
    text_scores: dict[str, float] = {}
    for hit in text_results:
        if hit.payload:
            text_scores[hit.payload["product_db_id"]] = hit.score

    # --- Image search (if room image is available) ---
    image_scores: dict[str, float] = {}
    if room_image_path:
        try:
            image_scores = _image_search(
                client, qdrant, settings, room_image_path, filter_payload, limit
            )
        except Exception as exc:
            logger.warning("image_search_failed_text_only", error=str(exc))

    # --- Merge scores ---
    all_product_ids = set(text_scores.keys()) | set(image_scores.keys())
    merged_scores: dict[str, float] = {}
    for pid in all_product_ids:
        t_score = text_scores.get(pid, 0.0)
        i_score = image_scores.get(pid, 0.0)
        if image_scores:
            # Hybrid: 60% text, 40% image
            merged_scores[pid] = t_score * 0.6 + i_score * 0.4
        else:
            merged_scores[pid] = t_score

    # Load Product objects and build candidates
    product_ids = [UUID(pid) for pid in merged_scores]
    products_map = {p.id: p for p in ProductRepository(db).get_many(product_ids)}

    candidates = []
    for pid_str, semantic_score in merged_scores.items():
        product = products_map.get(UUID(pid_str))
        if product:
            candidates.append(product_to_candidate(product, intent, semantic_score))

    return sorted(candidates, key=lambda c: c.score, reverse=True)


def _image_search(
    client,
    qdrant,
    settings,
    room_image_path: str,
    filter_payload: dict,
    limit: int,
) -> dict[str, float]:
    """Embed the room image and search the image vector space."""
    from app.storage.local_storage import LocalImageStorage

    storage = LocalImageStorage(settings)
    resolved = storage.resolve_room_image(room_image_path)
    if not resolved.exists():
        return {}

    image_bytes = resolved.read_bytes()
    image_vector = client.embed_multimodal(
        image_bytes=image_bytes,
        dimension=settings.qdrant_image_vector_size,
    )

    results = qdrant.query_points(
        collection_name=settings.qdrant_collection_products,
        query=image_vector,
        using="image",
        query_filter=models.Filter(**filter_payload),
        limit=limit,
    ).points

    if not results:
        results = qdrant.query_points(
            collection_name=settings.qdrant_collection_products,
            query=image_vector,
            using="image",
            limit=limit,
        ).points

    scores: dict[str, float] = {}
    for hit in results:
        if hit.payload:
            scores[hit.payload["product_db_id"]] = hit.score
    return scores
