from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import QDRANT_URL, QDRANT_COLLECTION_NAME
from utils.embeddings import get_embedding

client = QdrantClient(url=QDRANT_URL)

def retrieve_answer(query, top_k=3, min_score=0.7):
    """
    Retrieve answer from knowledge base with improved filtering
    """
    query_embedding = get_embedding(query)
    search_results = client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k
    )
    
    if search_results and search_results[0].score >= min_score:
        # Return the best match
        best_match = search_results[0].payload
        return {
            "answer": best_match['answer'],
            "question": best_match['question'],
            "level": best_match.get('level', ''),
            "type": best_match.get('type', ''),
            "category": best_match.get('category', ''),
            "difficulty": best_match.get('difficulty', 1),
            "confidence": search_results[0].score
        }
    else:
        return None

def retrieve_similar_questions(query, top_k=5):
    """
    Retrieve multiple similar questions for reference
    """
    query_embedding = get_embedding(query)
    search_results = client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k
    )
    
    results = []
    for result in search_results:
        if result.score >= 0.6:  # Lower threshold for similar questions
            results.append({
                "question": result.payload['question'],
                "answer": result.payload['answer'],
                "level": result.payload.get('level', ''),
                "type": result.payload.get('type', ''),
                "category": result.payload.get('category', ''),
                "score": result.score
            })
    
    return results