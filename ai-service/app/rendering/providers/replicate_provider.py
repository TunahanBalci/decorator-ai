"""Replicate provider — placeholder for Replicate API integration.

When implemented, this provider will call the Replicate API to run
SDXL inpainting models (e.g. ``stability-ai/sdxl``) via their HTTP API.

Requirements:
- ``EXTERNAL_AI_API_KEY`` set to a valid Replicate API token
- ``replicate`` Python package installed (``pip install replicate``)
"""

from __future__ import annotations

import structlog

from app.rendering.providers.base import InpaintProvider, InpaintRequest, InpaintResponse

logger = structlog.get_logger(__name__)


class ReplicateProvider(InpaintProvider):
    """Replicate API provider (not yet implemented).

    To implement:
    1. Install ``replicate`` package
    2. Set ``EXTERNAL_AI_API_KEY`` to your Replicate API token
    3. Implement :meth:`generate_inpaint` using ``replicate.run()``

    Example implementation::

        import replicate
        output = replicate.run(
            "stability-ai/sdxl:...",
            input={
                "image": open(request.room_image_path, "rb"),
                "mask": mask_bytes,
                "prompt": request.positive_prompt,
                "negative_prompt": request.negative_prompt,
            }
        )
    """

    def __init__(self, api_key: str | None = None, model_id: str | None = None):
        self._api_key = api_key
        self._model_id = model_id or "stability-ai/sdxl"

    @property
    def name(self) -> str:
        return "replicate"

    def generate_inpaint(self, request: InpaintRequest) -> InpaintResponse:
        return InpaintResponse(
            provider_name=self.name,
            success=False,
            error="Replicate provider not yet implemented. Set external_ai_provider=mock for testing.",
        )

    def validate_config(self) -> tuple[bool, str]:
        if not self._api_key:
            return False, "EXTERNAL_AI_API_KEY not set for Replicate provider."
        return True, "OK"
