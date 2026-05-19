from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(":memory:")
client.create_collection("test", vectors_config={"text": models.VectorParams(size=2, distance=models.Distance.COSINE)})
client.upload_points("test", [models.PointStruct(id=1, payload={"product_db_id": "foo"}, vector={"text": [0.5, 0.5]})])

res = client.query_points(
    collection_name="test",
    query=[0.5, 0.5],
    using="text",
    limit=10,
).points
print([hit.payload for hit in res])
