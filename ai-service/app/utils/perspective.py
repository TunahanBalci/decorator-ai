"""Sprint 2 — Perspective-aware rendering utilities.

Provides pure functions for depth-based furniture scaling, bottom-center
anchoring, soft shadow generation, and optional horizontal perspective skew.
All visual-realism logic lives here so that ``composite.py`` stays focused on
canvas orchestration.
"""

from __future__ import annotations

import structlog
from PIL import Image, ImageFilter

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Perspective-aware scaling
# ---------------------------------------------------------------------------

def compute_perspective_scale(
    normalized_y: float,
    min_scale: float = 0.35,
    max_scale: float = 1.2,
) -> float:
    """Return a scale factor based on vertical position in the image.

    The key insight is that objects lower in the image (higher ``normalized_y``)
    are closer to the camera and should appear **larger**, while objects higher
    in the image (lower ``normalized_y``) are farther away and should appear
    **smaller**.

    Formula::

        scale = min_scale + (clamped_y × (max_scale − min_scale))

    Args:
        normalized_y: Vertical position in ``[0.0, 1.0]``.
            0.0 = top of image (far from camera).
            1.0 = bottom of image (close to camera).
        min_scale: Scale factor at the top of the image.
        max_scale: Scale factor at the bottom of the image.

    Returns:
        A float clamped to ``[min_scale, max_scale]``.
    """
    clamped_y = max(0.0, min(1.0, normalized_y))
    scale = min_scale + clamped_y * (max_scale - min_scale)
    # Defensive clamp in case min/max are swapped or close to each other.
    return max(min_scale, min(max_scale, scale))


def compute_furniture_dimensions(
    scale: float,
    default_width: int,
    aspect_ratio: float,
) -> tuple[int, int]:
    """Compute pixel dimensions for a furniture image after scaling.

    Args:
        scale: Perspective scale factor (from :func:`compute_perspective_scale`).
        default_width: Base furniture width in pixels at ``scale = 1.0``.
        aspect_ratio: ``width / height`` of the original furniture image.

    Returns:
        ``(width_px, height_px)`` — both guaranteed ≥ 1.
    """
    width = max(1, int(default_width * scale))
    height = max(1, int(width / aspect_ratio)) if aspect_ratio > 0 else width
    return width, height


# ---------------------------------------------------------------------------
# 2. Bottom-center anchoring
# ---------------------------------------------------------------------------

def anchor_bottom_center(
    placement_x_px: float,
    placement_y_px: float,
    furniture_width: int,
    furniture_height: int,
    image_width: int,
    image_height: int,
) -> tuple[int, int]:
    """Convert a *bottom-center* placement point to a *top-left* paste coordinate.

    The placement point represents where the furniture's bottom-center should
    sit on the floor.  We compute the top-left corner of the furniture image
    and clamp it so the furniture stays inside the canvas.

    Args:
        placement_x_px: Horizontal pixel position of the placement point.
        placement_y_px: Vertical pixel position of the placement point (floor level).
        furniture_width: Width of the (scaled) furniture image.
        furniture_height: Height of the (scaled) furniture image.
        image_width: Room image width.
        image_height: Room image height.

    Returns:
        ``(paste_x, paste_y)`` — top-left corner, clamped to image bounds.
    """
    # Bottom-center → top-left conversion.
    paste_x = int(placement_x_px - furniture_width / 2)
    paste_y = int(placement_y_px - furniture_height)

    # Clamp to image boundaries.
    paste_x = max(0, min(paste_x, image_width - furniture_width))
    paste_y = max(0, min(paste_y, image_height - furniture_height))

    return paste_x, paste_y


# ---------------------------------------------------------------------------
# 3. Shadow generation
# ---------------------------------------------------------------------------

