"""
Database seeding script.
Ingests YouTube videos, extracts recipes, and saves them to the SQLite database.
"""
import sys
import os
from typing import List

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yt_ingest import get_transcript
from extractors import extract_recipe
from state import SessionManager

# --- CONFIGURATION ---
# Database path - using runtime/HCIDB.sqlite
import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime", "HCIDB.sqlite")

# List of YouTube URLs to process
# Replace these with your 10 cooking video URLs
VIDEO_URLS = [
    # Example:
    #  "https://www.youtube.com/watch?v=a03U45jFxOI",
    "https://www.youtube.com/watch?v=a03U45jFxOI&pp=ygUOQnV0dGVyIGNoaWNrZW4%3D",
    "https://www.youtube.com/watch?v=6XlMguO9r-M&pp=ygUQY2hpY2tlbiBiaXJpeWFuYQ%3D%3D",
    "https://www.youtube.com/watch?v=mhDJNfV7hjk&pp=ygUGcmFtc2F5",
    "https://www.youtube.com/shorts/mYtdXVVxohI",
    "https://www.youtube.com/shorts/XOjD3Rc8PGw",
    "https://www.youtube.com/watch?v=urECpujNgcM",
    "https://www.youtube.com/watch?v=oFSgLH8AN7w",
    "https://www.youtube.com/watch?v=_tx6VaBC_Bc",
    "https://www.youtube.com/watch?v=UhByCuLYt2g",
    "https://www.youtube.com/watch?v=evKMiaVfjvI",
    "https://www.youtube.com/watch?v=iM3ArXFgaYA&pp=ygUMY2hlZXNlIHBpenph",
    "https://www.youtube.com/watch?v=7wsa7XsaHQo",
    

]

def seed_database(urls: List[str], db_path: str = DB_PATH):
    """
    Process a list of YouTube URLs and populate the database.
    
    Args:
        urls: List of YouTube video URLs
        db_path: Path to the SQLite database file
    """
    print(f"Starting database seed with {len(urls)} videos...")
    print(f"Using database: {db_path}")
    
    # Create session manager directly with custom database path
    manager = SessionManager(db_path=db_path)
    
    success_count = 0
    
    for i, url in enumerate(urls):
        print(f"\n[{i+1}/{len(urls)}] Processing: {url}")
        
        try:
            # 1. Get Transcript
            print("  - Fetching transcript...")
            transcript_data = get_transcript(url)
            
            if not transcript_data:
                print(f"  - ⚠ Skipping: No transcript found for {url}")
                continue
            
            video_title = transcript_data['title']
            print(f"  - Video Title: {video_title}")
            
            # 2. Extract Recipe
            print("  - Extracting recipe (this may take a moment)...")
            recipe = extract_recipe(transcript_data['text'])
            
            if not recipe:
                print(f"  - ⚠ Skipping: Failed to extract recipe for {video_title}")
                continue
            
            # Ensure title is set
            if 'title' not in recipe or not recipe['title']:
                recipe['title'] = video_title
            
            # Add metadata to recipe
            recipe['image'] = transcript_data.get('thumbnail', '')
            recipe['video_url'] = transcript_data.get('url', url)
            
            # 3. Save to Database
            print(f"  - Saving to database...")
            
            # Create a description if missing
            description = recipe.get('description', "")
            if not description:
                # Try to construct a brief description
                item_count = len(recipe.get('ingredients', {}))
                step_count = len(recipe.get('steps', []))
                description = f"A delicious recipe for {recipe['title']} with {step_count} steps."
            
            # Save using SessionManager
            recipe_id = manager.save_recipe(
                title=recipe['title'],
                description=description,
                recipe=recipe
            )
            
            print(f"  - ✓ Success! Saved as Recipe ID: {recipe_id}")
            success_count += 1
            
        except Exception as e:
            print(f"  - ✗ Error processing {url}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*50)
    print(f"Seeding complete!")
    print(f"Successfully added {success_count} out of {len(urls)} recipes.")
    print(f"Database: {db_path}")
    print("="*50)

if __name__ == "__main__":
    # Check if URLs are provided in the script
    if VIDEO_URLS:
        seed_database(VIDEO_URLS, DB_PATH)
    else:
        print("No URLs defined in VIDEO_URLS.")
        print("Please edit this file and add your YouTube URLs to the VIDEO_URLS list.")
        print("Or pass URLs as command line arguments.")
        
        # Allow passing URLs as arguments
        if len(sys.argv) > 1:
            cmd_urls = sys.argv[1:]
            seed_database(cmd_urls, DB_PATH)