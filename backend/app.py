# """
# FastAPI backend for voice cooking assistant.
# Handles recipe ingestion, extraction, session management, and cooking assistance.
# """
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, Dict, List
# import asyncio

# from yt_ingest import get_transcript
# from extractors import extract_recipe
# from state import get_session_manager, parse_time_string
# from nlp_prompts import get_cooking_assistant_prompt
# from llm import chat
# import json


# app = FastAPI(title="Voice Cooking Assistant API", version="1.0.0")

# # Enable CORS for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Request/Response Models
# class IngestRequest(BaseModel):
#     youtube_url: str


# class IngestResponse(BaseModel):
#     video_id: str
#     title: str
#     transcript: str
#     snippet_count: int


# class ExtractRequest(BaseModel):
#     transcript: str
#     model: Optional[str] = "phi4"


# class ExtractResponse(BaseModel):
#     recipe: Dict


# class SessionStartRequest(BaseModel):
#     recipe: Dict


# class SessionStartResponse(BaseModel):
#     session_id: str
#     recipe_title: str
#     total_steps: int


# class SessionQueryRequest(BaseModel):
#     session_id: str
#     query: str


# class SessionQueryResponse(BaseModel):
#     response: str
#     current_step: int
#     total_steps: int
#     active_timers: List[Dict]


# class TimerRequest(BaseModel):
#     session_id: str
#     label: str
#     duration: str  # e.g., "5 minutes", "30 seconds"


# class TimerResponse(BaseModel):
#     timer_id: str
#     label: str
#     seconds_total: int
#     seconds_remaining: int


# class StepNavigationRequest(BaseModel):
#     session_id: str
#     action: str  # "next", "previous", "repeat"


# # Endpoints

# @app.get("/")
# async def root():
#     """Health check endpoint."""
#     return {
#         "status": "running",
#         "service": "Voice Cooking Assistant API",
#         "version": "1.0.0"
#     }


# @app.post("/ingest", response_model=IngestResponse)
# async def ingest_video(request: IngestRequest):
#     """
#     Ingest YouTube video and extract transcript.
    
#     Args:
#         youtube_url: YouTube video URL or ID
        
#     Returns:
#         Transcript data with metadata
#     """
#     try:
#         print(f"Ingesting URL: {request.youtube_url}")
        
#         # Clean URL (remove HTML entities)
#         clean_url = request.youtube_url.replace('&amp;', '&')
#         print(f"Cleaned URL: {clean_url}")
        
#         result = get_transcript(clean_url)
#         print(f"Transcript result: {result is not None}")
        
#         if not result:
#             raise HTTPException(status_code=400, detail="Failed to extract transcript - no transcript available for this video")
        
#         print(f"Successfully extracted transcript: {len(result['text'])} characters")
        
#         return IngestResponse(
#             video_id=result["video_id"],
#             title=result["title"],
#             transcript=result["text"],
#             snippet_count=len(result.get("snippets", []))
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         import traceback
#         error_detail = f"Ingestion error: {str(e)}\n{traceback.format_exc()}"
#         print(error_detail)
#         raise HTTPException(status_code=500, detail=error_detail)


# @app.post("/extract", response_model=ExtractResponse)
# async def extract_recipe_endpoint(request: ExtractRequest):
#     """
#     Extract structured recipe from transcript using LLM.
    
#     Args:
#         transcript: Video transcript text
#         model: LLM model to use (optional)
        
#     Returns:
#         Structured recipe JSON
#     """
#     try:
#         recipe = extract_recipe(request.transcript, model=request.model)
        
#         if not recipe:
#             raise HTTPException(status_code=400, detail="Failed to extract recipe")
        
#         return ExtractResponse(recipe=recipe)
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


# @app.post("/session/start", response_model=SessionStartResponse)
# async def start_session(request: SessionStartRequest):
#     """
#     Start a new cooking session with a recipe.
    
#     Args:
#         recipe: Structured recipe JSON
        
#     Returns:
#         Session ID and metadata
#     """
#     try:
#         manager = get_session_manager()
#         session = manager.create_session(request.recipe)
        
#         return SessionStartResponse(
#             session_id=session.session_id,
#             recipe_title=session.recipe.get("title", "Untitled Recipe"),
#             total_steps=session.total_steps
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Session error: {str(e)}")


# @app.post("/session/query", response_model=SessionQueryResponse)
# async def query_session(request: SessionQueryRequest):
#     """
#     Ask a question or give a command during cooking.
    
