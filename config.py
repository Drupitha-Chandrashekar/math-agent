# config.py

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve values
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
HF_EMBEDDING_MODEL=os.getenv("HF_EMBEDDING_MODEL")
HF_TOKEN=os.getenv("HF_TOEKN")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
SERPER_API_KEY=os.getenv("SERPER_API_KEY")
FEEDBACK_DB_PATH=os.getenv("FEEDBACK_DB_PATH")
