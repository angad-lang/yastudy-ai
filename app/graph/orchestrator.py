from langgraph.graph import StateGraph, START, END
from app.graph.state import AgentState
from app.graph.nodes import retrieve_context, generate_response
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from app.core.config import settings
from langchain_core.messages import HumanMessage
import json

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_response", generate_response)
    
    workflow.add_edge(START, "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow

# Create a singleton MongoDB client
mongo_client = MongoClient(settings.MONGODB_URI)
checkpointer = MongoDBSaver(mongo_client)

graph = build_graph().compile(checkpointer=checkpointer)

async def stream_chat_response(message: str, session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    input_message = HumanMessage(content=message)
    
    async for event in graph.astream_events({"messages": [input_message]}, config=config, version="v2"):
        if event["event"] == "on_chain_end" and event["name"] == "retrieve_context":
            # Extract the sources returned by retrieve_context
            sources = event["data"]["output"].get("sources", [])
            yield f"data: {json.dumps({'content': '', 'sources': sources})}\n\n"
        elif event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if isinstance(chunk, str) and chunk:
                yield f"data: {json.dumps({'content': chunk})}\n\n"
    
    yield "data: [DONE]\n\n"
