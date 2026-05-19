"""Abstract base class for furniture renderers.

Every renderer accepts the same inputs (room image, products with normalized
placement polygons, output path) and returns the same outputs (relative path,
absolute path).  This makes the rendering step in the workflow pipeline
swappable without touching any other node.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.storage.local_storage import LocalImageStorage


class RenderResult:
    """Container for renderer output."""

    __slots__ = ("relative_path", "output_path", "render_method", "debug_artifacts")

    def __init__(
        self,
        relative_path: str,
        output_path: Path,
        render_method: str,
        debug_artifacts: dict | None = None,
    ):
        self.relative_path = relative_path
        self.output_path = output_path
        self.render_method = render_method
        self.debug_artifacts = debug_artifacts or {}


class FurnitureRenderer(ABC):
    """Interface that all renderers must implement.

    Subclasses may add GPU-specific initialisation or model loading, but the
    public ``render`` contract stays identical so the workflow node never
    needs to know which concrete renderer is active.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this renderer (e.g. ``"overlay"``)."""

    @abstractmethod
    def render(
        self,
        *,
        storage: LocalImageStorage,
        room_image_path: str,
        products: list[dict],
        output_relative_path: str,
    ) -> RenderResult:
        """Render furniture onto the room image.

        Args:
            storage: Resolved image storage helper.
            room_image_path: Relative path to the uploaded room image.
            products: List of product dicts, each containing at minimum
                ``polygon`` (normalized coordinates) and optionally
                ``image_path``, ``role``, ``name``, ``product_id``.
            output_relative_path: Where to write the composite image
                (relative to ``GENERATED_IMAGE_DIR``).

        Returns:
            A :class:`RenderResult` with paths and metadata.
        """