#     Args:
#         session_id: Active session ID
#         query: User's question or command
        
#     Returns:
#         Assistant's response with session state
#     """
#     try:
#         manager = get_session_manager()
#         session = manager.get_session(request.session_id)
        
#         if not session:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         # Check for completed timers
#         completed_timers = session.check_timers()
#         if completed_timers:
#             timer_alerts = ", ".join([f"{t.label} is done" for t in completed_timers])
#             prefix = f"Alert: {timer_alerts}. "
#         else:
#             prefix = ""
        
#         # Build context for LLM
#         recipe_json = json.dumps(session.recipe, indent=2)
#         timers_list = [f"{t.label}: {t.seconds_remaining}s remaining" for t in session.get_active_timers()]
        
#         messages = get_cooking_assistant_prompt(
#             recipe_json=recipe_json,
#             current_step=session.current_step,
#             timers=timers_list,
#             user_query=request.query
#         )
        
#         # Get response from LLM
#         response = chat(messages, temperature=0.7)
        
#         # Save session
#         manager.update_session(session)
        
#         return SessionQueryResponse(
#             response=prefix + response,
#             current_step=session.current_step,
#             total_steps=session.total_steps,
#             active_timers=[t.to_dict() for t in session.get_active_timers()]
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


# @app.post("/session/step")
# async def navigate_step(request: StepNavigationRequest):
#     """
#     Navigate between recipe steps.
    
#     Args:
#         session_id: Active session ID
#         action: "next", "previous", or "repeat"
        
#     Returns:
#         Updated session state
#     """
#     try:
#         manager = get_session_manager()
#         session = manager.get_session(request.session_id)
        
#         if not session:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         # Perform navigation
#         if request.action == "next":
#             success = session.next_step()
#             message = "Moved to next step" if success else "Already at last step"
#         elif request.action == "previous":
#             success = session.previous_step()
#             message = "Moved to previous step" if success else "Already at first step"
#         elif request.action == "repeat":
#             message = "Repeating current step"
#         else:
#             raise HTTPException(status_code=400, detail="Invalid action")
        
#         # Save session
#         manager.update_session(session)
        
#         return {
#             "message": message,
#             "current_step": session.current_step,
#             "total_steps": session.total_steps,
#             "step_data": session.current_step_data
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Navigation error: {str(e)}")


# @app.post("/session/timer", response_model=TimerResponse)
# async def add_timer(request: TimerRequest):
#     """
#     Add a timer to the session.
    
#     Args:
#         session_id: Active session ID
#         label: Timer label (e.g., "Boil pasta")
#         duration: Duration string (e.g., "10 minutes")
        
#     Returns:
#         Timer details
#     """
#     try:
#         manager = get_session_manager()
#         session = manager.get_session(request.session_id)
        
#         if not session:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         # Parse duration
#         seconds = parse_time_string(request.duration)
#         if seconds is None:
#             raise HTTPException(status_code=400, detail="Invalid duration format")
        
#         # Add timer
#         timer = session.add_timer(request.label, seconds)
        
#         # Save session
#         manager.update_session(session)
        
#         return TimerResponse(
#             timer_id=timer.id,
#             label=timer.label,
#             seconds_total=timer.seconds_total,
#             seconds_remaining=timer.seconds_remaining
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Timer error: {str(e)}")


# @app.get("/session/{session_id}")
# async def get_session_state(session_id: str):
#     """
#     Get current session state.
    
#     Args:
#         session_id: Session ID
        
#     Returns:
#         Complete session state
#     """
#     try:
#         manager = get_session_manager()
#         session = manager.get_session(session_id)
        
#         if not session:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         # Check for completed timers
#         session.check_timers()
#         manager.update_session(session)
        
#         return session.to_dict()
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Session error: {str(e)}")


