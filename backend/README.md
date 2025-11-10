# Backend - Voice Cooking Assistant API

FastAPI backend for a voice-enabled cooking assistant that extracts recipes from YouTube videos and provides real-time cooking guidance.

---

## 📁 File Overview

### Core Application Files

#### **app.py**
Main FastAPI application server. Defines all REST API endpoints for the cooking assistant.

**Key Features:**
- `/ingest` - Extract transcripts from YouTube videos
- `/extract` - Convert transcripts to structured recipe JSON using LLM
- `/session/start` - Create a new cooking session
- `/session/query` - Ask questions during cooking (voice assistant)
- `/session/step` - Navigate between recipe steps (next/previous/repeat)
- `/session/timer` - Add and manage cooking timers
- CORS middleware for frontend integration

**Dependencies:** FastAPI, Pydantic, all other backend modules

---

#### **yt_ingest.py**
YouTube video transcript extraction module.

**What it does:**
- Extracts video ID from YouTube URLs
- Fetches captions/transcripts using YouTube Transcript API
- Falls back to audio download + Whisper ASR if captions unavailable
- Returns transcript text with metadata (title, video ID, snippets)

**Key Functions:**
- `extract_video_id()` - Parse YouTube URLs
- `fetch_transcript()` - Get captions from YouTube
- `transcribe_with_whisper()` - ASR fallback using faster-whisper
- `robust_ingest()` - Main entry point with automatic fallback

**Dependencies:** youtube-transcript-api, yt-dlp, faster-whisper

---

#### **extractors.py**
Recipe extraction from video transcripts using LLM.

**What it does:**
- Converts raw transcript text into structured recipe JSON
- Uses LLM (Ollama) to parse ingredients, tools, and steps
- Validates recipe structure
- Retries with JSON repair if parsing fails

**Key Components:**
- `RecipeExtractor` class - Main extraction logic with retry mechanism
- `extract_recipe()` - Convenience function for one-shot extraction
- `print_recipe_summary()` - Pretty-print recipe details

**Output Schema:**
```json
{
  "title": "Recipe name",
  "ingredients": {"main": [...], "spices_and_seasonings": [...]},
  "kitchen_tools_and_dishes": [...],
  "steps": [{"step_number": 1, "instruction": "...", "estimated_time": "..."}],
  "total_time": "45 minutes",
  "servings": "4"
}
```

**Dependencies:** llm.py, nlp_prompts.py

---

#### **state.py**
Cooking session state management and timer system.

**What it does:**
- Manages active cooking sessions with SQLite persistence
- Tracks current step, timers, and session metadata
- Provides step navigation (next/previous/repeat)
- Timer management with countdown and completion detection

**Key Classes:**
- `Timer` - Represents a cooking timer with countdown logic
- `CookingSession` - Active cooking session with recipe and state
- `SessionManager` - Manages multiple sessions with database persistence

**Key Functions:**
- `parse_time_string()` - Parse natural language time ("5 minutes" → 300 seconds)
- `get_session_manager()` - Get global session manager singleton

**Database:** SQLite (runtime/db.sqlite) with sessions and timers tables

---

#### **llm.py**
LLM client wrapper for Ollama API.

**What it does:**
- Connects to local Ollama server for LLM inference
- Handles chat completions with automatic model fallback
- Extracts JSON from LLM responses (removes markdown, etc.)
- Health checks and model listing

**Key Components:**
- `OllamaClient` class - Main API client
- `chat()` - Convenience function with automatic fallback
- `extract_json_from_response()` - Clean JSON from LLM output

**Supported Models:** phi4 (default), gemma3:1b, llama3.2:3b-instruct

