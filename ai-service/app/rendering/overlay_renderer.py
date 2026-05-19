"""Overlay renderer — wraps the Sprint 2 perspective-aware composite.

This is the default renderer.  It requires no GPU, no ``torch``, and no
external AI services.  It produces the best result achievable with pure
Pillow compositing: perspective-scaled furniture, bottom-center anchoring,
and soft shadow rendering.
"""

from __future__ import annotations

from app.rendering.base import FurnitureRenderer, RenderResult
from app.storage.local_storage import LocalImageStorage
from app.utils.composite import render_placeholder_composite


class OverlayRenderer(FurnitureRenderer):
    """Sprint 2 PNG overlay with perspective scaling and shadow."""

    @property
    def name(self) -> str:
        return "overlay"

    def render(
        self,
        *,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
    ) -> RenderResult:
        relative_path, output_path = render_placeholder_composite(
            storage=storage,
            room_image_path=room_image_path,
            products=products,
            output_relative_path=output_relative_path,
        )
        return RenderResult(
            relative_path=relative_path,
            output_path=output_path,
            render_method="png_overlay_perspective",
        )
