"""Tests for Sprint 4 enhanced product scoring."""

from unittest.mock import MagicMock

from app.schemas.ai_outputs import RoomStyleProfile
from app.utils.scoring import score_product


def _make_product(**overrides) -> MagicMock:
    """Create a mock Product with default attributes."""
    product = MagicMock()
    product.category = overrides.get("category", "sofa")
    product.styles = overrides.get("styles", ["modern"])
    product.colors = overrides.get("colors", ["gray"])
    product.material = overrides.get("material", ["fabric"])
    product.room_types = overrides.get("room_types", ["living_room"])
    product.temperature = overrides.get("temperature", "warm")
    product.quality_tier = overrides.get("quality_tier", "standard")
    return product


def _make_intent(**overrides) -> MagicMock:
    """Create a mock ProductRetrievalIntent with defaults."""
    intent = MagicMock()
    intent.category = overrides.get("category", "sofa")
    intent.styles = overrides.get("styles", ["modern"])
    intent.colors = overrides.get("colors", ["gray"])
    intent.material = overrides.get("material", ["fabric"])
    intent.room_types = overrides.get("room_types", ["living_room"])
    intent.temperature = overrides.get("temperature", "warm")
    return intent


def test_perfect_match_scores_high() -> None:
    """Product matching all intent criteria should score highly."""
    product = _make_product()
    intent = _make_intent()
    score = score_product(product, intent, semantic_score=0.9)
    assert score >= 0.70, f"Perfect match should score >= 0.70, got {score}"


def test_style_similarity_boosts_score() -> None:
    """Product with matching style should score higher than mismatched."""
    matching = _make_product(styles=["scandinavian"])
    mismatching = _make_product(styles=["industrial"])
    intent = _make_intent(styles=["scandinavian"])

    score_match = score_product(matching, intent, semantic_score=0.5)
    score_mismatch = score_product(mismatching, intent, semantic_score=0.5)
    assert score_match > score_mismatch


def test_color_compatibility_scoring() -> None:
    """Product with matching colors should score higher."""
    matching = _make_product(colors=["white", "oak"])
    mismatching = _make_product(colors=["red", "black"])
    intent = _make_intent(colors=["white", "oak"])

    score_match = score_product(matching, intent)
    score_mismatch = score_product(mismatching, intent)
    assert score_match > score_mismatch


def test_material_compatibility() -> None:
    """Product with matching material should score higher."""
    matching = _make_product(material=["wood"])
    mismatching = _make_product(material=["metal"])
    intent = _make_intent(material=["wood"])

    score_match = score_product(matching, intent)
    score_mismatch = score_product(mismatching, intent)
    assert score_match > score_mismatch


def test_room_type_match() -> None:
    """Product matching room type should score higher."""
    matching = _make_product(room_types=["bedroom"])
    mismatching = _make_product(room_types=["office"])
    intent = _make_intent(room_types=["bedroom"])

    score_match = score_product(matching, intent)
    score_mismatch = score_product(mismatching, intent)
    assert score_match > score_mismatch


def test_quality_tier_bonus() -> None:
    """Premium products should score higher on quality dimension."""
    premium = _make_product(quality_tier="premium")
    budget = _make_product(quality_tier="budget")
    intent = _make_intent()

    score_premium = score_product(premium, intent)
    score_budget = score_product(budget, intent)
    assert score_premium > score_budget


def test_score_is_bounded() -> None:
    """Score should always be in [0.0, 1.0]."""
    product = _make_product()
    intent = _make_intent()
    for sem in [0.0, 0.5, 1.0]:
        score = score_product(product, intent, semantic_score=sem)
        assert 0.0 <= score <= 1.0, f"Score {score} out of bounds"


def test_no_preferences_gives_neutral_score() -> None:
    """When intent has no preferences, score should be neutral."""
    product = _make_product()
    intent = _make_intent(styles=[], colors=[], material=[], room_types=[])
    score = score_product(product, intent)
    assert 0.3 <= score <= 0.8, f"Neutral score should be moderate, got {score}"


def test_room_style_profile_schema() -> None:
    """RoomStyleProfile should serialize correctly."""
    profile = RoomStyleProfile(
        style="scandinavian",
        confidence=0.84,
        dominant_colors=["white", "light_gray", "oak"],
        materials=["wood", "fabric"],
        room_type="living_room",
        design_mood="minimal and cozy",
    )
    assert profile.style == "scandinavian"
    assert profile.confidence == 0.84
    assert "wood" in profile.materials
    assert profile.design_mood == "minimal and cozy"
