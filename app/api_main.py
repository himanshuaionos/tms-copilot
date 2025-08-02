# app/api_main.py
import re
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sys
from pinecone import Pinecone, ServerlessSpec
import uvicorn
from fastapi.responses import StreamingResponse
import json
from db import Feedback, init_db, get_db, create_conversation, add_message, add_source, add_feedback, Conversation, Message, Source
from sqlalchemy import and_
from sqlalchemy.orm import Session, aliased
from starlette.responses import StreamingResponse as StarletteStreamingResponse

# Add the parent directory to the path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.config import config
from core.embeddings import EmbeddingManager
from core.vector_store import VectorStore
from core.llm import LLMManager

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="A REST API for TMS Cytric RAG Chatbot",
    version="1.0.0"
)

# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []
    context_window: Optional[int] = 5
    max_history: Optional[int] = 10
    include_sources: Optional[bool] = False
    conversation_id: Optional[int] = None

class FeedbackRequest(BaseModel):
    user_id: int
    username: str
    user_full_name: str
    feedback_type: str
    conversation_id: int
    time_saved: str
    rating: int
    recommend: str
    liked_aspects: str
    other_liked: str
    improvement_suggestions: str
    issues: str
    other_feedback: str

class SourceDocument(BaseModel):
    text: str
    metadata: Dict

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[SourceDocument]] = []
    chat_history: List[ChatMessage]
    conversation_id: Optional[int] = None