def generate_shadow(
    furniture_rgba: Image.Image,
    opacity: float = 0.45,
    blur_radius: int = 15,
    y_offset: int = 10,
) -> Image.Image:
    """Create a soft drop shadow from a furniture image's alpha channel.

    Steps:
        1. Extract the alpha channel as a luminance mask.
        2. Build a solid-black image with that mask as its alpha.
        3. Scale alpha values by ``opacity``.
        4. Apply Gaussian blur for soft edges.
        5. Expand the canvas downward by ``y_offset`` so the shadow peeks out
           beneath the furniture.

    The returned image has the **same width** as the furniture but is taller
    by ``y_offset`` pixels.  The caller should paste it offset by
    ``(0, y_offset)`` relative to the furniture paste coordinate so the
    shadow appears *behind* and *below* the furniture.

    Args:
        furniture_rgba: The furniture image in RGBA mode.
        opacity: Shadow darkness in ``[0.0, 1.0]``.
        blur_radius: Gaussian blur radius in pixels.
        y_offset: How many pixels the shadow shifts downward.

    Returns:
        An RGBA :class:`~PIL.Image.Image` containing the shadow.
    """
    if furniture_rgba.mode != "RGBA":
        furniture_rgba = furniture_rgba.convert("RGBA")

    width, height = furniture_rgba.size
    shadow_height = height + abs(y_offset)

    # 1. Extract alpha → silhouette.
    alpha = furniture_rgba.split()[3]  # A channel

    # 2. Build black image and apply the furniture silhouette as alpha.
    shadow = Image.new("RGBA", (width, shadow_height), (0, 0, 0, 0))
    silhouette = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    silhouette.putalpha(alpha)

    # 3. Paste silhouette shifted down by y_offset.
    shadow.paste(silhouette, (0, abs(y_offset)), silhouette)

    # 4. Scale alpha by opacity.
    shadow_alpha = shadow.split()[3]
    shadow_alpha = shadow_alpha.point(lambda a: int(a * min(max(opacity, 0.0), 1.0)))
    shadow.putalpha(shadow_alpha)

    # 5. Apply Gaussian blur.
    if blur_radius > 0:
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    return shadow


# ---------------------------------------------------------------------------
# 4. Optional perspective skew (OpenCV)
# ---------------------------------------------------------------------------

def apply_perspective_skew(
    furniture_rgba: Image.Image,
    normalized_x: float,
    max_skew_pixels: float = 12.0,
) -> Image.Image:
    """Apply a subtle horizontal perspective warp based on x-position.

    Objects on the left side of the image lean slightly right (positive skew)
    and objects on the right lean slightly left (negative skew).  Objects in
    the center receive no skew.

    This uses OpenCV's ``warpPerspective``.  If OpenCV is unavailable or the
    warp fails, the original image is returned unchanged.

    Args:
        furniture_rgba: Furniture image in RGBA mode.
        normalized_x: Horizontal placement position in ``[0.0, 1.0]``.
            0.0 = left edge, 0.5 = center, 1.0 = right edge.
        max_skew_pixels: Maximum horizontal shift applied to the top corners.

    Returns:
        The (possibly skewed) RGBA image.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.debug("opencv_not_available_skipping_perspective_skew")
        return furniture_rgba

    # Deviation from center: -0.5 (left) to +0.5 (right).
    deviation = normalized_x - 0.5
    skew_px = deviation * max_skew_pixels * 2  # full range: ±max_skew_pixels

    if abs(skew_px) < 0.5:
        return furniture_rgba  # negligible — skip the warp

    width, height = furniture_rgba.size
    if width < 4 or height < 4:
        return furniture_rgba

    try:
        arr = np.array(furniture_rgba)

        # Source corners: TL, TR, BL, BR.
        src = np.float32([
            [0, 0],
            [width, 0],
            [0, height],
            [width, height],
        ])
        # Destination: shift top corners horizontally by skew_px.
        dst = np.float32([
            [skew_px, 0],
            [width + skew_px, 0],
            [0, height],
            [width, height],
        ])

        matrix = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(
            arr, matrix, (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )
        return Image.fromarray(warped, "RGBA")
    except Exception:
        logger.warning("perspective_skew_failed_returning_original")
        return furniture_rgba
