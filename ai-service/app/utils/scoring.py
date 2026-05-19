"""Enhanced product scoring for style-aware furniture selection.

Sprint 4 upgrade: the scoring function now considers style similarity,
color compatibility, material compatibility, spatial fit, room type match,
and product quality — all deterministic and testable.
"""

from __future__ import annotations

from app.db.models.product import Product
from app.schemas.ai_outputs import ProductRetrievalIntent


def score_product(
    product: Product,
    intent: ProductRetrievalIntent,
    semantic_score: float = 0.0,
) -> float:
    """Score a product's fit for a given retrieval intent.

    Sprint 4 scoring formula::

        score = (
            0.30 * style_similarity +
            0.20 * color_compatibility +
            0.15 * material_compatibility +
            0.15 * spatial_fit +
            0.10 * room_type_match +
            0.10 * product_quality
        )

    Args:
        product: Product database model.
        intent: Retrieval intent with desired attributes.
        semantic_score: Semantic similarity from vector search (0.0-1.0).

    Returns:
        Score in [0.0, 1.0].
    """
    style_sim = _style_similarity(product, intent, semantic_score)
    color_compat = _color_compatibility(product, intent)
    material_compat = _material_compatibility(product, intent)
    spatial = _spatial_fit(product, intent)
    room_match = _room_type_match(product, intent)
    quality = _product_quality(product)

    score = (
        0.30 * style_sim
        + 0.20 * color_compat
        + 0.15 * material_compat
        + 0.15 * spatial
        + 0.10 * room_match
        + 0.10 * quality
    )
    return round(min(max(score, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# Component scoring functions
# ---------------------------------------------------------------------------


def _style_similarity(
    product: Product,
    intent: ProductRetrievalIntent,
    semantic_score: float,
) -> float:
    """Style similarity: semantic score + style tag overlap."""
    base = semantic_score * 0.6
    product_styles = set(product.styles or [])
    intent_styles = set(intent.styles)
    if product_styles and intent_styles:
        overlap = len(product_styles & intent_styles) / max(len(intent_styles), 1)
        base += overlap * 0.4
    elif not intent_styles:
        base += 0.2  # No style preference → neutral bonus.
    return min(base, 1.0)


def _color_compatibility(product: Product, intent: ProductRetrievalIntent) -> float:
    """Color compatibility: overlap between product and intent colors."""
    product_colors = set(product.colors or [])
    intent_colors = set(intent.colors)
    if not intent_colors:
        return 0.6  # No color preference → neutral.
    if not product_colors:
        return 0.3
    overlap = len(product_colors & intent_colors)
    return min(overlap / max(len(intent_colors), 1), 1.0)


def _material_compatibility(product: Product, intent: ProductRetrievalIntent) -> float:
    """Material compatibility: overlap between product and intent materials."""
    product_materials = set(product.material or [])
    intent_materials = set(intent.material)
    if not intent_materials:
        return 0.6  # No material preference → neutral.
    if not product_materials:
        return 0.3
    overlap = len(product_materials & intent_materials)
    return min(overlap / max(len(intent_materials), 1), 1.0)


def _spatial_fit(product: Product, intent: ProductRetrievalIntent) -> float:
    """Spatial fit: penalize products too large or too small for the room."""
    score = 0.5  # Base score.

    # Category match is still important for spatial fit.
    if product.category == intent.category:
        score += 0.3

    # Temperature compatibility.
    if not intent.temperature or product.temperature in {intent.temperature, None}:
        score += 0.2

    return min(score, 1.0)


def _room_type_match(product: Product, intent: ProductRetrievalIntent) -> float:
    """Room type match: does the product belong in this room type?"""
    product_rooms = set(product.room_types or [])
    intent_rooms = set(intent.room_types)
    if not intent_rooms:
        return 0.6
    if not product_rooms:
        return 0.4
    return 1.0 if product_rooms & intent_rooms else 0.2


def _product_quality(product: Product) -> float:
    """Product quality: bonus for higher quality products."""
    quality_map = {
        "premium": 1.0,
        "high": 0.8,
        "mid": 0.6,
        "standard": 0.5,
        "low": 0.3,
        "budget": 0.2,
    }
    tier = getattr(product, "quality_tier", None)
    return quality_map.get(str(tier).lower(), 0.5)
