from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from config import QDRANT_COLLECTION_NAME, QDRANT_URL
import json
import hashlib
import os

# Use QDRANT_URL from config if available, otherwise default to localhost
try:
    client = QdrantClient(url=QDRANT_URL)
except:
    client = QdrantClient("localhost", port=6333)

model = SentenceTransformer("all-MiniLM-L6-v2")
collection_name = QDRANT_COLLECTION_NAME

# Recreate collection
if client.collection_exists(collection_name=collection_name):
    client.delete_collection(collection_name=collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# === Load dataset (full or sample fallback) ===
dataset_path = "data/math_dataset.json"
sample_path = "data/sample_math_dataset.json"

if os.path.exists(dataset_path):
    print(f"Loading full dataset from {dataset_path}...")
    with open(dataset_path) as f:
        data = json.load(f)
elif os.path.exists(sample_path):
    print(f"Full dataset not found. Loading sample dataset from {sample_path}...")
    with open(sample_path) as f:
        data = json.load(f)
else:
    raise FileNotFoundError("Neither math_dataset.json nor sample_math_dataset.json found in data/ folder.")

print(f"Processing {len(data)} questions...")

# Convert to PointStruct list
points = []
for idx, item in enumerate(data):
    try:
        embedding = model.encode(item["question"]).tolist()

        point_id = item.get("id")
        if isinstance(point_id, str):
            point_id = abs(hash(point_id)) % (10**9)
        else:
            point_id = idx

        points.append(PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "question": item["question"],
                "answer": item["answer"],
                "level": item.get("level", ""),
                "type": item.get("type", ""),
                "category": item.get("category", ""),
                "difficulty": item.get("difficulty", 1),
                "original_id": item.get("id", "")
            }
        ))

        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1}/{len(data)} questions")

    except Exception as e:
        print(f"Error processing item {idx}: {e}")
        continue

print(f"Upserting {len(points)} points to Qdrant...")

# Upsert in batches
batch_size = 100
for i in range(0, len(points), batch_size):
    batch = points[i:i + batch_size]
    client.upsert(collection_name=collection_name, points=batch)
    if (i + batch_size) % 1000 == 0:
        print(f"Upserted {min(i + batch_size, len(points))}/{len(points)} points")

print("Knowledge base population completed!")
