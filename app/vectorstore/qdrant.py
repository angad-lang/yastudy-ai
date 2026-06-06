from langchain_qdrant import QdrantVectorStore
from app.core.config import settings
from app.services.embeddings import get_embeddings

def get_vector_store() -> QdrantVectorStore:
    embeddings = get_embeddings()
    return QdrantVectorStore.from_existing_collection(
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION,
        embedding=embeddings,
    )
