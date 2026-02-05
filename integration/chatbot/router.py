from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, constr

from chatbot.agent_graph import invoke_agent
from chatbot.memory import memory_store
from utils.logging import get_logger

router = APIRouter(tags=["Chatbot"])
logger = get_logger(__name__)

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query")
    session_id: str = Field(..., description="Unique ID for the conversation session")


class ChatResponse(BaseModel):
    answer: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Stateful Chatbot endpoint using Redis for persistence.
    Pass a 'session_id' to maintain context across requests.
    """
    try:
        # 1. Retrieve History from Redis
        try:
            # Smart Memory: Retrieve only the last 10 interactions to manage token costs
            stored_history = memory_store.get_history(request.session_id, limit=10)
        except Exception as e:
            logger.error(f"Redis Read Error: {e}")
            # Fail open: Continue with empty history rather than crashing
            stored_history = []
        
        # 2. Invoke Agent with Context
        answer = invoke_agent(request.query, stored_history)
        
        # 3. Save new interaction to Redis
        try:
            memory_store.add_message(request.session_id, "user", request.query)
            memory_store.add_message(request.session_id, "assistant", answer)
        except Exception as e:
            logger.error(f"Redis Write Error: {e}")
            # Non-blocking error: We still return the answer to the user
        
        return {
            "answer": answer,
            "session_id": request.session_id
        }
    except ValueError as ve:
        # Context window exceeded or validation error
        logger.warning(f"Validation Error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Critical Agent Error: {e}")
        raise HTTPException(status_code=500, detail="Internal AI Service Error. Please try again later.")
