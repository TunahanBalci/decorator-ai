"""Stability AI API provider — placeholder.

When implemented, this provider will call the Stability AI REST API
for image inpainting.

Requirements:
- ``EXTERNAL_AI_API_KEY`` set to a valid Stability AI API key
- ``requests`` package (already in project dependencies)
"""

from __future__ import annotations

import structlog

from app.rendering.providers.base import InpaintProvider, InpaintRequest, InpaintResponse

logger = structlog.get_logger(__name__)


class StabilityProvider(InpaintProvider):
    """Stability AI API provider (not yet implemented)."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "stability"

    def generate_inpaint(self, request: InpaintRequest) -> InpaintResponse:
        return InpaintResponse(
            provider_name=self.name,
            success=False,
            error="Stability AI provider not yet implemented. Set external_ai_provider=mock for testing.",
        )

    def validate_config(self) -> tuple[bool, str]:
        if not self._api_key:
            return False, "EXTERNAL_AI_API_KEY not set for Stability AI provider."
        return True, "OK"
