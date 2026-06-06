from openai import AsyncOpenAI
from app.core.config import settings

def get_llm_client():
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
