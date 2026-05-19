"""Hugging Face Inference API provider — placeholder.

When implemented, this provider will call the Hugging Face Inference API
to run inpainting models via ``InferenceClient.image_to_image()``.

Requirements:
- ``EXTERNAL_AI_API_KEY`` set to a valid HF API token
- ``huggingface_hub`` package installed
"""

from __future__ import annotations

import structlog

from app.rendering.providers.base import InpaintProvider, InpaintRequest, InpaintResponse

logger = structlog.get_logger(__name__)


class HuggingFaceProvider(InpaintProvider):
    """Hugging Face Inference API provider (not yet implemented)."""

    def __init__(self, api_key: str | None = None, model_id: str | None = None):
        self._api_key = api_key
        self._model_id = model_id or "stabilityai/stable-diffusion-xl-base-1.0"

    @property
    def name(self) -> str:
        return "huggingface"

    def generate_inpaint(self, request: InpaintRequest) -> InpaintResponse:
        return InpaintResponse(
            provider_name=self.name,
            success=False,
            error="Hugging Face provider not yet implemented. Set external_ai_provider=mock for testing.",
        )

    def validate_config(self) -> tuple[bool, str]:
        if not self._api_key:
            return False, "EXTERNAL_AI_API_KEY not set for Hugging Face provider."
        return True, "OK"
