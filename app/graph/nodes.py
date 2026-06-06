from app.graph.state import AgentState
from app.vectorstore.qdrant import get_vector_store
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from app.core.prompts import SYSTEM_PROMPT
from app.core.config import settings
import os

async def retrieve_context(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1].content
    
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(query=last_message, k=4)
    
    threshold = 0.25
    filtered_results = [res for res, score in results if score > threshold]
    
    context_parts = []
    sources = []
    
    for res in filtered_results:
        page_content = res.page_content
        metadata = res.metadata
        page_num = metadata.get("page_label", "Unknown")
        source_doc = metadata.get("source", "Unknown").split("/")[-1].split("\\")[-1]
        
        context_parts.append(
            f"Document: {source_doc}\nPage: {page_num}\nContent: {page_content}"
        )
        sources.append({
            "document": source_doc,
            "page": int(page_num) if str(page_num).isdigit() else page_num
        })
        
    context_str = "\n\n---\n\n".join(context_parts)
    return {"context": context_str, "sources": sources}

async def generate_response(state: AgentState):
    messages = state["messages"]
    context_str = state.get("context", "")
    
    sys_msg = SystemMessage(content=SYSTEM_PROMPT.format(context=context_str))
    messages_to_pass = [sys_msg] + messages
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=settings.OPENAI_API_KEY)
    response = await llm.ainvoke(messages_to_pass)
    
    return {"messages": [response]}
