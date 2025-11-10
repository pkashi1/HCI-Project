"""
Start a cooking session with a recipe JSON file.
"""
import sys
import json
import requests

BASE_URL = "http://localhost:8000"

def start_session(recipe_file: str):
    """Start a cooking session and return session ID."""
    
    # Load recipe
    try:
        with open(recipe_file, 'r', encoding='utf-8') as f:
            recipe = json.load(f)
    except FileNotFoundError:
        print(f"✗ Recipe file not found: {recipe_file}")
        return None
    
    print(f"Starting session with recipe: {recipe.get('title', 'Untitled')}")
    
    # Start session
    try:
        response = requests.post(
            f"{BASE_URL}/session/start",
            json={"recipe": recipe}
        )
        response.raise_for_status()
        
        data = response.json()
        session_id = data['session_id']
        
        print(f"\n✓ Session started successfully!")
        print(f"Session ID: {session_id}")
        print(f"Recipe: {data['recipe_title']}")
        print(f"Total Steps: {data['total_steps']}")
        print(f"\nSave this session ID to interact with your cooking session!")
        
        return session_id
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to backend server!")
        print("Start it with: uvicorn app:app --reload --port 8000")
        return None
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python start_session.py <recipe_json_file>")
        print('\nExample:')
        print('  python start_session.py "Chicken Fried Rice - EASY DINNER under 30 Minutes_recipe.json"')
        sys.exit(1)
    
    recipe_file = sys.argv[1]
    session_id = start_session(recipe_file)
    
    if session_id:
        sys.exit(0)
    else:
        sys.exit(1)
