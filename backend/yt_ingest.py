"""
YouTube transcript ingestion module.
Extracts transcripts from YouTube videos with fallback to audio download + ASR.
"""
import re
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable, NoTranscriptFound
import yt_dlp


def extract_video_id(url_or_id: str) -> str:
    """
    Extract video ID from YouTube URL or return as-is if already an ID.
    
    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - VIDEO_ID (11 characters)
    """
    match = re.search(r'(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})', url_or_id)
    return match.group(1) if match else url_or_id


def get_video_metadata(video_id: str) -> Dict[str, str]:
    """Fetch video title and thumbnail using yt-dlp."""
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            # Sanitize title for filenames
            title = re.sub(r'[<>:"/\\|?*]', '_', info['title'])
            return {
                'title': title,
                'thumbnail': info.get('thumbnail', ''),
                'url': info.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}")
            }
    except Exception as e:
        print(f"Could not fetch metadata: {e}")
        return {
            'title': video_id,
            'thumbnail': '',
            'url': f"https://www.youtube.com/watch?v={video_id}"
        }


def get_transcript_from_api(video_id: str, languages: List[str] = None) -> Optional[Dict]:
    """
    Try to get transcript using youtube-transcript-api.
    
    Returns:
        Dict with 'text', 'snippets', 'title', 'thumbnail', 'url'
        None if transcript unavailable
    """
    if languages is None:
        languages = ['en']
    
    try:
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=languages)
        
        # Get metadata
        metadata = get_video_metadata(video_id)
        
        # Extract snippets with timestamps
        snippets = [{
            'text': item.text,
            'start': item.start,
            'duration': item.duration
        } for item in transcript_data.snippets]
        
        # Combine into full text
        full_text = " ".join([item['text'] for item in snippets])
        
        return {
            'video_id': video_id,
            'title': metadata['title'],
            'thumbnail': metadata['thumbnail'],
            'url': metadata['url'],
            'text': full_text,
            'snippets': snippets,
            'source': 'api'
        }
        
    except TranscriptsDisabled:
        print(f"Transcripts are disabled for video: {video_id}")
        return None
    except VideoUnavailable:
        print(f"Video unavailable: {video_id}")
        return None
    except NoTranscriptFound:
        print(f"No transcript found for languages: {languages}")
        return None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None


def get_transcript_from_audio(video_id: str) -> Optional[Dict]:
    """
    Fallback: Download audio and transcribe with faster-whisper.
    
    NOTE: This requires faster-whisper to be installed.
    Implementation pending - will be added in next step.
    """
    # TODO: Implement audio download + ASR fallback
    print("Audio fallback not yet implemented")
    return None


def get_transcript(url_or_id: str) -> Optional[Dict]:
    """
    Main entry point: Get transcript from YouTube video.
    
    Args:
        url_or_id: YouTube URL or video ID
        
    Returns:
        Dict with transcript data or None if failed
    """
    video_id = extract_video_id(url_or_id)
    print(f"Processing video ID: {video_id}")
    
    # Try API first (fast and free)
    result = get_transcript_from_api(video_id)
    
    if result:
        return result
    
    # Fallback to audio download + ASR
    print("Trying audio download fallback...")
    result = get_transcript_from_audio(video_id)
    
    return result


# CLI interface (for testing)
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python yt_ingest.py <youtube_url_or_id>")
        print('Example: python yt_ingest.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"')
        sys.exit(1)
    
    result = get_transcript(sys.argv[1])
    
    if result:
        print("\n--- Transcript Retrieved ---")
        print(f"Title: {result['title']}")
        print(f"Source: {result['source']}")
        print(f"Length: {len(result['text'])} characters")
        print(f"Segments: {len(result['snippets'])}")
        print("\n--- First 500 characters ---")
        print(result['text'][:500])
        
        # Save to file
        filename = f"{result['title']}_transcript.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result['text'])
        print(f"\nSaved to: {filename}")
    else:
        print("\nFailed to retrieve transcript")
        sys.exit(1)