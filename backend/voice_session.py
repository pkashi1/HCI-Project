"""
Voice-interactive cooking session.
Speak to ask questions and hear responses.
"""
import sys
import json
import requests
import subprocess
import os

BASE_URL = "http://localhost:8000"


def speak(text):
    """Convert text to speech and play it."""
    try:
        # Use macOS 'say' command for TTS
        subprocess.run(["say", text], check=True)
    except Exception as e:
        print(f"TTS Error: {e}")
        print(f"Assistant: {text}")


def listen(use_voice=True):
    """Listen for voice input and convert to text."""
    if not use_voice:
        return input("You: ").strip()
    
    try:
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 4000  # Adjust for sensitivity
        recognizer.dynamic_energy_threshold = True
        
        with sr.Microphone() as source:
            print("🎤 Listening... (speak clearly)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
        
        print("🔄 Processing...")
        text = recognizer.recognize_google(audio)
        print(f"✓ You said: {text}")
        return text
    
    except sr.WaitTimeoutError:
        print("⏱️  Timeout - try typing instead")
        return input("Type: ").strip() or None
    except sr.UnknownValueError:
        print("❌ Couldn't understand - try typing")
        return input("Type: ").strip() or None
    except Exception as e:
        print(f"ASR Error: {e}")
        return input("Type: ").strip() or None


def start_session(recipe_file):
    """Start a new cooking session."""
    with open(recipe_file, 'r') as f:
        recipe = json.load(f)
    
    response = requests.post(f"{BASE_URL}/session/start", json={"recipe": recipe})
    
    if response.status_code == 200:
        data = response.json()
        return data['session_id'], data['recipe_title'], data['total_steps']
    return None, None, None


def query_session(session_id, query):
    """Ask a question during cooking."""
    response = requests.post(
        f"{BASE_URL}/session/query",
        json={"session_id": session_id, "query": query}
    )
    
    if response.status_code == 200:
        return response.json()
    return None


def navigate_step(session_id, action):
    """Navigate between steps."""
    response = requests.post(
        f"{BASE_URL}/session/step",
        json={"session_id": session_id, "action": action}
    )
    
    if response.status_code == 200:
        return response.json()
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 voice_session.py <recipe_json_file>")
        sys.exit(1)
    
    recipe_file = sys.argv[1]
    
    # Check dependencies
    try:
        import speech_recognition
    except ImportError:
        print("Installing speech recognition...")
        subprocess.run([sys.executable, "-m", "pip", "install", "SpeechRecognition", "pyaudio"], check=True)
        import speech_recognition
    
    # Start session
    print("Starting cooking session...")
    session_id, recipe_title, total_steps = start_session(recipe_file)
    
    if not session_id:
        print("Failed to start session")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🍳 Cooking: {recipe_title}")
    print(f"📋 Total steps: {total_steps}")
    print(f"{'='*60}\n")
    
    # Ask for input mode
    print("\nInput mode:")
    print("  1. Voice (speak commands)")
    print("  2. Keyboard (type commands)")
    mode = input("Choose (1/2) [default: 2]: ").strip() or "2"
    use_voice = mode == "1"
    
    if use_voice:
        speak(f"Let's cook {recipe_title}. I'll guide you through {total_steps} steps.")
        speak("Say next to move forward, previous to go back, or ask me any question.")
    else:
        print(f"\n👨‍🍳 Let's cook {recipe_title}!")
    
    print("\nCommands:")
    print("  - 'next' to go to next step")
    print("  - 'previous' to go back")
    print("  - 'repeat' to hear current step again")
    print("  - Ask any question about the recipe")
    print("  - 'quit' to exit\n")
    
    # Interactive loop
    while True:
        try:
            user_input = listen(use_voice)
            
            if not user_input:
                continue
            
            user_lower = user_input.lower()
            
            # Exit commands
            if any(word in user_lower for word in ['quit', 'stop', 'exit', 'goodbye']):
                speak("Happy cooking! Goodbye!")
                break
            
            # Navigation commands
            if 'next' in user_lower:
                result = navigate_step(session_id, "next")
                if result and result['step_data']:
                    speak(f"Step {result['current_step']}. {result['step_data']['instruction']}")
                else:
                    speak("You're at the last step")
                continue
            
            if 'previous' in user_lower or 'back' in user_lower:
                result = navigate_step(session_id, "previous")
                if result and result['step_data']:
                    speak(f"Going back. Step {result['current_step']}. {result['step_data']['instruction']}")
                else:
                    speak("You're at the first step")
                continue
            
            if 'repeat' in user_lower or 'again' in user_lower:
                result = navigate_step(session_id, "repeat")
                if result and result['step_data']:
                    speak(result['step_data']['instruction'])
                continue
            
            # Query the assistant
            result = query_session(session_id, user_input)
            if result:
                speak(result['response'])
        
        except KeyboardInterrupt:
            speak("Happy cooking!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