**Dependencies:** requests, Ollama running locally (http://localhost:11434)

---

#### **nlp_prompts.py**
Prompt templates for LLM-based recipe extraction and cooking assistance.

**What it does:**
- Defines system and user prompts for different LLM tasks
- Recipe extraction prompt with strict JSON schema
- Cooking assistant prompt for conversational guidance
- JSON repair prompt for fixing malformed output

**Key Prompts:**
- `RECIPE_EXTRACTION_SYSTEM` - Instructs LLM to extract structured recipes
- `COOKING_ASSISTANT_SYSTEM` - Defines voice assistant personality and rules
- `JSON_FIX_SYSTEM` - Repairs malformed JSON

**Key Functions:**
- `get_extraction_prompt()` - Build messages for recipe extraction
- `get_cooking_assistant_prompt()` - Build messages for cooking queries
- `get_json_fix_prompt()` - Build messages for JSON repair

---

### Utility Files

#### **asr.py**
Automatic Speech Recognition module (currently empty - placeholder for future voice input).

---

#### **tts.py**
Text-to-Speech module (currently empty - placeholder for future voice output).

---

### Test Files

#### **test_api.py**
Comprehensive test suite for all FastAPI endpoints.

**Tests:**
1. Health check
2. Video ingestion
3. Recipe extraction
4. Session creation
5. Cooking queries
6. Step navigation
7. Timer functionality
8. Session state retrieval

**Usage:** Run API server first, then execute `python test_api.py`

---

#### **test_extract.py**
End-to-end pipeline test: YouTube URL → Transcript → Recipe JSON.

**What it does:**
- Tests complete workflow from video to structured recipe
- Saves transcript and recipe JSON to files
- Prints recipe summary

**Usage:** `python test_extract.py <youtube_url> [model]`

---

### Configuration Files

#### **requirements.txt**
Python dependencies for the backend.

**Key Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `youtube-transcript-api` - YouTube caption extraction
- `yt-dlp` - YouTube video/audio download
- `requests` - HTTP client for Ollama API

**Additional (not in file):**
- `faster-whisper` - ASR fallback (optional)
- Ollama - Local LLM server (separate installation)

---

#### **__init__.py**
Empty file marking the directory as a Python package.

---

### Data Files

#### **Easy Pasta Dough Recipe_recipe.json**
Sample extracted recipe in JSON format (test output).

---

#### **Easy Pasta Dough Recipe_transcript.txt**
Sample video transcript (test output).

---

#### **The Best Way To Make Pasta From Scratch _ Epicurious 101_transcript.txt**
Another sample transcript (test output).

---

#### **server.log**
Application log file (generated at runtime).

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull phi4
```

### 3. Start Ollama Server
```bash
ollama serve
```

### 4. Run API Server
```bash
uvicorn app:app --reload --port 8000
```

### 5. Test the API
```bash
python test_api.py
```

---

## 🔄 Data Flow

```
YouTube URL
    ↓
[yt_ingest.py] → Transcript
    ↓
[extractors.py + llm.py + nlp_prompts.py] → Structured Recipe JSON
    ↓
[app.py] → API Endpoint (/extract)
    ↓
[state.py] → Cooking Session
    ↓
[app.py] → Voice Assistant (/session/query)
```

---

## 🎯 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/ingest` | POST | Extract YouTube transcript |
| `/extract` | POST | Convert transcript to recipe |
| `/session/start` | POST | Start cooking session |
| `/session/query` | POST | Ask cooking questions |
| `/session/step` | POST | Navigate steps |
| `/session/timer` | POST | Add timer |

---

## 🧪 Testing

### Test Individual Components
```bash
# Test transcript extraction
python yt_ingest.py "https://youtube.com/watch?v=VIDEO_ID"

# Test recipe extraction
python extractors.py "transcript.txt"

# Test LLM connection
python llm.py

# Test full pipeline
python test_extract.py "https://youtube.com/watch?v=VIDEO_ID"
```

### Test API Endpoints
```bash
# Start server first
uvicorn app:app --reload --port 8000

# Run tests
python test_api.py
```

---

## 📝 Notes

- **LLM Models:** Requires Ollama with phi4, gemma3:1b, or llama3.2 models
- **Database:** SQLite database created at `runtime/db.sqlite`
- **Transcripts:** Falls back to Whisper ASR if YouTube captions unavailable
- **Voice I/O:** asr.py and tts.py are placeholders for future implementation
- **CORS:** Enabled for all origins (configure for production)

---

## 🐛 Troubleshooting

**"Could not connect to Ollama"**
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`

**"No transcript available"**
- Video may not have captions
- Requires faster-whisper for ASR fallback: `pip install faster-whisper`

**"JSON parsing error"**
- LLM may need different model (try gemma3:1b)
- Check prompt templates in nlp_prompts.py

---

## 📚 Architecture

**Design Pattern:** Modular microservice architecture
- **Ingestion Layer:** yt_ingest.py
- **Processing Layer:** extractors.py, llm.py, nlp_prompts.py
- **State Layer:** state.py
- **API Layer:** app.py
- **Future:** asr.py, tts.py for voice I/O
