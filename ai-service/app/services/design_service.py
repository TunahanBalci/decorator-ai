from uuid import UUID

from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import JOB_STATUS_COMPLETED
from app.db.models.design_job import DesignJob
from app.db.repositories.design_job_repository import DesignJobRepository
from app.schemas.design_job import (
    ClickableRegion,
    CreateDesignJobRequest,
    DesignJobOut,
    DesignOut,
    ProductCard,
)
from app.utils.store_names import normalize_store_name_from_url


class DesignService:
    def __init__(self, db: Session, queue: Any | None = None):
        self.db = db
        self.repo = DesignJobRepository(db)
        self.queue = queue

    def create_job(self, request: CreateDesignJobRequest) -> DesignJob:
        job = self.repo.create(
            room_image_path=request.room_image_path,
            room_dimensions=request.room_dimensions.model_dump(),
            preferences=request.preferences.model_dump(),
            requested_design_count=request.requested_design_count,
        )
        if self.queue is None:
            from app.workers.rq_worker import get_queue

            queue = get_queue()
        else:
            queue = self.queue
        from app.workers.jobs import run_design_job

        queue.enqueue(run_design_job, str(job.id), job_timeout="30m")
        return job

    def get_job(self, job_id: UUID) -> DesignJobOut | None:
        job = self.repo.get_with_results(job_id)
        if not job:
            return None
        progress = None if job.status == JOB_STATUS_COMPLETED else job.workflow_state
        return DesignJobOut(
            job_id=job.id,
            status=job.status,
            progress=progress,
            error_message=job.error_message,
            designs=[self._design_out(design) for design in job.designs],
        )

    def _design_out(self, design) -> DesignOut:
        regions = []
        products = []
        first_selected = None
        first_image_path = None
        for selected in design.selected_products:
            if first_selected is None:
                first_selected = selected
            product = selected.product
            primary = next(
                (img for img in product.images if img.is_primary),
                product.images[0] if product.images else None,
            )
            if first_image_path is None and primary:
                first_image_path = primary.relative_path
            store_name = normalize_store_name_from_url(product.source_url)
            if selected.polygon:
                regions.append(
                    ClickableRegion(
                        region_id=selected.id,
                        polygon=selected.polygon,
                        product_id=product.id,
                    )
                )
            products.append(
                ProductCard(
                    product_id=product.id,
                    external_id=product.external_id,
                    name=product.name,
                    category=product.category,
                    brand=store_name,
                    store_name=store_name,
                    role=selected.role,
                    source_url=product.source_url,
                    image_path=primary.relative_path if primary else None,
                    image_url=primary.relative_path if primary else None,
                    price={
                        "amount": float(product.price_amount),
                        "currency": product.price_currency,
                    }
                    if product.price_amount is not None
                    else None,
                    reason=selected.reason,
                    score=float(selected.score) if selected.score is not None else None,
                )
            )
        placement_debug = (
            (design.placement_plan or {}).get("debug") if design.placement_plan else None
        )
        render_meta = (
            (design.placement_plan or {}).get("render") if design.placement_plan else None
        ) or {}
        debug_artifacts = render_meta.get("debug_artifacts") or {}
        debug_mask_url = None
        if placement_debug:
            debug_mask_url = next(
                (
                    value
                    for key, value in debug_artifacts.items()
                    if key.startswith("mask_") and isinstance(value, str)
                ),
                None,
            )
        image_payload = None
        if design.generated_image_path:
            image_payload = {
                "path": design.generated_image_path,
                "original_image_url": design.design_job.input_room_image_path,
                "final_rendered_image_url": design.generated_image_path,
                "render_method": render_meta.get("renderer"),
                "width": placement_debug.get("image_width") if placement_debug else None,
                "height": placement_debug.get("image_height") if placement_debug else None,
                **({"debug_mask_url": debug_mask_url} if debug_mask_url else {}),
            }
        placement_coordinate = (
            _placement_coordinate(first_selected.polygon) if first_selected else None
        )
        return DesignOut(
            design_id=design.id,
            title=design.title,
            style=design.style,
            summary=design.summary,
            image=image_payload,
            original_image_url=design.design_job.input_room_image_path,
            final_rendered_image_url=design.generated_image_path,
            render_method=render_meta.get("renderer"),
            selected_product_id=first_selected.product_id if first_selected else None,
            selected_product_image_url=first_image_path,
            placement_coordinate=placement_coordinate,
            debug_mask_url=debug_mask_url,
            placement_debug=placement_debug,
            clickable_regions=regions,
            products=products,
        )


def _placement_coordinate(polygon: list | dict | None) -> dict | None:
    if not polygon or not isinstance(polygon, list):
        return None
    xs = [point[0] for point in polygon if isinstance(point, list) and len(point) >= 2]
    ys = [point[1] for point in polygon if isinstance(point, list) and len(point) >= 2]
    if not xs or not ys:
        return None
    return {"x": (min(xs) + max(xs)) / 2, "y": max(ys)}
