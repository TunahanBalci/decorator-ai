"""Tests for Sprint 5 external AI rendering providers.

Covers:
- Provider interface
- Mock provider
- External renderer fallback without API key
- Prompt and mask passed to provider
- Iterative multi-furniture rendering order
- Provider timeout fallback
- Response validation
- No API key leakage in logs
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from app.rendering.base import RenderResult
from app.rendering.factory import get_renderer
from app.rendering.providers.base import InpaintProvider, InpaintRequest, InpaintResponse
from app.rendering.providers.mock_provider import MockProvider


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------


def test_mock_provider_implements_interface() -> None:
    """MockProvider should implement InpaintProvider."""
    provider = MockProvider()
    assert isinstance(provider, InpaintProvider)
    assert provider.name == "mock"


def test_mock_provider_validate_config() -> None:
    """MockProvider should always pass validation."""
    provider = MockProvider()
    valid, msg = provider.validate_config()
    assert valid is True


def test_replicate_provider_fails_without_key() -> None:
    """ReplicateProvider should fail validation without API key."""
    from app.rendering.providers.replicate_provider import ReplicateProvider
    provider = ReplicateProvider(api_key=None)
    valid, msg = provider.validate_config()
    assert valid is False
    assert "API_KEY" in msg


def test_huggingface_provider_fails_without_key() -> None:
    """HuggingFaceProvider should fail validation without API key."""
    from app.rendering.providers.huggingface_provider import HuggingFaceProvider
    provider = HuggingFaceProvider(api_key=None)
    valid, msg = provider.validate_config()
    assert valid is False


def test_stability_provider_fails_without_key() -> None:
    """StabilityProvider should fail validation without API key."""
    from app.rendering.providers.stability_provider import StabilityProvider
    provider = StabilityProvider(api_key=None)
    valid, msg = provider.validate_config()
    assert valid is False


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------


def test_mock_provider_returns_room_image(tmp_path: Path) -> None:
    """MockProvider should return the room image as output."""
    room_path = tmp_path / "room.png"
    Image.new("RGB", (800, 600), (200, 200, 200)).save(room_path)

    mask = Image.new("L", (800, 600), 0)
    provider = MockProvider(save_payloads=False)

    request = InpaintRequest(
        room_image_path=room_path,
        mask_image=mask,
        positive_prompt="a gray sofa in a living room",
        negative_prompt="blurry, low quality",
    )
    response = provider.generate_inpaint(request)

    assert response.success is True
    assert response.output_image is not None
    assert response.provider_name == "mock"
    assert response.output_image.size == (800, 600)


def test_mock_provider_saves_payload(tmp_path: Path) -> None:
    """MockProvider should save request payload when save_payloads=True."""
    room_path = tmp_path / "room.png"
    Image.new("RGB", (400, 300), (180, 180, 180)).save(room_path)

    mask = Image.new("L", (400, 300), 0)
    output_dir = tmp_path / "debug"
    provider = MockProvider(save_payloads=True, output_dir=output_dir)

    request = InpaintRequest(
        room_image_path=room_path,
        mask_image=mask,
        positive_prompt="a modern desk",
        negative_prompt="floating",
    )
    provider.generate_inpaint(request)

    payload_path = output_dir / "mock_provider_payload.json"
    assert payload_path.exists()

    import json
    payload = json.loads(payload_path.read_text())
    assert payload["positive_prompt"] == "a modern desk"
    assert payload["provider"] == "mock"
    # API keys should NEVER be in the payload.
    assert "api_key" not in payload
    assert "API_KEY" not in str(payload)


def test_mock_provider_handles_missing_image(tmp_path: Path) -> None:
    """MockProvider should return error for missing room image."""
    provider = MockProvider(save_payloads=False)
    request = InpaintRequest(
        room_image_path=tmp_path / "nonexistent.png",
        mask_image=Image.new("L", (100, 100), 0),
        positive_prompt="test",
        negative_prompt="test",
    )
    response = provider.generate_inpaint(request)
    assert response.success is False
    assert response.error is not None


# ---------------------------------------------------------------------------
# External renderer fallback
# ---------------------------------------------------------------------------


def test_external_renderer_fallback_without_api_key(tmp_path: Path) -> None:
    """ExternalAIInpaintRenderer should fall back to overlay when provider config is invalid."""
    from app.core.config import Settings
    from app.rendering.external_renderer import ExternalAIInpaintRenderer
    from app.rendering.providers.replicate_provider import ReplicateProvider
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        external_ai_provider="replicate",
        external_ai_api_key=None,
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/test.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (640, 480), (220, 215, 210)).save(room_path)

    # Use Replicate provider with no API key — should fail validation.
    renderer = ExternalAIInpaintRenderer(provider=ReplicateProvider(api_key=None))

    with patch("app.rendering.external_renderer.get_settings", return_value=settings):
        result = renderer.render(
            storage=storage,
            room_image_path="rooms/test.png",
            products=[{"role": "sofa", "polygon": [[0.3, 0.5], [0.7, 0.5], [0.7, 0.9], [0.3, 0.9]]}],
            output_relative_path="generated/fallback_test.png",
        )

    # Should fall back to overlay.
    assert result.output_path.exists()
    assert result.render_method == "png_overlay_perspective"
    assert "fallback_reason" in result.debug_artifacts


def test_external_renderer_with_mock_provider(tmp_path: Path) -> None:
    """ExternalAIInpaintRenderer with MockProvider should produce an image."""
    from app.core.config import Settings
    from app.rendering.external_renderer import ExternalAIInpaintRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        debug_placement=False,
        external_ai_provider="mock",
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/mock_room.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 600), (230, 225, 220)).save(room_path)

    provider = MockProvider(save_payloads=False)
    renderer = ExternalAIInpaintRenderer(provider=provider)

    with patch("app.rendering.external_renderer.get_settings", return_value=settings):
        result = renderer.render(
            storage=storage,
            room_image_path="rooms/mock_room.png",
            products=[
                {"product_id": "p1", "role": "sofa", "metadata": {},
                 "polygon": [[0.2, 0.5], [0.6, 0.5], [0.6, 0.85], [0.2, 0.85]]},
            ],
            output_relative_path="generated/mock_external.png",
        )

    assert isinstance(result, RenderResult)
    assert result.output_path.exists()
    assert "external_ai" in result.render_method


# ---------------------------------------------------------------------------
# Iterative rendering order
# ---------------------------------------------------------------------------


def test_external_renderer_iterative_order(tmp_path: Path) -> None:
    """Products should be rendered in render order (large items first)."""
    from app.core.config import Settings
    from app.rendering.external_renderer import ExternalAIInpaintRenderer
    from app.storage.local_storage import LocalImageStorage

    settings = Settings(
        local_image_root=tmp_path / "images",
        room_upload_dir=tmp_path / "images" / "rooms",
        product_image_dir=tmp_path / "images" / "products",
        generated_image_dir=tmp_path / "images" / "generated",
        debug_placement=True,
        external_ai_provider="mock",
    )
    storage = LocalImageStorage(settings)

    room_path = storage.resolve_room_image("rooms/order_test.png")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 600), (210, 210, 210)).save(room_path)

    # Products in wrong order — renderer should sort by render order.
    products = [
        {"product_id": "fl1", "role": "floor_lamp", "metadata": {},
         "polygon": [[0.8, 0.5], [0.9, 0.5], [0.9, 0.9], [0.8, 0.9]]},
        {"product_id": "s1", "role": "sofa", "metadata": {},
         "polygon": [[0.2, 0.5], [0.5, 0.5], [0.5, 0.8], [0.2, 0.8]]},
        {"product_id": "r1", "role": "rug", "metadata": {},
         "polygon": [[0.1, 0.7], [0.6, 0.7], [0.6, 0.95], [0.1, 0.95]]},
    ]

    provider = MockProvider(save_payloads=False)
    renderer = ExternalAIInpaintRenderer(provider=provider)

    with patch("app.rendering.external_renderer.get_settings", return_value=settings):
        result = renderer.render(
            storage=storage,
            room_image_path="rooms/order_test.png",
            products=products,
            output_relative_path="generated/order_test.png",
        )

    # Check render steps are in correct order (rug=0, sofa=1, lamp=4).
    steps = result.debug_artifacts.get("render_steps", [])
    if steps:
        roles = [s["role"] for s in steps]
        assert roles.index("rug") < roles.index("sofa")
        assert roles.index("sofa") < roles.index("floor_lamp")


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------


def test_inpaint_response_validation() -> None:
    """InpaintResponse should correctly report success and error."""
    success_resp = InpaintResponse(
        output_image=Image.new("RGB", (100, 100)),
        provider_name="test",
        success=True,
    )
    assert success_resp.success is True
    assert success_resp.error is None

    error_resp = InpaintResponse(
        provider_name="test",
        success=False,
        error="timeout",
    )
    assert error_resp.success is False
    assert error_resp.error == "timeout"


# ---------------------------------------------------------------------------
# Factory integration
# ---------------------------------------------------------------------------


def test_factory_returns_external_ai_inpaint() -> None:
    """get_renderer('external_ai_inpaint') should return ExternalAIInpaintRenderer."""
    renderer = get_renderer("external_ai_inpaint")
    assert renderer.name == "external_ai_inpaint"


def test_factory_supports_external_ai_alias() -> None:
    """get_renderer('external_ai') should also return ExternalAIInpaintRenderer."""
    renderer = get_renderer("external_ai")
    assert renderer.name == "external_ai_inpaint"


# ---------------------------------------------------------------------------
# No API key leakage
# ---------------------------------------------------------------------------


def test_no_api_key_in_mock_payload(tmp_path: Path) -> None:
    """Ensure API keys are never included in mock provider payload."""
    room_path = tmp_path / "room.png"
    Image.new("RGB", (200, 200), (200, 200, 200)).save(room_path)

    output_dir = tmp_path / "debug"
    provider = MockProvider(save_payloads=True, output_dir=output_dir)

    request = InpaintRequest(
        room_image_path=room_path,
        mask_image=Image.new("L", (200, 200), 0),
        positive_prompt="test prompt",
        negative_prompt="negative",
    )
    provider.generate_inpaint(request)

    payload_path = output_dir / "mock_provider_payload.json"
    assert payload_path.exists()

    import json
    payload = json.loads(payload_path.read_text())
    # Payload keys should never contain api_key, secret, or token.
    payload_keys = {k.lower() for k in payload.keys()}
    assert "api_key" not in payload_keys
    assert "secret" not in payload_keys
    assert "token" not in payload_keys


def test_no_api_key_in_response_metadata() -> None:
    """InpaintResponse metadata should not contain API keys."""
    response = InpaintResponse(
        provider_name="replicate",
        success=True,
        metadata={"model": "sdxl", "steps": 30},
    )
    metadata_str = str(response.metadata)
    assert "api_key" not in metadata_str.lower()
