from sentence_transformers import SentenceTransformer
from config import HF_EMBEDDING_MODEL

model = SentenceTransformer(HF_EMBEDDING_MODEL)

def get_embedding(text):
    return model.encode(text).tolist()
