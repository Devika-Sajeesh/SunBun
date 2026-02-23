from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from datetime import datetime
from graph.orchestrator import get_graph_instance

# Initialize FastAPI app
app = FastAPI(
    title="SunBun Solar Assistant API",
    description="LangGraph-based agentic assistant for SunBun Solar",
    version="1.0.0"
)

# Enable CORS for agentchat.vercel.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for agentchat
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    
class ChatResponse(BaseModel):
    session_id: str
    response: str
    current_node: str
    is_complete: bool
    awaiting_input: bool
    timestamp: str

class ResetRequest(BaseModel):
    session_id: str

class ResetResponse(BaseModel):
    session_id: str
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

class SessionStateResponse(BaseModel):
    session_id: str
    state: dict


# Initialize graph on startup
graph = None

@app.on_event("startup")
async def startup_event():
    """Initialize graph on app startup"""
    global graph
    print("=" * 60)
    print("🌞 SunBun Solar Assistant API Starting...")
    print("=" * 60)
    
    try:
        graph = get_graph_instance()
        print("✅ Graph initialized successfully")
        print("📡 Server ready at http://localhost:8000")
        print("🔗 Connect agentchat.vercel.app to: http://localhost:8000/chat")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Error initializing graph: {e}")
        raise


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "ok",
        "service": "SunBun Solar Assistant",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "SunBun Solar Assistant",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for agentchat.vercel.app
    
    Accepts a message and session_id, returns assistant response
    """
    try:
        # Log incoming request
        print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] Session: {request.session_id}")
        print(f"👤 User: {request.message}")
        
        # Process message through graph
        result = graph.process_message(request.session_id, request.message)
        
        # Log response
        print(f"🤖 Assistant: {result['response'][:100]}...")
        print(f"📍 Node: {result['current_node']}")
        
        # Return response
        return {
            "session_id": request.session_id,
            "response": result["response"],
            "current_node": result["current_node"],
            "is_complete": result["is_complete"],
            "awaiting_input": result["awaiting_input"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@app.post("/reset", response_model=ResetResponse)
async def reset_session(request: ResetRequest):
    """
    Reset a session to initial state
    """
    try:
        graph.reset_session(request.session_id)
        
        print(f"\n🔄 Session {request.session_id} reset")
        
        return {
            "session_id": request.session_id,
            "status": "success",
            "message": "Session reset successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting session: {str(e)}"
        )


@app.get("/session/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """
    Get current session state for debugging
    """
    try:
        state = graph.get_session_state(session_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Mask sensitive data
        safe_state = state.copy()
        if "otp_code" in safe_state and safe_state["otp_code"]:
            safe_state["otp_code"] = "***masked***"
        
        return {
            "session_id": session_id,
            "state": safe_state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session: {str(e)}"
        )


@app.get("/graph/diagram")
async def get_graph_diagram():
    """
    Get mermaid diagram of the graph structure
    """
    try:
        diagram = graph.export_graph_diagram()
        return {
            "diagram": diagram,
            "format": "mermaid"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating diagram: {str(e)}"
        )


# Alternative endpoint for compatibility
@app.post("/message")
async def message_endpoint(request: ChatRequest):
    """
    Alternative message endpoint (same as /chat)
    Some clients may use /message instead of /chat
    """
    return await chat(request)


# Run server
if __name__ == "__main__":
    print("\n🚀 Starting SunBun Solar Assistant API...")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
