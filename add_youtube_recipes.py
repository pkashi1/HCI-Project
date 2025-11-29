#!/usr/bin/env python3
"""
Script to add YouTube recipes to the database.
"""

import sys
import os
import json
import requests

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.yt_ingest import get_transcript
from backend.extractors import extract_recipe
from backend.state import get_session_manager

# YouTube URLs provided by the user
YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=-fMcKbeqX4g&pp=ygUZRmx1ZmZ5IEJsdWViZXJyeSBQYW5jYWtlcw%3D%3D",
    "https://www.youtube.com/watch?v=mhDJNfV7hjk&pp=ygUOY29va2luZyB2aWRlb3M%3D"
]

BASE_URL = "http://localhost:8000"

def ingest_video(youtube_url):
    """Ingest a YouTube video and get transcript."""
    print(f"Ingesting video: {youtube_url}")
    try:
        result = get_transcript(youtube_url)
        if result:
            print(f"✓ Successfully ingested: {result['title']}")
            return result
        else:
            print("✗ Failed to ingest video")
            return None
    except Exception as e:
        print(f"✗ Error ingesting video: {e}")
        return None

def extract_recipe_from_transcript(transcript_data):
    """Extract recipe from transcript."""
    print("Extracting recipe from transcript...")
    try:
        recipe = extract_recipe(transcript_data["text"], model="gemma2")
        if recipe:
            print("✓ Successfully extracted recipe")
            # Add title from video if not in recipe
            if "title" not in recipe:
                recipe["title"] = transcript_data["title"]
            return recipe
        else:
            print("✗ Failed to extract recipe")
            return None
    except Exception as e:
        print(f"✗ Error extracting recipe: {e}")
        return None

def save_recipe_to_db(title, description, recipe):
    """Save recipe to database via API."""
    print("Saving recipe to database...")
    try:
        response = requests.post(
            f"{BASE_URL}/recipes",
            json={
                "title": title,
                "description": description,
                "recipe": recipe
            }
        )
        
        if response.status_code == 200:
            saved_recipe = response.json()
            print(f"✓ Recipe saved with ID: {saved_recipe['id']}")
            return saved_recipe
        else:
            print(f"✗ Failed to save recipe: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error saving recipe: {e}")
        return None

def main():
    """Main function to process YouTube recipes."""
    print("=" * 60)
    print("ADDING YOUTUBE RECIPES TO DATABASE")
    print("=" * 60)
    
    # Check if API is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("✗ API is not running. Please start the backend server:")
            print("  cd backend && uvicorn app:app --reload --port 8000")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Please start the backend server:")
        print("  cd backend && uvicorn app:app --reload --port 8000")
        return
    
    saved_recipes = []
    
    for i, url in enumerate(YOUTUBE_URLS, 1):
        print(f"\n[{i}/{len(YOUTUBE_URLS)}] Processing: {url}")
        
        # Step 1: Ingest video
        transcript_data = ingest_video(url)
        if not transcript_data:
            continue
            
        # Step 2: Extract recipe
        recipe = extract_recipe_from_transcript(transcript_data)
        if not recipe:
            continue
            
        # Step 3: Save to database
        title = recipe.get("title", transcript_data["title"])
        description = f"Recipe extracted from YouTube video: {transcript_data['title']}"
        
        saved_recipe = save_recipe_to_db(title, description, recipe)
        if saved_recipe:
            saved_recipes.append(saved_recipe)
            
        # Add a small delay between processing videos
        if i < len(YOUTUBE_URLS):
            import time
            time.sleep(2)
    
    print("\n" + "=" * 60)
    if saved_recipes:
        print(f"✓ Successfully saved {len(saved_recipes)} recipes to database")
        print("\nSaved recipes:")
        for recipe in saved_recipes:
            print(f"  - {recipe['title']} (ID: {recipe['id']})")
    else:
        print("✗ No recipes were saved")
    print("=" * 60)

if __name__ == "__main__":
    main()