import json
import logging
from typing import AsyncGenerator

from app.vectorstore.qdrant import get_vector_store
from app.services.llm import get_llm_client
from app.core.prompts import SYSTEM_PROMPT
from app.models.chat import Source

logger = logging.getLogger(__name__)

async def stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    vector_store = get_vector_store()
    
    # Retrieve with score, top_k = 4
    results = vector_store.similarity_search_with_score(query=message, k=4)
    
    # Threshold filtering to avoid hallucinations
    # Depending on the embedding model, cosine similarity threshold might need tuning.
    # 0.25 is a safe starting point.
    threshold = 0.25
    filtered_results = [res for res, score in results if score > threshold]
    
    context_parts = []
    sources = []
    
    for doc in filtered_results:
        page_content = doc.page_content
        page_number = doc.metadata.get('page_label', doc.metadata.get('page', '0'))
        source_name = doc.metadata.get('source', 'Unknown Document')
        
        context_parts.append(f"Document: {source_name}\nPage Number: {page_number}\nContent:\n{page_content}")
        
        # Add to sources list if not already there to avoid duplicates
        try:
            page_int = int(page_number)
        except ValueError:
            page_int = 0
            
        source_obj = {"document": str(source_name).split('/')[-1].split('\\')[-1], "page": page_int}
        if source_obj not in sources:
            sources.append(source_obj)
            
    context = "\n\n---\n\n".join(context_parts)
    prompt = SYSTEM_PROMPT.format(context=context)
    
    llm = get_llm_client()
    
    # Send sources first so the frontend can display them immediately
    yield f"data: {json.dumps({'content': '', 'sources': sources})}\n\n"
    
    try:
        response_stream = await llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            stream=True
        )
        
        async for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'content': content, 'sources': []})}\n\n"
                
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        yield f"data: {json.dumps({'content': '\n\n**Error:** The AI service is currently unavailable. Please try again later.', 'sources': []})}\n\n"
