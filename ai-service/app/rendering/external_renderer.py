"""External AI inpainting renderer — cloud-based rendering via providers.

This renderer integrates with external AI services (Replicate, HF, Stability,
or mock) for furniture inpainting.  It:

1. Generates masks for each furniture placement
2. Builds inpainting prompts from product metadata
3. Calls the configured provider for each furniture item (iterative rendering)
4. Validates the output image
5. Falls back to overlay if the provider fails

Multi-furniture rendering order:
1. rug  2. bed/sofa/desk  3. table/chair  4. lamps/decor
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from PIL import Image

from app.core.config import get_settings
from app.layout.constraints import get_render_order
from app.rendering.base import FurnitureRenderer, RenderResult
from app.rendering.masks import generate_placement_mask, save_debug_mask
from app.rendering.overlay_renderer import OverlayRenderer
from app.rendering.prompts import build_inpainting_prompt
from app.rendering.providers.base import InpaintProvider, InpaintRequest, InpaintResponse
from app.storage.local_storage import LocalImageStorage
from app.utils.placement import image_size

logger = structlog.get_logger(__name__)


class ExternalAIInpaintRenderer(FurnitureRenderer):
    """Cloud-based AI inpainting renderer using pluggable providers.

    Uses the configured provider (mock, replicate, huggingface, stability)
    to generate inpainted images.  Falls back to the overlay renderer when
    the provider fails or returns an invalid result.
    """

    def __init__(self, provider: InpaintProvider | None = None):
        self._provider = provider

    @property
    def name(self) -> str:
        return "external_ai_inpaint"

    def render(
        self,
        *,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
    ) -> RenderResult:
        settings = get_settings()
        provider = self._provider or _resolve_provider(settings)
        room_path = storage.resolve_room_image(room_image_path)
        img_w, img_h = image_size(room_path)
        output_path = storage.resolve_generated_image(output_relative_path)

        debug_artifacts: dict = {}
        debug_dir = output_path.parent / "debug"

        # Validate provider configuration.
        valid, msg = provider.validate_config()
        if not valid:
            logger.warning(
                "external_ai_provider_config_invalid",
                provider=provider.name,
                message=msg,
            )
            return self._fallback_overlay(
                storage, room_image_path, products, output_relative_path,
                reason=f"Provider config invalid: {msg}",
            )

        # Sort products by render order (large items first).
        sorted_products = sorted(
            products,
            key=lambda p: get_render_order(p.get("role", "")),
        )

        # Iterative rendering: each step uses previous output as input.
        current_room_path = room_path
        render_steps: list[dict] = []

        for i, product in enumerate(sorted_products):
            polygon = product.get("polygon") or []
            if not polygon:
                continue

            role = product.get("role", "furniture")
            metadata = product.get("metadata", {})
            colors = metadata.get("colors") or []
            color = colors[0] if colors else None
            styles = metadata.get("styles") or []
            style = styles[0] if styles else None

            # 1. Generate mask.
            mask = generate_placement_mask(
                img_w, img_h, polygon,
                dilation_px=settings.mask_dilation_px,
            )

            # 2. Generate prompt.
            positive, negative = build_inpainting_prompt(
                category=role, color=color, style=style,
            )

            # 3. Save debug artifacts.
            if settings.debug_placement:
                debug_dir.mkdir(parents=True, exist_ok=True)
                mask_path = debug_dir / f"mask_{i}_{role}.png"
                save_debug_mask(mask, mask_path)

                step_log = {
                    "step": i,
                    "role": role,
                    "product_id": str(product.get("product_id", "")),
                    "positive_prompt": positive,
                    "negative_prompt": negative,
                    "provider": provider.name,
                    "input_image": str(current_room_path),
                    "mask_path": str(mask_path),
                    # Never log API keys.
                }
                render_steps.append(step_log)

            # 4. Call provider.
            try:
                request = InpaintRequest(
                    room_image_path=current_room_path,
                    mask_image=mask,
                    positive_prompt=positive,
                    negative_prompt=negative,
                    image_size=settings.external_ai_image_size,
                )

                response = provider.generate_inpaint(request)

                if not response.success or not response.output_image:
                    logger.warning(
                        "external_ai_step_failed",
                        step=i, role=role,
                        error=response.error,
                        provider=provider.name,
                    )
                    continue  # Skip this item, keep previous result.

                # 5. Validate output image.
                if not _validate_output(response.output_image, img_w, img_h):
                    logger.warning(
                        "external_ai_output_validation_failed",
                        step=i, role=role,
                    )
                    continue

                # 6. Save intermediate output for next iteration.
                intermediate_path = output_path.parent / f"intermediate_{i}_{role}.png"
                intermediate_path.parent.mkdir(parents=True, exist_ok=True)
                response.output_image.save(intermediate_path)
                current_room_path = intermediate_path

                if settings.debug_placement:
                    render_steps[-1]["output_image"] = str(intermediate_path)
                    render_steps[-1]["success"] = True

            except Exception as exc:
                logger.warning(
                    "external_ai_step_exception",
                    step=i, role=role, error=str(exc),
                )
                if settings.external_ai_fallback_to_overlay:
                    return self._fallback_overlay(
                        storage, room_image_path, products, output_relative_path,
                        reason=f"Provider exception: {exc}",
                    )

        # Save final output.
        try:
            if current_room_path != room_path:
                final_img = Image.open(current_room_path).convert("RGB")
            else:
                # No provider calls succeeded — use overlay as fallback.
                return self._fallback_overlay(
                    storage, room_image_path, products, output_relative_path,
                    reason="No provider steps succeeded",
                )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_img.save(output_path)
        except Exception as exc:
            return self._fallback_overlay(
                storage, room_image_path, products, output_relative_path,
                reason=f"Failed to save final output: {exc}",
            )

        # Save debug log.
        if settings.debug_placement and render_steps:
            debug_log_path = debug_dir / "render_log.json"
            try:
                debug_log_path.write_text(json.dumps(render_steps, indent=2))
            except Exception:
                pass
            debug_artifacts["render_steps"] = render_steps
            debug_artifacts["render_log"] = str(debug_log_path)

        logger.info(
            "external_ai_render_complete",
            provider=provider.name,
            output_path=str(output_path),
            num_steps=len(render_steps),
        )

        return RenderResult(
            relative_path=output_relative_path,
            output_path=output_path,
            render_method=f"external_ai_{provider.name}",
            debug_artifacts=debug_artifacts,
        )

    def _fallback_overlay(
        self,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
        reason: str = "",
    ) -> RenderResult:
        """Fall back to overlay renderer."""
        logger.warning(
            "external_ai_falling_back_to_overlay",
            reason=reason,
        )
        result = OverlayRenderer().render(
            storage=storage,
            room_image_path=room_image_path,
            products=products,
            output_relative_path=output_relative_path,
        )
        result.debug_artifacts["fallback_reason"] = reason
        return result


def _resolve_provider(settings) -> InpaintProvider:
    """Resolve the configured provider."""
    provider_name = settings.external_ai_provider

    if provider_name == "mock":
        from app.rendering.providers.mock_provider import MockProvider
        return MockProvider(
            save_payloads=settings.external_ai_save_payloads,
            output_dir=settings.generated_image_dir / "debug",
        )
    if provider_name == "replicate":
        from app.rendering.providers.replicate_provider import ReplicateProvider
        return ReplicateProvider(api_key=settings.external_ai_api_key)
    if provider_name == "huggingface":
        from app.rendering.providers.huggingface_provider import HuggingFaceProvider
        return HuggingFaceProvider(api_key=settings.external_ai_api_key)
    if provider_name == "stability":
        from app.rendering.providers.stability_provider import StabilityProvider
        return StabilityProvider(api_key=settings.external_ai_api_key)

    logger.warning("unknown_provider_using_mock", provider=provider_name)
    from app.rendering.providers.mock_provider import MockProvider
    return MockProvider()


def _validate_output(image: Image.Image, expected_w: int, expected_h: int) -> bool:
    """Validate that the output image is usable."""
    if image is None:
        return False
    w, h = image.size
    if w == 0 or h == 0:
        return False
    # Allow size differences (providers may resize).
    return True
