"""Mock inpainting renderer.

Simulates the full SDXL inpainting pipeline without requiring GPU, ``torch``,
or ``diffusers``.  It exercises the complete rendering architecture — mask
generation, prompt generation, debug artifact saving — and returns the overlay
result as the final image.

This renderer exists so the full pipeline can be tested and debugged end-to-end
without GPU infrastructure.  When real SDXL support is added, only the actual
inference step changes; everything else (mask, prompt, debug output) is reused.
"""

from __future__ import annotations

import structlog

from app.core.config import get_settings
from app.rendering.base import FurnitureRenderer, RenderResult
from app.rendering.masks import generate_placement_mask, save_debug_mask
from app.rendering.overlay_renderer import OverlayRenderer
from app.rendering.prompts import build_inpainting_prompt
from app.storage.local_storage import LocalImageStorage
from app.utils.placement import image_size

logger = structlog.get_logger(__name__)


class MockInpaintRenderer(FurnitureRenderer):
    """Simulates SDXL inpainting: generates masks + prompts, renders via overlay.

    Debug artifacts written when ``DEBUG_PLACEMENT=true``:
    - Mask images for each furniture placement
    - Generated prompts logged via structlog
    - Combined mask for the full scene
    """

    @property
    def name(self) -> str:
        return "mock_inpaint"

    def render(
        self,
        *,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
    ) -> RenderResult:
        settings = get_settings()

        # Resolve room image dimensions for mask generation.
        room_path = storage.resolve_room_image(room_image_path)
        img_w, img_h = image_size(room_path)

        debug_artifacts: dict = {}
        prompts: list[dict] = []

        for i, product in enumerate(products):
            polygon = product.get("polygon") or []
            if not polygon:
                continue

            # ---- 1. Generate inpainting mask ----------------------------
            mask = generate_placement_mask(
                img_w, img_h, polygon,
                dilation_px=settings.mask_dilation_px,
            )

            # ---- 2. Generate inpainting prompt --------------------------
            role = product.get("role", "furniture")
            metadata = product.get("metadata", {})
            colors = metadata.get("colors") or []
            color = colors[0] if colors else None
            styles = metadata.get("styles") or []
            style = styles[0] if styles else None

            positive, negative = build_inpainting_prompt(
                category=role,
                color=color,
                style=style,
                room_type=None,  # Could be passed from room_analysis
            )

            prompt_info = {
                "product_id": str(product.get("product_id", "")),
                "role": role,
                "positive_prompt": positive,
                "negative_prompt": negative,
            }
            prompts.append(prompt_info)

            logger.info(
                "mock_inpaint_prompt_generated",
                product_index=i,
                **prompt_info,
            )

            # ---- 3. Save debug mask when DEBUG_PLACEMENT is enabled -----
            if settings.debug_placement:
                mask_relative = output_relative_path.replace(
                    ".png", f"_mask_{i}.png"
                )
                mask_path = storage.resolve_generated_image(mask_relative)
                save_debug_mask(mask, mask_path)
                debug_artifacts[f"mask_{i}"] = mask_relative

                logger.info(
                    "mock_inpaint_debug_mask_saved",
                    product_index=i,
                    mask_path=mask_relative,
                    mask_size={"w": mask.width, "h": mask.height},
                )

        # ---- 4. Actual rendering: delegate to overlay -------------------
        # The mock renderer produces the same visual output as overlay.
        # When real SDXL is available, this step will be replaced with
        # actual diffusion inference using the masks and prompts above.
        overlay = OverlayRenderer()
        overlay_result = overlay.render(
            storage=storage,
            room_image_path=room_image_path,
            products=products,
            output_relative_path=output_relative_path,
        )

        debug_artifacts["prompts"] = prompts
        debug_artifacts["render_note"] = (
            "Mock inpainting: masks and prompts generated, overlay used for final image. "
            "Replace with real SDXL inference when GPU is available."
        )

        logger.info(
            "mock_inpaint_render_complete",
            output_path=str(overlay_result.output_path),
            num_products=len(products),
            num_masks=len([k for k in debug_artifacts if k.startswith("mask_")]),
            num_prompts=len(prompts),
        )

        return RenderResult(
            relative_path=overlay_result.relative_path,
            output_path=overlay_result.output_path,
            render_method="mock_inpaint",
            debug_artifacts=debug_artifacts,
        )