class FeedbackResponse(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Global variables for components
embedding_manager = None
vector_store = None
llm_manager = None

def check_environment():
    """Check if all required environment variables are set."""
    missing_vars = []
    
    if not config.OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    if not config.PINECONE_API_KEY:
        missing_vars.append("PINECONE_API_KEY")
    if not config.PINECONE_ENVIRONMENT:
        missing_vars.append("PINECONE_ENVIRONMENT")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        raise ValueError(error_msg)

def initialize_components():
    """Initialize all components needed for the RAG system."""
    try:
        # Check environment variables first
        check_environment()
        
        # Initialize Pinecone
        pc = Pinecone(
            api_key=config.PINECONE_API_KEY,
            environment=config.PINECONE_ENVIRONMENT
        )
        
        # Verify Pinecone index exists and is accessible
        index = pc.Index(config.PINECONE_INDEX_NAME)
        
        # Initialize components
        embedding_manager = EmbeddingManager()
        vector_store = VectorStore()
        llm_manager = LLMManager()
        
        return embedding_manager, vector_store, llm_manager
        
    except Exception as e:
        raise Exception(f"Initialization Error: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global embedding_manager, vector_store, llm_manager
    try:
        init_db()
        embedding_manager, vector_store, llm_manager = initialize_components()
        print("✅ All components initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize components: {str(e)}")
        raise e

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify API is running."""
    if embedding_manager is None or vector_store is None or llm_manager is None:
        raise HTTPException(status_code=503, detail="Service components not initialized")
    
    return HealthResponse(
        status="healthy",
        message="RAG Chatbot API is running successfully"
    )

# Main chat endpoint (non-streaming, legacy)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for processing user queries."""
    global embedding_manager, vector_store, llm_manager
    
    # Check if components are initialized
    if embedding_manager is None or vector_store is None or llm_manager is None:
        raise HTTPException(status_code=503, detail="Service components not initialized")
    
    try:
        db = next(get_db())
        # Create or get conversation
        if request.conversation_id:
            conversation_id = request.conversation_id
        else:
            conv = create_conversation(db)
            conversation_id = conv.id
        # Store user message
        user_msg = add_message(db, conversation_id, "user", request.message)
        
        # Generate embedding for the user query
        query_embedding = embedding_manager.generate_embeddings([request.message])[0]
        
        # Search for relevant documents
        relevant_docs = vector_store.search(
            request.message,
            query_embedding,
            k=request.context_window
        )
        
        # Convert chat history to the format expected by LLM manager
        chat_history = []
        for msg in request.chat_history:
            chat_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Limit chat history
        if len(chat_history) > request.max_history:
            chat_history = chat_history[-request.max_history:]
        
        # Generate response using LLM manager
        response = llm_manager.generate_response(
            request.message,
            relevant_docs,
            chat_history
        )
        
        # Store assistant message
        assistant_msg = add_message(db, conversation_id, "assistant", response)
        
        # Prepare sources if requested
        sources = []
        if request.include_sources:
            for doc in relevant_docs:
                sources.append(SourceDocument(
                    text=doc["text"],
                    metadata=doc.get("metadata", {})
                ))
                # Store source in DB
                add_source(db, assistant_msg.id, doc["text"], doc.get("metadata", {}))
        
        # Update chat history with the new exchange
        updated_chat_history = chat_history + [
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=response)
        ]
        
        return ChatResponse(
            response=response,
            sources=sources if request.include_sources else [],
            chat_history=updated_chat_history,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

# Streaming chat endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for processing user queries."""
    global embedding_manager, vector_store, llm_manager
    if embedding_manager is None or vector_store is None or llm_manager is None:
        raise HTTPException(status_code=503, detail="Service components not initialized")

    try:
        db = next(get_db())
        # Create or get conversation
        if request.conversation_id:
            conversation_id = request.conversation_id
        else:
            conv = create_conversation(db)
            conversation_id = conv.id
        # Store user message
        user_msg = add_message(db, conversation_id, "user", request.message)
        query_embedding = embedding_manager.generate_embeddings([request.message])[0]
        relevant_docs = vector_store.search(
            request.message,
            query_embedding,
            k=request.context_window
        )
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history
        ]
        if len(chat_history) > request.max_history:
            chat_history = chat_history[-request.max_history:]

        def token_stream():
            response_accum = ""
            for token in llm_manager.stream_response(
                request.message,
                relevant_docs,
                chat_history
            ):
                response_accum += token
                yield token
            # Store assistant message and sources after streaming is done
            assistant_msg = add_message(db, conversation_id, "assistant", response_accum)
            for doc in relevant_docs:
                add_source(db, assistant_msg.id, doc["text"], doc.get("metadata", {}))
        
        # Set conversation_id in response header so frontend can persist it
        headers = {"conversation_id": str(conversation_id)}
        return StarletteStreamingResponse(token_stream(), media_type="text/plain", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


# Endpoint to save feedback
@app.post("/chat/feedback", response_model=FeedbackResponse)
async def save_feedback(request: FeedbackRequest):
    """Save feedback to the database."""
    try:
        db = next(get_db())
        
        # Add feedback to the database
        add_feedback(
            db,
            request.user_id,
            request.username,
            request.user_full_name,
            request.feedback_type,
            request.conversation_id,
            request.time_saved,
            request.rating,
            request.recommend,
            request.liked_aspects,
            request.other_liked,
            request.improvement_suggestions,
            request.issues,
            request.other_feedback
        )
        
        return FeedbackResponse(
            message="Feedback saved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")


# Endpoint to retrieve the feedback
@app.get("/chat/feedback/list")
async def get_feedback():
    try:
        db = next(get_db())

        UserMessage = aliased(Message)
        AssistantMessage = aliased(Message)
        feedbacks_db = db.query(
            Feedback,
            UserMessage.content.label('query'),
            AssistantMessage.content.label('response')
        ).join(
            UserMessage,
            and_(
                Feedback.conversation_id == UserMessage.conversation_id,
                UserMessage.role == 'user'
            )
        ).join(
            AssistantMessage,
            and_(
                Feedback.conversation_id == AssistantMessage.conversation_id,
                AssistantMessage.role == 'assistant'
            )
        ).limit(1000).all()
        if not feedbacks_db:
            raise HTTPException(status_code=404, detail="No feedback found")

        feedbacks = list()

        for feedback_row in feedbacks_db:
            feedback_obj = feedback_row[0]
            query = feedback_row.query
            response = feedback_row.response

            feedback = {
                "user_id" : feedback_obj.user_id,
                "username" : feedback_obj.username,
                "user_full_name" : feedback_obj.user_full_name,
                "feedback_type" : feedback_obj.feedback_type,
                "query": query,
                "response": response,
                "time_saved" : feedback_obj.time_saved,
                "rating" : feedback_obj.rating,
                "recommend" : feedback_obj.recommend,
                "liked_aspects" : feedback_obj.liked_aspects,
                "other_liked" : feedback_obj.other_liked,
                "improvement_suggestions" : feedback_obj.improvement_suggestions,
                "issues" : feedback_obj.issues,
                "other_feedback" : feedback_obj.other_feedback,
                "timestamp": feedback_obj.timestamp
            }

            feedbacks.append(feedback)
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading feedback: {str(e)}")


# Endpoint to retrieve the response
@app.get("/chat/reponse/list")
async def get_response():
    try:
        db = next(get_db())

        UserMessage = aliased(Message)
        AssistantMessage = aliased(Message)
        feedbacks_db = db.query(
            Feedback.user_id,
            Feedback.username,
            Feedback.user_full_name,
            Feedback.timestamp,
            UserMessage.content.label('query'),
            AssistantMessage.content.label('response')
        ).join(
            UserMessage,
            and_(
                Feedback.conversation_id == UserMessage.conversation_id,
                UserMessage.role == 'user'
            )
        ).join(
            AssistantMessage,
            and_(
                Feedback.conversation_id == AssistantMessage.conversation_id,
                AssistantMessage.role == 'assistant'
            )
        ).limit(1000).all()
        if not feedbacks_db:
            raise HTTPException(status_code=404, detail="No response found")

        feedbacks = list()

        for feedback_row in feedbacks_db:
            feedback = {
                "user_id" : feedback_row.user_id,
                "username" : feedback_row.username,
                "user_full_name" : feedback_row.user_full_name,
                "query": feedback_row.query,
                "response": feedback_row.response,
                "query_time": feedback_row.timestamp
            }

            feedbacks.append(feedback)
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading response: {str(e)}")


# Endpoint to search documents only
@app.post("/search")
async def search_documents(query: str, k: int = 5):
    """Search for relevant documents without generating a response."""
    global embedding_manager, vector_store
    
    if embedding_manager is None or vector_store is None:
        raise HTTPException(status_code=503, detail="Service components not initialized")
    
    try:
        # Generate embedding for the query
        query_embedding = embedding_manager.generate_embeddings([query])[0]
        
        # Search for relevant documents
        relevant_docs = vector_store.search(query, query_embedding, k=k)
        
        # Format response
        sources = []
        for doc in relevant_docs:
            sources.append(SourceDocument(
                text=doc["text"],
                metadata=doc.get("metadata", {})
            ))
        
        return {"query": query, "sources": sources}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


# Endpoint to get system information
@app.get("/info")
async def get_system_info():
    """Get system information and configuration."""
    return {
        "app_title": config.APP_TITLE,
        "pinecone_index": config.PINECONE_INDEX_NAME,
        "environment": config.PINECONE_ENVIRONMENT,
        "components_initialized": all([
            embedding_manager is not None,
            vector_store is not None,
            llm_manager is not None
        ])
    }


# Endpoint to fetch conversation history by conversation_id
@app.get("/conversation/{conversation_id}")
async def get_conversation_history(conversation_id: int):
    db = next(get_db())
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
    result = {
        "conversation_id": conv.id,
        "user_id": conv.user_id,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": []
    }
    for msg in messages:
        msg_dict = {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at,
        }
        if msg.role == "assistant":
            sources = db.query(Source).filter(Source.message_id == msg.id).all()
            msg_dict["sources"] = [
                {"text": src.text, "metadata": src.meta} for src in sources
            ]
        result["messages"].append(msg_dict)
    return result

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "feedback": "/chat/feedback",
            "search": "/search",
            "info": "/info",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )