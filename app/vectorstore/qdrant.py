from langchain_qdrant import QdrantVectorStore
from app.core.config import settings
from app.services.embeddings import get_embeddings

def get_vector_store() -> QdrantVectorStore:
    embeddings = get_embeddings()
    return QdrantVectorStore.from_existing_collection(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
        embedding=embeddings,
    )
