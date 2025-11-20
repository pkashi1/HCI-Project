import sys
import re
import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable, NoTranscriptFound
import yt_dlp
from pytube import YouTube

def download_video(video_id, folder_name="vids"):
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': f'{folder_name}/video.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return f"{folder_name}/video.mp4"

if len(sys.argv) > 1:
    input_arg = sys.argv[1]
    # Extract video ID from URL or use as-is if already an ID
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', input_arg)
    video_id = match.group(1) if match else input_arg
else:
    print("Error: Please provide a YouTube URL or video ID.")
    print('Example: python3 extract.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"')
    sys.exit(1)

print(f"Attempting to fetch transcript for video ID: {video_id}")

try:
    # Create API instance and fetch transcript
    api = YouTubeTranscriptApi()
    transcript_data = api.fetch(video_id, languages=['en'])

    # Get video title and duration
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        title = re.sub(r'[<>:"/\\|?*]', '_', info['title'])
        duration = info.get('duration', 0)
    
    # Create folder for images
    folder_name = f"{title}_cooking_stages"
    os.makedirs(folder_name, exist_ok=True)
    
    # Extract frames at regular intervals
    frame_opts = {
        'format': 'best[height<=720]',
        'outtmpl': f'{folder_name}/frame_%(autonumber)02d.%(ext)s',
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writethumbnail': False,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'jpg',
        }, {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'none',
        }],
        'postprocessor_args': {
            'ffmpeg': ['-vf', f'fps=1/{max(1, duration//10)}', '-frames:v', '10']
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(frame_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        print(f"\nExtracted cooking stage images to {folder_name}/")
    except Exception as e:
        print(f"\nCould not extract images: {e}")
    
    # Combine transcript into a single string
    full_transcript = " ".join([item.text for item in transcript_data.snippets])
    
    print("\n--- Transcript ---")
    print(full_transcript)
    print("------------------")
    
    filename = f"{title}_transcript.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_transcript)
        
    print(f"\nSuccessfully saved transcript to {filename}")

except TranscriptsDisabled:
    print(f"\nERROR: Transcripts are disabled for video ID: {video_id}")
except VideoUnavailable:
    print(f"\nERROR: Video {video_id} is unavailable (it may be private or deleted).")
except NoTranscriptFound:
    print(f"\nERROR: No transcript was found for the language 'en'.")
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        print("Available languages for this video are:")
        for transcript in transcript_list:
            print(f"- {transcript.language_code} ({transcript.language})")
    except Exception:
        print("Could not retrieve available languages.")
except Exception as e:
    # This will catch other errors, like an invalid video ID
    print(f"\nAn unexpected error occurred: {e}")