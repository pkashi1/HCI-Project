"""
Interactive cooking session CLI.
Start a session and ask questions in real-time.
"""
import sys
import json
import requests

BASE_URL = "http://localhost:8000"


def start_session(recipe_file):
    """Start a new cooking session."""
    with open(recipe_file, 'r') as f:
        recipe = json.load(f)
    
    response = requests.post(f"{BASE_URL}/session/start", json={"recipe": recipe})
    
    if response.status_code == 200:
        data = response.json()
        return data['session_id'], data['recipe_title'], data['total_steps']
    else:
        print(f"Error starting session: {response.text}")
        return None, None, None


def query_session(session_id, query):
    """Ask a question during cooking."""
    response = requests.post(
        f"{BASE_URL}/session/query",
        json={"session_id": session_id, "query": query}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None


def navigate_step(session_id, action):
    """Navigate between steps."""
    response = requests.post(
        f"{BASE_URL}/session/step",
        json={"session_id": session_id, "action": action}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 interactive_session.py <recipe_json_file>")
        print('Example: python3 interactive_session.py "Easy Pasta Dough Recipe_recipe.json"')
        sys.exit(1)
    
    recipe_file = sys.argv[1]
    
    # Start session
    print("Starting cooking session...")
    session_id, recipe_title, total_steps = start_session(recipe_file)
    
    if not session_id:
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🍳 Cooking: {recipe_title}")
    print(f"📋 Total steps: {total_steps}")
    print(f"🆔 Session ID: {session_id}")
    print(f"{'='*60}\n")
    
    print("Commands:")
    print("  - Ask any question about the recipe")
    print("  - Type 'next' to go to next step")
    print("  - Type 'prev' to go to previous step")
    print("  - Type 'repeat' to repeat current step")
    print("  - Type 'quit' to exit\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Happy cooking!")
                break
            
            # Handle navigation commands
            if user_input.lower() in ['next', 'n']:
                result = navigate_step(session_id, "next")
                if result:
                    print(f"\n✓ {result['message']}")
                    print(f"Step {result['current_step']}/{result['total_steps']}")
                    if result['step_data']:
                        print(f"📝 {result['step_data']['instruction']}\n")
                continue
            
            if user_input.lower() in ['prev', 'previous', 'p']:
                result = navigate_step(session_id, "previous")
                if result:
                    print(f"\n✓ {result['message']}")
                    print(f"Step {result['current_step']}/{result['total_steps']}")
                    if result['step_data']:
                        print(f"📝 {result['step_data']['instruction']}\n")
                continue
            
            if user_input.lower() in ['repeat', 'r']:
                result = navigate_step(session_id, "repeat")
                if result:
                    print(f"\n✓ {result['message']}")
                    if result['step_data']:
                        print(f"📝 {result['step_data']['instruction']}\n")
                continue
            
            # Query the assistant
            result = query_session(session_id, user_input)
            if result:
                print(f"\n🤖 Assistant: {result['response']}")
                print(f"📍 Step {result['current_step']}/{result['total_steps']}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Happy cooking!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
