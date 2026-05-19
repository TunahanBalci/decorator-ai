"""Abstract provider interface for AI inpainting backends.

Every provider implements :meth:`generate_inpaint`, which takes a room image,
mask, and prompts, and returns a generated output image.  This decouples
the rendering pipeline from any specific AI service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image


@dataclass
class InpaintRequest:
    """Encapsulates all inputs for an inpainting request."""

    room_image_path: Path
    mask_image: Image.Image
    positive_prompt: str
    negative_prompt: str
    image_size: int = 1024
    guidance_scale: float = 7.5
    num_inference_steps: int = 30
    strength: float = 0.85
    seed: int | None = None


@dataclass
class InpaintResponse:
    """Encapsulates provider response."""

    output_image: Image.Image | None = None
    output_path: Path | None = None
    provider_name: str = ""
    success: bool = False
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class InpaintProvider(ABC):
    """Interface for AI inpainting service providers.

    Subclass and implement :meth:`generate_inpaint` for each backend.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short provider identifier (e.g. ``"replicate"``)."""

    @abstractmethod
    def generate_inpaint(self, request: InpaintRequest) -> InpaintResponse:
        """Generate an inpainted image.

        Args:
            request: The inpainting request with room image, mask, and prompts.

        Returns:
            An :class:`InpaintResponse` with the output image or error.
        """

    def validate_config(self) -> tuple[bool, str]:
        """Check if the provider is properly configured.

        Returns:
            ``(is_valid, message)`` tuple.
        """
        return True, "OK"
