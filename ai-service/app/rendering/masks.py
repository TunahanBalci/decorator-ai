"""Inpainting mask generation.

Generates binary masks (white = area to inpaint, black = preserve) from
normalized placement polygons.  These masks are used by the mock renderer
for debug output and will be consumed by real SDXL inpainting when
GPU infrastructure is available.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from PIL import Image, ImageDraw, ImageFilter

logger = structlog.get_logger(__name__)


def generate_placement_mask(
    image_width: int,
    image_height: int,
    polygon: list[list[float]],
    dilation_px: int = 10,
) -> Image.Image:
    """Create a white-on-black inpainting mask for a single furniture placement.

    The mask marks the region where the furniture should be painted by the
    inpainting model.  A slight dilation improves blending by giving the
    model room to feather the edges.

    Args:
        image_width: Room image width in pixels.
        image_height: Room image height in pixels.
        polygon: Normalized placement polygon ``[[x1,y1], ...]`` with values
            in ``[0.0, 1.0]``.
        dilation_px: Number of pixels to dilate the mask boundary.

    Returns:
        A single-channel ``"L"`` mode :class:`~PIL.Image.Image` where
        white (255) marks the inpaint region and black (0) marks preserved
        areas.
    """
    mask = Image.new("L", (image_width, image_height), 0)
    if not polygon:
        return mask

    # Convert normalized polygon → pixel coordinates.
    pixel_points = [
        (x * image_width, y * image_height) for x, y in polygon
    ]

    draw = ImageDraw.Draw(mask)
    draw.polygon(pixel_points, fill=255)

    # Dilate the mask for better blending at edges.
    if dilation_px > 0:
        mask = mask.filter(ImageFilter.MaxFilter(size=dilation_px * 2 + 1))

    return mask


def generate_combined_mask(
    image_width: int,
    image_height: int,
    polygons: list[list[list[float]]],
    dilation_px: int = 10,
) -> Image.Image:
    """Generate a single mask covering multiple furniture placements.

    Useful for batch inpainting where all furniture areas are painted in one
    pass.

    Args:
        image_width: Room image width in pixels.
        image_height: Room image height in pixels.
        polygons: List of normalized placement polygons.
        dilation_px: Dilation applied to each individual mask.

    Returns:
        Combined ``"L"`` mode mask.
    """
    combined = Image.new("L", (image_width, image_height), 0)
    for polygon in polygons:
        individual = generate_placement_mask(
            image_width, image_height, polygon, dilation_px
        )
        # Merge: take the maximum (union of masks).
        from PIL import ImageChops
        combined = ImageChops.lighter(combined, individual)
    return combined


def save_debug_mask(
    mask: Image.Image,
    output_path: Path,
) -> None:
    """Save a mask image for debug inspection.

    Args:
        mask: The mask to save.
        output_path: Absolute path to write the mask PNG.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mask.save(output_path)
    logger.debug("debug_mask_saved", path=str(output_path))
