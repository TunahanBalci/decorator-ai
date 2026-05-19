from app.schemas.ai_outputs import ProductRetrievalIntent
from app.vector.product_search import build_filter_payload


def test_build_filter_payload() -> None:
    payload = build_filter_payload(
        ProductRetrievalIntent(
            role="coffee_table",
            category="coffee_table",
            styles=["scandinavian"],
            material=["wood"],
            colors=["oak"],
            query_text="oak coffee table",
        )
    )
    assert {"key": "category", "match": {"value": "coffee_table"}} in payload["must"]
    assert {"key": "styles", "match": {"any": ["scandinavian"]}} in payload["must"]


def test_build_filter_payload_dimensions() -> None:
    payload = build_filter_payload(
        ProductRetrievalIntent(
            role="sofa",
            category="sofa",
            styles=["modern"],
            material=["fabric"],
            colors=["gray"],
            query_text="modern sofa",
            min_width_cm=120.0,
            max_width_cm=328.0,
            min_depth_cm=60.0,
            max_depth_cm=252.0,
            min_height_cm=55.0,
            max_height_cm=256.5,
        )
    )
    assert {"key": "category", "match": {"value": "sofa"}} in payload["must"]
    assert {"key": "width_cm", "range": {"gte": 120.0, "lte": 328.0}} in payload["must"]
    assert {"key": "depth_cm", "range": {"gte": 60.0, "lte": 252.0}} in payload["must"]
    assert {"key": "height_cm", "range": {"gte": 55.0, "lte": 256.5}} in payload["must"]