# @app.get("/sessions")
# async def list_sessions():
#     """List all sessions."""
#     try:
#         manager = get_session_manager()
#         session_ids = manager.list_sessions()
#         return {"sessions": session_ids, "count": len(session_ids)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
"""
FastAPI backend for voice cooking assistant.
Handles recipe ingestion, extraction, session management, and cooking assistance.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import asyncio

from yt_ingest import get_transcript
from extractors import extract_recipe
from state import get_session_manager, parse_time_string
from nlp_prompts import get_cooking_assistant_prompt
from llm import chat
import json


app = FastAPI(title="Voice Cooking Assistant API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class IngestRequest(BaseModel):
    youtube_url: str


class IngestResponse(BaseModel):
    video_id: str
    title: str
    transcript: str
    snippet_count: int


class ExtractRequest(BaseModel):
    transcript: str
    model: Optional[str] = "gemma3:1b"


class ExtractResponse(BaseModel):
    recipe: Dict


class SessionStartRequest(BaseModel):
    recipe: Dict


class SessionStartResponse(BaseModel):
    session_id: str
    recipe_title: str
    total_steps: int


class SessionQueryRequest(BaseModel):
    session_id: str
    query: str


class SessionQueryResponse(BaseModel):
    response: str
    current_step: int
    total_steps: int
    active_timers: List[Dict]
    is_paused: bool = False


class TimerRequest(BaseModel):
    session_id: str
    label: str
    duration: str  # e.g., "5 minutes", "30 seconds"


class TimerResponse(BaseModel):
    timer_id: str
    label: str
    seconds_total: int
    seconds_remaining: int


class StepNavigationRequest(BaseModel):
    session_id: str
    action: str  # "next", "previous", "repeat"


# Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Voice Cooking Assistant API",
        "version": "1.0.0"
    }


@app.post("/ingest", response_model=IngestResponse)
async def ingest_video(request: IngestRequest):
    """
    Ingest YouTube video and extract transcript.
    
    Args:
        youtube_url: YouTube video URL or ID
        
    Returns:
        Transcript data with metadata
    """
    try:
        result = get_transcript(request.youtube_url)
        
        if not result:
            raise HTTPException(
                status_code=400, 
                detail="Failed to extract transcript - no transcript available for this video. Try a different video with captions/subtitles enabled."
            )
        
        return IngestResponse(
            video_id=result["video_id"],
            title=result["title"],
            transcript=result["text"],
            snippet_count=len(result["snippets"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


@app.post("/extract", response_model=ExtractResponse)
async def extract_recipe_endpoint(request: ExtractRequest):
    """
    Extract structured recipe from transcript using LLM.
    
    Args:
        transcript: Video transcript text
        model: LLM model to use (optional)
        
    Returns:
        Structured recipe JSON
    """
    try:
        recipe = extract_recipe(request.transcript, model=request.model)
        
        if not recipe:
            raise HTTPException(status_code=400, detail="Failed to extract recipe")
        
        return ExtractResponse(recipe=recipe)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


@app.post("/session/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """
    Start a new cooking session with a recipe.
    
    Args:
        recipe: Structured recipe JSON
        
    Returns:
        Session ID and metadata
    """
    try:
        manager = get_session_manager()
        session = manager.create_session(request.recipe)
        
        return SessionStartResponse(
            session_id=session.session_id,
            recipe_title=session.recipe.get("title", "Untitled Recipe"),
            total_steps=session.total_steps
        )
        
    except Exception as e:
        import traceback
        error_detail = f"Session error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/session/query", response_model=SessionQueryResponse)
async def query_session(request: SessionQueryRequest):
    """
    Ask a question or give a command during cooking.
    
    Args:
        session_id: Active session ID
        query: User's question or command
        
    Returns:
        Assistant's response with session state
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check for navigation commands
        import re
        query_lower = request.query.lower()
        
        # Handle "pause"
        if re.search(r'\b(pause|stop|hold)\b', query_lower):
            session.is_paused = True
            manager.update_session(session)
            return SessionQueryResponse(
                response="Session paused. Say 'resume' or 'continue' when you're ready.",
                current_step=session.current_step,
                total_steps=session.total_steps,
                active_timers=[t.to_dict() for t in session.get_active_timers()],
                is_paused=True
            )
        
        # Handle "resume"
        if re.search(r'\b(resume|continue|start)\b', query_lower):
            session.is_paused = False
            manager.update_session(session)
            current_step_data = session.current_step_data
            step_text = current_step_data['instruction'] if current_step_data else "Ready to continue"
            return SessionQueryResponse(
                response=f"Resuming. Step {session.current_step}: {step_text}",
                current_step=session.current_step,
                total_steps=session.total_steps,
                active_timers=[t.to_dict() for t in session.get_active_timers()],
                is_paused=False
            )
        
        # Handle "next step"
        if re.search(r'\b(next|next step)\b', query_lower):
            session.next_step()
        
        # Handle "previous step"
        elif re.search(r'\b(previous|previous step|back|go back)\b', query_lower):
            session.previous_step()
        
        # Handle "repeat step" or "repeat"
        elif re.search(r'\b(repeat|repeat step|again)\b', query_lower):
            pass  # Keep current step
        
        # Handle "go to step X"
        else:
            step_match = re.search(r'(?:go to|jump to|show me|goto)\s+step\s+(\d+)', query_lower)
            if step_match:
                target_step = int(step_match.group(1))
                if 1 <= target_step <= session.total_steps:
                    session.current_step = target_step
        
        # Handle "explain" or "explain step"
        explain_match = re.search(r'\b(explain|detail|more info|tell me more)\b', query_lower)
        
        # Handle "list first/last X steps"
        list_match = re.search(r'list\s+(?:the\s+)?(first|last)\s+(\d+)\s+steps?', query_lower)
        if list_match:
            direction = list_match.group(1)
            count = int(list_match.group(2))
            steps = session.recipe.get("steps", [])
            
            if direction == "first":
                selected_steps = steps[:count]
            else:
                selected_steps = steps[-count:]
            
            response = "\n".join([f"Step {s['step_number']}: {s['instruction']}" for s in selected_steps])
            manager.update_session(session)
            
            return SessionQueryResponse(
                response=response,
                current_step=session.current_step,
                total_steps=session.total_steps,
                active_timers=[t.to_dict() for t in session.get_active_timers()],
                is_paused=session.is_paused
            )
        
        # For explain requests, add context to the query
        if explain_match:
            current_step_data = session.current_step_data
            if current_step_data:
                request.query = f"Explain step {session.current_step} in detail: {current_step_data['instruction']}"
        
        # Check for completed timers
        completed_timers = session.check_timers()
        if completed_timers:
            timer_alerts = ", ".join([f"{t.label} is done" for t in completed_timers])
            prefix = f"Alert: {timer_alerts}. "
        else:
            prefix = ""
        
        # Build context for LLM
        recipe_json = json.dumps(session.recipe, indent=2)
        timers_list = [f"{t.label}: {t.seconds_remaining}s remaining" for t in session.get_active_timers()]
        
        messages = get_cooking_assistant_prompt(
            recipe_json=recipe_json,
            current_step=session.current_step,
            timers=timers_list,
            user_query=request.query
        )
        
        # Get response from LLM
        response = chat(messages, temperature=0.7)
        
        # Save session
        manager.update_session(session)
        
        return SessionQueryResponse(
            response=prefix + response,
            current_step=session.current_step,
            total_steps=session.total_steps,
            active_timers=[t.to_dict() for t in session.get_active_timers()],
            is_paused=session.is_paused
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


@app.post("/session/step")
async def navigate_step(request: StepNavigationRequest):
    """
    Navigate between recipe steps.
    
    Args:
        session_id: Active session ID
        action: "next", "previous", or "repeat"
        
    Returns:
        Updated session state
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Perform navigation
        if request.action == "next":
            success = session.next_step()
            message = "Moved to next step" if success else "Already at last step"
        elif request.action == "previous":
            success = session.previous_step()
            message = "Moved to previous step" if success else "Already at first step"
        elif request.action == "repeat":
            message = "Repeating current step"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Save session
        manager.update_session(session)
        
        return {
            "message": message,
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "step_data": session.current_step_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Navigation error: {str(e)}")


@app.post("/session/timer", response_model=TimerResponse)
async def add_timer(request: TimerRequest):
    """
    Add a timer to the session.
    
    Args:
        session_id: Active session ID
        label: Timer label (e.g., "Boil pasta")
        duration: Duration string (e.g., "10 minutes")
        
    Returns:
        Timer details
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Parse duration
        seconds = parse_time_string(request.duration)
        if seconds is None:
            raise HTTPException(status_code=400, detail="Invalid duration format")
        
        # Add timer
        timer = session.add_timer(request.label, seconds)
        
        # Save session
        manager.update_session(session)
        
        return TimerResponse(
            timer_id=timer.id,
            label=timer.label,
            seconds_total=timer.seconds_total,
            seconds_remaining=timer.seconds_remaining
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timer error: {str(e)}")


@app.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """
    Get current session state.
    
    Args:
        session_id: Session ID
        
    Returns:
        Complete session state
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check for completed timers
        session.check_timers()
        manager.update_session(session)
        
        return session.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session error: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    """List all sessions."""
    try:
        manager = get_session_manager()
        session_ids = manager.list_sessions()
        return {"sessions": session_ids, "count": len(session_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)