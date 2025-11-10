"""
Test script for FastAPI endpoints.
Run the API server first: uvicorn app:app --reload
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("\n[1] Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Health check passed")


def test_ingest(youtube_url):
    """Test video ingestion."""
    print(f"\n[2] Testing ingestion with URL: {youtube_url}")
    response = requests.post(
        f"{BASE_URL}/ingest",
        json={"youtube_url": youtube_url}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    data = response.json()
    print(f"Video ID: {data['video_id']}")
    print(f"Title: {data['title']}")
    print(f"Transcript length: {len(data['transcript'])} characters")
    print(f"Snippets: {data['snippet_count']}")
    print("✓ Ingestion passed")
    return data


def test_extract(transcript):
    """Test recipe extraction."""
    print("\n[3] Testing recipe extraction...")
    response = requests.post(
        f"{BASE_URL}/extract",
        json={"transcript": transcript, "model": "gemma3:1b"}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    data = response.json()
    recipe = data["recipe"]
    print(f"Recipe title: {recipe.get('title', 'Untitled')}")
    print(f"Ingredients: {len(recipe.get('ingredients', {}))} categories")
    print(f"Steps: {len(recipe.get('steps', []))}")
    print("✓ Extraction passed")
    return recipe


def test_session_start(recipe):
    """Test session creation."""
    print("\n[4] Testing session start...")
    response = requests.post(
        f"{BASE_URL}/session/start",
        json={"recipe": recipe}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    data = response.json()
    print(f"Session ID: {data['session_id']}")
    print(f"Recipe: {data['recipe_title']}")
    print(f"Total steps: {data['total_steps']}")
    print("✓ Session start passed")
    return data["session_id"]


def test_session_query(session_id):
    """Test cooking queries."""
    print("\n[5] Testing session queries...")
    
    queries = [
        "What's the first step?",
        "What ingredients do I need?",
        "How long should I knead the dough?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: {query}")
        response = requests.post(
            f"{BASE_URL}/session/query",
            json={"session_id": session_id, "query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data['response'][:100]}...")
            print(f"  Current step: {data['current_step']}/{data['total_steps']}")
        else:
            print(f"  Error: {response.text}")
    
    print("✓ Queries passed")


def test_step_navigation(session_id):
    """Test step navigation."""
    print("\n[6] Testing step navigation...")
    
    actions = ["next", "next", "previous", "repeat"]
    
    for action in actions:
        print(f"\n  Action: {action}")
        response = requests.post(
            f"{BASE_URL}/session/step",
            json={"session_id": session_id, "action": action}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  {data['message']}")
            print(f"  Current step: {data['current_step']}/{data['total_steps']}")
            if data['step_data']:
                print(f"  Instruction: {data['step_data']['instruction'][:60]}...")
        else:
            print(f"  Error: {response.text}")
    
    print("✓ Navigation passed")


def test_timer(session_id):
    """Test timer functionality."""
    print("\n[7] Testing timers...")
    
    # Add timer
    response = requests.post(
        f"{BASE_URL}/session/timer",
        json={
            "session_id": session_id,
            "label": "Knead dough",
            "duration": "10 seconds"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Timer added: {data['label']}")
        print(f"  Duration: {data['seconds_total']} seconds")
        print(f"  Timer ID: {data['timer_id']}")
        
        # Wait a bit and check timer
        print("\n  Waiting 3 seconds...")
        time.sleep(3)
        
        # Get session state
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            data = response.json()
            active_timers = data['active_timers']
            if active_timers:
                timer = active_timers[0]
                print(f"  Timer remaining: {timer['seconds_remaining']} seconds")
            else:
                print("  Timer completed!")
    else:
        print(f"  Error: {response.text}")
    
    print("✓ Timer test passed")


def test_get_session(session_id):
    """Test getting session state."""
    print("\n[8] Testing get session state...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Session ID: {data['session_id']}")
        print(f"  Current step: {data['current_step']}/{data['total_steps']}")
        print(f"  Active timers: {len(data['active_timers'])}")
        print("✓ Get session passed")
    else:
        print(f"  Error: {response.text}")


def main():
    """Run all tests."""
    print("="*60)
    print("FASTAPI ENDPOINT TESTS")
    print("="*60)
    print("\nMake sure the API is running:")
    print("  uvicorn app:app --reload --port 8000")
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2-3: Ingest and extract
        # Use your pasta video or a short cooking video
        youtube_url = input("\nEnter a YouTube cooking video URL (or press Enter to use saved recipe): ").strip()
        
        if youtube_url:
            ingest_data = test_ingest(youtube_url)
            if not ingest_data:
                print("\n✗ Ingestion failed, stopping tests")
                return
            
            recipe = test_extract(ingest_data["transcript"])
            if not recipe:
                print("\n✗ Extraction failed, stopping tests")
                return
        else:
            # Load from saved file
            print("\nLoading saved recipe...")
            try:
                with open("Easy Pasta Dough Recipe_recipe.json", "r") as f:
                    recipe = json.load(f)
                print("✓ Loaded saved recipe")
            except FileNotFoundError:
                print("✗ No saved recipe found. Please provide a YouTube URL.")
                return
        
        # Test 4: Start session
        session_id = test_session_start(recipe)
        if not session_id:
            print("\n✗ Session start failed, stopping tests")
            return
        
        # Test 5-8: Session operations
        test_session_query(session_id)
        test_step_navigation(session_id)
        test_timer(session_id)
        test_get_session(session_id)
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print(f"\nSession ID for manual testing: {session_id}")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API")
        print("Make sure the server is running:")
        print("  cd backend && uvicorn app:app --reload --port 8000")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()