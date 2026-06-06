from langchain_openai import OpenAIEmbeddings
from app.core.config import settings

def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=settings.OPENAI_API_KEY
    )
