"""Mock inpainting provider — runs without API keys or GPU.

Accepts the same request shape as real providers, saves the request payload
for debugging, and returns the original room image as the "generated" output.
This allows the full pipeline to be tested end-to-end offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from PIL import Image

from app.rendering.providers.base import InpaintProvider, InpaintRequest, InpaintResponse

logger = structlog.get_logger(__name__)


class MockProvider(InpaintProvider):
    """Mock provider: saves payloads, returns room image as output.

    When ``save_payloads=True``, writes request details (prompt, mask path,
    settings) to a JSON file alongside the output.  API keys are never
    included in saved payloads.
    """

    def __init__(self, save_payloads: bool = True, output_dir: Path | None = None):
        self._save_payloads = save_payloads
        self._output_dir = output_dir

    @property
    def name(self) -> str:
        return "mock"

    def generate_inpaint(self, request: InpaintRequest) -> InpaintResponse:
        """Return the room image as-is, simulating a successful generation."""
        try:
            room_image = Image.open(request.room_image_path).convert("RGB")
        except Exception as exc:
            return InpaintResponse(
                provider_name=self.name,
                success=False,
                error=f"Failed to open room image: {exc}",
            )

        # Save debug payload.
        if self._save_payloads and self._output_dir:
            self._save_request_payload(request)

        logger.info(
            "mock_provider_generate_inpaint",
            room_image=str(request.room_image_path),
            prompt_preview=request.positive_prompt[:80],
            image_size=request.image_size,
        )

        return InpaintResponse(
            output_image=room_image,
            provider_name=self.name,
            success=True,
            metadata={
                "mode": "mock",
                "note": "Room image returned unchanged. Connect a real provider for AI generation.",
                "prompt": request.positive_prompt,
                "negative_prompt": request.negative_prompt,
                "image_size": request.image_size,
            },
        )

    def _save_request_payload(self, request: InpaintRequest) -> None:
        """Save the request payload for debugging (never includes API keys)."""
        payload = {
            "provider": self.name,
            "room_image_path": str(request.room_image_path),
            "positive_prompt": request.positive_prompt,
            "negative_prompt": request.negative_prompt,
            "image_size": request.image_size,
            "guidance_scale": request.guidance_scale,
            "num_inference_steps": request.num_inference_steps,
            "strength": request.strength,
            "seed": request.seed,
        }
        try:
            output_dir = self._output_dir or Path("/tmp")
            output_dir.mkdir(parents=True, exist_ok=True)
            payload_path = output_dir / "mock_provider_payload.json"
            payload_path.write_text(json.dumps(payload, indent=2))
            logger.debug("mock_provider_payload_saved", path=str(payload_path))
        except Exception as exc:
            logger.warning("mock_provider_payload_save_failed", error=str(exc))
