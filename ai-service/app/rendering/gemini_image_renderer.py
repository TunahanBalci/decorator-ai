"""Gemini image-edit renderer for final room design images."""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from PIL import Image

from app.ai.vertex_client import VertexAIClient
from app.core.config import get_settings
from app.core.errors import AIOutputValidationError
from app.rendering.base import FurnitureRenderer, RenderResult
from app.rendering.overlay_renderer import OverlayRenderer
from app.storage.local_storage import LocalImageStorage
from app.utils.composite import _load_product_image_raw

logger = structlog.get_logger(__name__)


class GeminiImageEditRenderer(FurnitureRenderer):
    """Render the final room image with Gemini native image editing.

    The overlay renderer is deterministic but limited: it pastes product cutouts
    and can only approximate perspective. Gemini receives the room photograph and
    product reference images, then edits the room directly so it can remove white
    product backgrounds, fit objects to perspective, and blend lighting/shadows.
    """

    @property
    def name(self) -> str:
        return "gemini_image_edit"

    def render(
        self,
        *,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
    ) -> RenderResult:
        settings = get_settings()
        room_path = storage.resolve_room_image(room_image_path)
        output_path = storage.resolve_generated_image(output_relative_path)

        if not settings.enable_image_generation or not settings.vertex_project_id:
            return self._fallback_overlay(
                storage,
                room_image_path,
                products,
                output_relative_path,
                reason="Gemini image editing is not configured",
            )

        reference_paths, reference_manifest = _prepare_product_references(
            storage=storage,
            products=products,
            output_dir=output_path.parent / "gemini_references",
        )
        if not reference_paths:
            return self._fallback_overlay(
                storage,
                room_image_path,
                products,
                output_relative_path,
                reason="No product reference images were available for Gemini",
            )

        prompt = _build_gemini_edit_prompt(products, reference_manifest)
        try:
            VertexAIClient(settings).generate_image_edit(
                prompt=prompt,
                images=[room_path, *reference_paths],
                output_path=output_path,
            )
        except AIOutputValidationError as exc:
            return self._fallback_overlay(
                storage,
                room_image_path,
                products,
                output_relative_path,
                reason=f"Gemini image edit failed: {exc}",
            )

        logger.info(
            "gemini_image_edit_complete",
            model=settings.vertex_image_model_id,
            output_path=str(output_path),
            product_count=len(reference_paths),
        )
        return RenderResult(
            relative_path=output_relative_path,
            output_path=output_path,
            render_method=f"gemini_image_edit:{settings.vertex_image_model_id}",
            debug_artifacts={
                "model": settings.vertex_image_model_id,
                "reference_products": reference_manifest,
            } if settings.debug_placement else {},
        )

    def _fallback_overlay(
        self,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
        reason: str,
    ) -> RenderResult:
        logger.warning("gemini_image_edit_falling_back_to_overlay", reason=reason)
        result = OverlayRenderer().render(
            storage=storage,
            room_image_path=room_image_path,
            products=products,
            output_relative_path=output_relative_path,
        )
        result.debug_artifacts["fallback_reason"] = reason
        return result


def _prepare_product_references(
    *,
    storage: LocalImageStorage,
    products: list[dict],
    output_dir: Path,
) -> tuple[list[Path], list[dict]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    manifest: list[dict] = []

    for index, product in enumerate(products, start=1):
        image = _load_product_image_raw(storage, product.get("image_path"))
        if image is None:
            logger.warning(
                "gemini_reference_product_image_missing",
                product_id=str(product.get("product_id", "")),
                image_path=product.get("image_path"),
            )
            continue

        reference_path = output_dir / f"product_{index}.png"
        _save_reference_image(image, reference_path)
        paths.append(reference_path)
        manifest.append(
            {
                "reference_image_number": len(paths),
                "product_id": str(product.get("product_id", "")),
                "name": product.get("name"),
                "role": product.get("role"),
                "category": product.get("category"),
                "target_polygon_normalized": product.get("polygon"),
                "scale_hint": product.get("scale"),
                "rotation_hint_degrees": product.get("rotation"),
            }
        )
    return paths, manifest


def _save_reference_image(image: Image.Image, path: Path) -> None:
    rgba = image.convert("RGBA")
    rgba.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(path)


def _build_gemini_edit_prompt(products: list[dict], reference_manifest: list[dict]) -> str:
    product_context = [
        {
            "product_id": str(product.get("product_id", "")),
            "name": product.get("name"),
            "role": product.get("role"),
            "category": product.get("category"),
            "target_polygon_normalized": product.get("polygon"),
            "scale_hint": product.get("scale"),
            "rotation_hint_degrees": product.get("rotation"),
            "metadata": product.get("metadata") or {},
        }
        for product in products
    ]

    return (
        "Edit the first input image, which is the user's room photo. "
        "The following input images are catalog product references in the same "
        "order as reference_products. Create one photorealistic final room image.\n\n"
        "Use the catalog references as identity, shape, material, and color guidance, "
        "but do not paste them as flat cutouts. Product reference photos often have "
        "white or solid studio backgrounds; remove those backgrounds completely. "
        "Adapt each product to the room perspective, camera angle, scale, rotation, "
        "contact shadows, occlusion, and lighting.\n\n"
        "The placement polygons are normalized room-image coordinates. Treat them as "
        "soft placement guidance, not rigid boxes. Prefer a believable interior-design "
        "edit over exact polygon filling if perspective, size, or collisions require "
        "small adjustments. Do not add white rectangles, borders, labels, watermarks, "
        "debug overlays, or extra furniture that is not requested. Preserve walls, "
        "floor, windows, doors, and fixed architecture from the original room photo.\n\n"
        f"reference_products:\n{json.dumps(reference_manifest, ensure_ascii=False, indent=2)}\n\n"
        f"all_selected_products:\n{json.dumps(product_context, ensure_ascii=False, indent=2)}"
    )
