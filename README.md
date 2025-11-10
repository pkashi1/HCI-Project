# Voice Cooking Assistant

An AI-powered voice assistant that helps you cook by extracting recipes from YouTube videos and providing interactive, step-by-step guidance.

## Features

- 🎥 Extract recipes from YouTube cooking videos
- 🤖 AI-powered recipe structuring using local LLMs (Ollama)
- 🗣️ Voice and text-based interaction
- ⏱️ Built-in timer management
- 📝 Step-by-step navigation
- 💬 Natural language Q&A about recipes

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- macOS (for voice features) or Linux

## Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Project
```

### 2. Install Ollama and download models
```bash
# Install Ollama from https://ollama.ai/

# Pull required models
ollama pull phi4
ollama pull llama3.2:3b-instruct
```

### 3. Install Python dependencies
```bash
cd backend
pip install -r requirements.txt

# For voice features (optional)
pip install SpeechRecognition pyaudio
```

### 4. Create required directories
```bash
mkdir -p runtime/voices
mkdir -p runtime
```

### 5. Download voice model (optional, for TTS)
```bash
cd runtime/voices
curl -L -O https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
curl -L -O https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ../..
```

## Usage

### 1. Start the API server
```bash
cd backend
python3 -m uvicorn app:app --reload --port 8000
```

### 2. Extract a recipe from YouTube (in a new terminal)
```bash
cd backend
python3 test_extract.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

This creates a `*_recipe.json` file.

### 3. Start an interactive cooking session

**Option A: Text-based (recommended)**
```bash
python3 interactive_session.py "Recipe_Name_recipe.json"
```

**Option B: Voice-enabled**
```bash
python3 voice_session.py "Recipe_Name_recipe.json"
```

### 4. Use the assistant
- Type or say "next" to move to the next step
- Type or say "previous" to go back
- Ask questions like "What ingredients do I need?"
- Type "quit" to exit

## Project Structure

```
Project/
├── backend/
│   ├── app.py                 # FastAPI server
│   ├── yt_ingest.py          # YouTube transcript extraction
│   ├── extractors.py         # Recipe extraction with LLM
│   ├── llm.py                # Ollama integration
│   ├── state.py              # Session and timer management
│   ├── nlp_prompts.py        # LLM prompts
│   ├── interactive_session.py # Text-based CLI
│   ├── voice_session.py      # Voice-enabled CLI
│   ├── test_api.py           # API endpoint tests
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── index.html            # Web UI
│   ├── main.js               # Frontend logic
│   └── style.css             # Styling
└── runtime/
    ├── db.sqlite             # Session database (auto-created)
    └── voices/               # TTS voice models
```

## API Endpoints

- `POST /ingest` - Extract transcript from YouTube URL
- `POST /extract` - Extract structured recipe from transcript
- `POST /session/start` - Start a cooking session
- `POST /session/query` - Ask questions during cooking
- `POST /session/step` - Navigate between steps
- `POST /session/timer` - Add a timer
- `GET /session/{id}` - Get session state

## Testing

Run the full test suite:
```bash
cd backend
python3 test_api.py
```

When prompted, enter a YouTube cooking video URL.

## Troubleshooting

**Port 8000 already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Database schema errors:**
```bash
rm backend/runtime/db.sqlite
```

**Ollama not responding:**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama if needed
```

**Voice recognition issues:**
- Choose keyboard mode (option 2) when prompted
- Check microphone permissions in System Preferences

## Dependencies

Key Python packages:
- `fastapi` - Web API framework
- `uvicorn` - ASGI server
- `youtube-transcript-api` - YouTube transcript extraction
- `yt-dlp` - YouTube metadata
- `requests` - HTTP client
- `SpeechRecognition` - Voice input (optional)
- `pyaudio` - Audio I/O (optional)

## License

MIT
