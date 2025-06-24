import json
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from config import QDRANT_URL, QDRANT_COLLECTION_NAME
from utils.embeddings import get_embedding

client = QdrantClient(url=QDRANT_URL)

def create_kb():
    """
    Create knowledge base from the updated math_dataset.json with enhanced error handling
    """
    print("Loading math dataset...")
    try:
        with open("data/math_dataset.json") as f:
            data = json.load(f)
        print(f"Loaded {len(data)} questions from dataset")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return False

    # Recreate collection with proper configuration
    try:
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Created collection: {QDRANT_COLLECTION_NAME}")
    except Exception as e:
        print(f"Error creating collection: {e}")
        return False

    # Process data and create points
    points = []
    failed_items = 0
    
    for i, q in enumerate(data):
        try:
            # Generate embedding for the question
            embedding = get_embedding(q['question'])
            
            # Use the original ID from data, convert to integer hash if it's a string
            point_id = q.get("id")
            if isinstance(point_id, str):
                # Convert string ID to integer using hash
                point_id = abs(hash(point_id)) % (10**9)
            else:
                point_id = i
            
            # Create point with all available data
            point = PointStruct(
                id=point_id, 
                vector=embedding, 
                payload={
                    "question": q['question'],
                    "answer": q['answer'],
                    "level": q.get('level', ''),
                    "type": q.get('type', ''),
                    "category": q.get('category', ''),
                    "difficulty": q.get('difficulty', 1),
                    "original_id": q.get('id', '')
                }
            )
            points.append(point)
            
            # Progress indicator for large datasets
            if (i + 1) % 1000 == 0:
                print(f"Processed {i + 1}/{len(data)} questions")
                
        except Exception as e:
            print(f"Error processing question {i}: {e}")
            failed_items += 1
            continue

    if failed_items > 0:
        print(f"Warning: Failed to process {failed_items} items")

    # Upsert points in batches for better performance
    print(f"Upserting {len(points)} points to Qdrant...")
    try:
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=batch)
            
            if (i + batch_size) % 1000 == 0:
                print(f"Upserted {min(i + batch_size, len(points))}/{len(points)} points")
        
        print("Knowledge base creation completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error upserting points: {e}")
        return False

def retrieve_from_kb(query: str, top_k=3, similarity_threshold=0.75):
    """
    Enhanced retrieval function with multiple results and metadata
    """
    try:
        embedding = get_embedding(query)
        hits = client.search(
            collection_name=QDRANT_COLLECTION_NAME, 
            query_vector=embedding, 
            limit=top_k
        )
        
        if hits and hits[0].score > similarity_threshold:
            # Return the best match with additional metadata
            best_match = hits[0].payload
            best_match['confidence'] = hits[0].score
            return best_match
        
        # If no high-confidence match, return None
        return None
        
    except Exception as e:
        print(f"Error retrieving from knowledge base: {e}")
        return None

def retrieve_multiple_from_kb(query: str, top_k=5, similarity_threshold=0.6):
    """
    Retrieve multiple similar questions for reference
    """
    try:
        embedding = get_embedding(query)
        hits = client.search(
            collection_name=QDRANT_COLLECTION_NAME, 
            query_vector=embedding, 
            limit=top_k
        )
        
        results = []
        for hit in hits:
            if hit.score > similarity_threshold:
                result = hit.payload.copy()
                result['confidence'] = hit.score
                results.append(result)
        
        return results
        
    except Exception as e:
        print(f"Error retrieving multiple results: {e}")
        return []

def get_kb_stats():
    """
    Get statistics about the knowledge base
    """
    try:
        collection_info = client.get_collection(QDRANT_COLLECTION_NAME)
        return {
            "total_points": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance_metric": collection_info.config.params.vectors.distance
        }
    except Exception as e:
        print(f"Error getting KB stats: {e}")
        return None
    


# Add to knowledge_base.py
def update_knowledge_base_item(question: str, answer: str, metadata: dict = None):
    """
    Update or add an item to the knowledge base based on feedback
    """
    try:
        embedding = get_embedding(question)
        
        # Check if question already exists
        existing = retrieve_from_kb(question)
        
        if existing:
            # Update existing item
            point_id = existing.get('original_id') or abs(hash(question)) % (10**9)
            payload = existing.copy()
            payload['answer'] = answer
            if metadata:
                payload.update(metadata)
            
            client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )]
            )
            return True, "Updated existing KB item"
        else:
            # Add new item
            point_id = abs(hash(question)) % (10**9)
            payload = {
                "question": question,
                "answer": answer,
                "level": metadata.get('level', 'unknown'),
                "type": metadata.get('type', 'unknown'),
                "category": metadata.get('category', 'feedback'),
                "difficulty": metadata.get('difficulty', 2),
                "source": "user_feedback"
            }
            
            client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )]
            )
            return True, "Added new KB item from feedback"
            
    except Exception as e:
        return False, f"Error updating KB: {str(e)}"