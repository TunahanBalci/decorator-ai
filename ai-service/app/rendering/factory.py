"""Renderer factory — resolves a render method name to a concrete renderer.

The factory centralises renderer selection so the workflow node only needs
to call ``get_renderer(settings.render_method)`` and never imports concrete
renderer classes directly.

Fallback chain:
    ``sdxl_inpaint``        → ``overlay``  (when torch/diffusers unavailable)
    ``external_ai_inpaint`` → ``overlay``  (when provider fails)
    ``mock_inpaint``        → always works (uses overlay internally)
    ``overlay``             → always works
"""

from __future__ import annotations

import structlog

from app.rendering.base import FurnitureRenderer

logger = structlog.get_logger(__name__)


def get_renderer(method: str = "overlay") -> FurnitureRenderer:
    """Return a :class:`FurnitureRenderer` for the given render method.

    Args:
        method: One of ``"overlay"``, ``"mock_inpaint"``, ``"sdxl_inpaint"``,
            ``"external_ai_inpaint"``.  Unknown values fall back to ``"overlay"``.

    Returns:
        A ready-to-use :class:`FurnitureRenderer` instance.
    """
    if method == "overlay":
        return _overlay()

    if method == "mock_inpaint":
        return _mock_inpaint()

    if method == "sdxl_inpaint":
        return _sdxl_inpaint_or_fallback()

    if method in ("external_ai", "external_ai_inpaint"):
        return _external_ai()

    logger.warning("unknown_render_method_falling_back_to_overlay", method=method)
    return _overlay()


# ---------------------------------------------------------------------------
# Private factory helpers
# ---------------------------------------------------------------------------


def _overlay() -> FurnitureRenderer:
    from app.rendering.overlay_renderer import OverlayRenderer
    return OverlayRenderer()


def _mock_inpaint() -> FurnitureRenderer:
    from app.rendering.mock_inpaint_renderer import MockInpaintRenderer
    return MockInpaintRenderer()


def _sdxl_inpaint_or_fallback() -> FurnitureRenderer:
    """Try to create SDXL renderer; fall back to overlay if deps missing."""
    try:
        import torch  # noqa: F401
        import diffusers  # noqa: F401
    except ImportError:
        logger.warning(
            "sdxl_dependencies_not_available",
            message="torch and/or diffusers not installed. "
                    "Falling back to overlay renderer. "
                    "Install with: pip install torch diffusers[torch] transformers accelerate",
        )
        return _overlay()

    # When real SDXL renderer is implemented, import and return it here.
    logger.info("sdxl_renderer_not_yet_implemented_using_mock_inpaint")
    return _mock_inpaint()


def _external_ai() -> FurnitureRenderer:
    """Return the external AI inpaint renderer (Sprint 5)."""
    from app.rendering.external_renderer import ExternalAIInpaintRenderer
    return ExternalAIInpaintRenderer()
