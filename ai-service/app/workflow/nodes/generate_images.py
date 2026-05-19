import structlog
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.rendering.factory import get_renderer
from app.storage.local_storage import LocalImageStorage
from app.utils.placement import image_size, normalized_to_pixel_polygon
from app.workflow.nodes.helpers import progress
from app.workflow.state import DesignWorkflowState

logger = structlog.get_logger(__name__)


def generate_images_node(db: Session):
    def node(state: DesignWorkflowState) -> DesignWorkflowState:
        progress(db, state, "generate_images")
        settings = get_settings()
        storage = LocalImageStorage(settings)
        room_image_path = state.get("room_image_path", "")
        selected = state.get("selected_products", [])
        if not room_image_path or not selected:
            return {"generated_images": []}

        # Sprint 3: resolve renderer from configuration.
        renderer = get_renderer(settings.render_method)
        logger.info(
            "renderer_selected",
            render_method=settings.render_method,
            renderer_name=renderer.name,
        )

        generated_images = []
        image_width, image_height = image_size(storage.resolve_room_image(room_image_path))
        for strategy in state.get("design_strategies", []):
            design_index = int(strategy["design_index"])
            products = [
                product
                for product in selected
                if int(product.get("design_index", -1)) == design_index and product.get("polygon")
            ]
            if not products:
                continue

            output_relative_path = (
                f"generated/{state['job_id']}/design_{design_index}_composite.png"
            )

            # Sprint 3: delegate to the configured renderer.
            result = renderer.render(
                storage=storage,
                room_image_path=room_image_path,
                products=products,
                output_relative_path=output_relative_path,
            )

            generated_images.append(
                {
                    "design_index": design_index,
                    "path": result.relative_path,
                    "width": image_width,
                    "height": image_height,
                    "renderer": result.render_method,
                    "render_settings": {
                        "render_method": settings.render_method,
                        "perspective_min_scale": settings.perspective_min_scale,
                        "perspective_max_scale": settings.perspective_max_scale,
                        "default_furniture_width": settings.default_furniture_width,
                        "shadow_opacity": settings.shadow_opacity,
                        "shadow_blur_radius": settings.shadow_blur_radius,
                        "shadow_y_offset": settings.shadow_y_offset,
                        "skew_enabled": settings.enable_perspective_skew,
                        "mask_dilation_px": settings.mask_dilation_px,
                    },
                    "debug_artifacts": result.debug_artifacts if settings.debug_placement else {},
                }
            )

            for product in products:
                pixel_polygon = normalized_to_pixel_polygon(
                    product["polygon"],
                    image_width,
                    image_height,
                )
                logger.info(
                    "placement_rendered",
                    job_id=state.get("job_id"),
                    design_index=design_index,
                    selected_furniture_id=str(product.get("product_id")),
                    selected_furniture_image_path=product.get("image_path"),
                    normalized_polygon=product.get("polygon"),
                    pixel_polygon=pixel_polygon,
                    original_image_size={"width": image_width, "height": image_height},
                    final_output_image_path=result.relative_path,
                )
            logger.info(
                "composite_written",
                job_id=state.get("job_id"),
                design_index=design_index,
                output_path=str(result.output_path),
                render_method=result.render_method,
            )

            # Sprint 2: generate debug composite when DEBUG_PLACEMENT is enabled.
            if settings.debug_placement:
                _write_debug_composite(
                    storage=storage,
                    room_image_path=room_image_path,
                    products=products,
                    job_id=state["job_id"],
                    design_index=design_index,
                    image_width=image_width,
                    image_height=image_height,
                    settings=settings,
                )

        return {"generated_images": generated_images}

    return node


def _write_debug_composite(
    *,
    storage: LocalImageStorage,
    room_image_path: str,
    products: list[dict],
    job_id: str,
    design_index: int,
    image_width: int,
    image_height: int,
    settings,
) -> None:
    """Generate a debug image annotating placement points, bounding boxes, and scales.

    Written to ``generated/debug/{job_id}_design_{design_index}_composite_debug.png``.
    """
    from PIL import ImageDraw, ImageFont
    from app.utils.perspective import compute_perspective_scale

    debug_path_relative = (
        f"generated/debug/{job_id}_design_{design_index}_composite_debug.png"
    )
    debug_path = storage.resolve_generated_image(debug_path_relative)
    room_path = storage.resolve_room_image(room_image_path)

    try:
        canvas = Image.open(room_path).convert("RGBA")
    except Exception:
        canvas = Image.new("RGBA", (image_width, image_height), (245, 241, 234, 255))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for product in products:
        polygon = product.get("polygon") or []
        if not polygon:
            continue

        norm_xs = [pt[0] for pt in polygon]
        norm_ys = [pt[1] for pt in polygon]
        center_x = (min(norm_xs) + max(norm_xs)) / 2.0
        floor_y = max(norm_ys)

        px_x = center_x * image_width
        px_y = floor_y * image_height

        # Placement point (green dot).
        r = 8
        draw.ellipse(
            (px_x - r, px_y - r, px_x + r, px_y + r),
            fill=(20, 200, 80, 255),
        )

        # Furniture bounding box (yellow outline).
        pixel_polygon = normalized_to_pixel_polygon(polygon, image_width, image_height)
        pts = [(pt[0], pt[1]) for pt in pixel_polygon]
        if len(pts) >= 3:
            draw.polygon(pts, outline=(255, 220, 40, 255), width=3)

        # Scale value label.
        scale = compute_perspective_scale(
            floor_y,
            min_scale=settings.perspective_min_scale,
            max_scale=settings.perspective_max_scale,
        )
        role = product.get("role") or "item"
        label = f"{role} s={scale:.2f}"
        try:
            font = ImageFont.load_default()
        except Exception:
            font = ImageFont.ImageFont()
        draw.text((px_x + 12, px_y - 16), label, fill=(255, 255, 255, 255), font=font)

    debug_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(canvas, overlay).convert("RGB").save(debug_path)
    logger.info(
        "debug_composite_written",
        job_id=job_id,
        design_index=design_index,
        debug_path=str(debug_path),
    )
