from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest
from app.graph.orchestrator import stream_chat_response

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        stream_chat_response(request.message, request.session_id),
        media_type="text/event-stream"
    )
