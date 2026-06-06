from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: str

class Source(BaseModel):
    document: str
    page: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
