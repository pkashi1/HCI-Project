"""
End-to-end test: YouTube URL → Transcript → Recipe JSON
"""
import sys
import json
from yt_ingest import get_transcript
from extractors import extract_recipe, print_recipe_summary


def test_full_pipeline(url_or_id: str, model: str = "gemma3:1b"):
    """
    Test complete pipeline from YouTube to structured recipe.
    
    Args:
        url_or_id: YouTube URL or video ID
        model: LLM model to use for extraction
    """
    print("="*60)
    print("RECIPE EXTRACTION PIPELINE TEST")
    print("="*60)
    
    # Step 1: Get transcript
    print("\n[1/2] Fetching transcript from YouTube...")
    transcript_data = get_transcript(url_or_id)
    
    if not transcript_data:
        print("✗ Failed to get transcript")
        return None
    
    print(f"✓ Got transcript: {len(transcript_data['text'])} characters")
    print(f"   Title: {transcript_data['title']}")
    print(f"   Segments: {len(transcript_data['snippets'])}")
    
    # Save transcript
    transcript_file = f"{transcript_data['title']}_transcript.txt"
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(transcript_data['text'])
    print(f"   Saved to: {transcript_file}")
    
    # Step 2: Extract recipe
    print(f"\n[2/2] Extracting recipe using {model}...")
    recipe = extract_recipe(transcript_data['text'], model=model)
    
    if not recipe:
        print("✗ Failed to extract recipe")
        return None
    
    # Add metadata
    recipe['source_video_id'] = transcript_data['video_id']
    recipe['source_title'] = transcript_data['title']
    
    # Print summary
    print_recipe_summary(recipe)
    
    # Save recipe JSON
    recipe_file = f"{transcript_data['title']}_recipe.json"
    with open(recipe_file, 'w', encoding='utf-8') as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved recipe JSON to: {recipe_file}")
    
    return recipe


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_extract.py <youtube_url> [model]")
        print("\nExamples:")
        print('  python test_extract.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"')
        print('  python test_extract.py "dQw4w9WgXcQ" llama3.2:3b-instruct')
        print("\nAvailable models:")
        print("  - phi4 (default, recommended)")
        print("  - llama3.2:3b-instruct")
        sys.exit(1)
    
    url_or_id = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "phi4"
    
    try:
        recipe = test_full_pipeline(url_or_id, model)
        
        if recipe:
            print("\n" + "="*60)
            print("✓ SUCCESS! Recipe extracted and saved.")
            print("="*60)
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("✗ FAILED: Could not extract recipe")
            print("="*60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()