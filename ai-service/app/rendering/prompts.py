"""Dynamic inpainting prompt generation.

Builds positive and negative prompts for SDXL-style inpainting models.
Prompts are assembled from furniture metadata (category, color, style) and
room context (room type, detected style).  This module is used by the mock
renderer today for debug output and will drive real SDXL generation later.
"""

from __future__ import annotations


def build_inpainting_prompt(
    category: str,
    color: str | None = None,
    style: str | None = None,
    room_type: str | None = None,
    extra_context: str | None = None,
) -> tuple[str, str]:
    """Generate a positive and negative prompt for furniture inpainting.

    Args:
        category: Furniture type (e.g. ``"sofa"``, ``"floor_lamp"``).
        color: Primary color of the furniture (e.g. ``"gray"``).
        style: Design style (e.g. ``"modern"``, ``"scandinavian"``).
        room_type: Room type from analysis (e.g. ``"living_room"``).
        extra_context: Optional additional context for the prompt.

    Returns:
        A ``(positive_prompt, negative_prompt)`` tuple.

    Examples:
        >>> pos, neg = build_inpainting_prompt("sofa", "gray", "modern", "living_room")
        >>> "sofa" in pos
        True
        >>> "floating" in neg
        True
    """
    # --- Build positive prompt ---
    furniture_desc = _humanize_category(category)
    parts = []

    if color and style:
        parts.append(f"a {color} {style} {furniture_desc}")
    elif color:
        parts.append(f"a {color} {furniture_desc}")
    elif style:
        parts.append(f"a {style} {furniture_desc}")
    else:
        parts.append(f"a {furniture_desc}")

    room_desc = _humanize_room_type(room_type) if room_type else "this room"
    parts.append(f"placed naturally in {room_desc}")

    # Realism instructions for the inpainting model.
    parts.append(
        "Maintain realistic lighting, natural shadows, correct floor perspective, "
        "and preserve the room structure. The furniture should look like it belongs "
        "in the scene."
    )

    if extra_context:
        parts.append(extra_context)

    positive = ". ".join(parts) + "."

    # --- Build negative prompt ---
    negative_terms = [
        "floating furniture",
        "distorted geometry",
        "extra furniture",
        "duplicate objects",
        "blurry",
        "low quality",
        "warped room",
        "unrealistic",
        "cartoon",
        "painting",
        "sketch",
        "deformed",
        "bad proportions",
        "cropped furniture",
    ]
    negative = ", ".join(negative_terms)

    return positive, negative


def build_multi_furniture_prompt(
    products: list[dict],
    room_type: str | None = None,
    room_style: str | None = None,
) -> tuple[str, str]:
    """Generate a prompt covering multiple furniture items.

    Useful for batch inpainting or scene-level generation.

    Args:
        products: List of product dicts with ``role``, ``color``, ``style`` keys.
        room_type: Room type from analysis.
        room_style: Overall room style from analysis.

    Returns:
        ``(positive_prompt, negative_prompt)`` tuple.
    """
    if not products:
        return build_inpainting_prompt("furniture", room_type=room_type, style=room_style)

    descriptions = []
    for product in products:
        role = product.get("role", "furniture")
        category = _humanize_category(role)
        color = _extract_color(product)
        if color:
            descriptions.append(f"a {color} {category}")
        else:
            descriptions.append(f"a {category}")

    furniture_list = ", ".join(descriptions)
    style_prefix = f"{room_style} " if room_style else ""
    room_desc = _humanize_room_type(room_type) if room_type else "this room"

    positive = (
        f"Place {furniture_list} naturally in {room_desc}. "
        f"{style_prefix}interior design. "
        f"Maintain realistic lighting, natural shadows, correct floor perspective, "
        f"and preserve the room structure."
    )

    negative = (
        "floating furniture, distorted geometry, extra furniture, duplicate objects, "
        "blurry, low quality, warped room, unrealistic, cartoon, deformed"
    )

    return positive, negative


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _humanize_category(category: str) -> str:
    """Convert a snake_case role/category into human-readable text."""
    replacements = {
        "coffee_table": "coffee table",
        "side_table": "side table",
        "dining_table": "dining table",
        "console_table": "console table",
        "tv_unit": "TV unit",
        "floor_lamp": "floor lamp",
        "pendant_lamp": "pendant lamp",
        "plant_pot": "plant pot",
        "wall_art": "wall art",
        "storage_unit": "storage unit",
        "office_chair": "office chair",
        "dining_chair": "dining chair",
    }
    return replacements.get(category, category.replace("_", " "))


def _humanize_room_type(room_type: str) -> str:
    """Convert a snake_case room_type into human-readable text."""
    return room_type.replace("_", " ") if room_type else "this room"


def _extract_color(product: dict) -> str | None:
    """Try to extract a representative color from a product dict."""
    # Product metadata may carry colors from the enrichment pipeline.
    metadata = product.get("metadata", {})
    colors = metadata.get("colors") or product.get("colors") or []
    if isinstance(colors, list) and colors:
        return colors[0]
    return None
