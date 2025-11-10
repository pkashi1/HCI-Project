"""
Automatic Speech Recognition (ASR) using faster-whisper.
Converts audio to text for voice commands.
"""
import os
import tempfile
from typing import Optional, List, Dict
from faster_whisper import WhisperModel
import numpy as np


class ASREngine:
    """Speech-to-text engine using faster-whisper."""
    
    def __init__(self, model_size: str = "small.en", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize ASR engine.
        
        Args:
            model_size: Whisper model size (tiny.en, base.en, small.en, medium.en, large)
            device: "cpu" or "cuda"
            compute_type: "int8", "int8_float16", "float16", "float32"
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        print(f"Initializing ASR with model: {model_size} on {device}")
    
    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            print(f"Loading Whisper model: {self.model_size}...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            print("✓ ASR model loaded")
    
    def transcribe_file(self, audio_path: str, language: str = "en") -> Dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (wav, mp3, m4a, etc.)
            language: Language code (default: "en")
            
        Returns:
            Dict with 'text' and 'segments' (with timestamps)
        """
        self._load_model()
        
        print(f"Transcribing audio file: {audio_path}")
        
        # Transcribe with word-level timestamps
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Voice Activity Detection to filter silence
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Collect segments
        text_segments = []
        full_text = []
        
        for segment in segments:
            text_segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
            full_text.append(segment.text.strip())
        
        result = {
            'text': ' '.join(full_text),
            'segments': text_segments,
            'language': info.language,
            'duration': info.duration
        }
        
        print(f"✓ Transcribed: {len(result['text'])} characters")
        return result
    
    def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav", language: str = "en") -> Dict:
        """
        Transcribe audio from bytes.
        
        Args:
            audio_bytes: Audio data as bytes
            format: Audio format (wav, mp3, m4a, etc.)
            language: Language code
            
        Returns:
            Dict with 'text' and 'segments'
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            result = self.transcribe_file(tmp_path, language=language)
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def transcribe_numpy(self, audio: np.ndarray, sample_rate: int, language: str = "en") -> Dict:
        """
        Transcribe audio from numpy array.
        
        Args:
            audio: Audio samples as numpy array (float32, -1.0 to 1.0)
            sample_rate: Sample rate in Hz
            language: Language code
            
        Returns:
            Dict with 'text' and 'segments'
        """
        # Save to temporary WAV file
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            sf.write(tmp_path, audio, sample_rate)
            result = self.transcribe_file(tmp_path, language=language)
            return result
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def transcribe_streaming(self, audio_chunks: List[np.ndarray], sample_rate: int, language: str = "en"):
        """
        Transcribe streaming audio in chunks.
        
        Args:
            audio_chunks: List of audio chunk arrays
            sample_rate: Sample rate in Hz
            language: Language code
            
        Yields:
            Transcription results as they become available
        """
        # Concatenate chunks
        full_audio = np.concatenate(audio_chunks)
        
        # For now, just transcribe the full audio
        # Real streaming would need VAD and chunking logic
        result = self.transcribe_numpy(full_audio, sample_rate, language)
        yield result


# Global ASR engine instance
_asr_engine = None


def get_asr_engine(model_size: str = "small.en") -> ASREngine:
    """
    Get or create global ASR engine instance.
    
    Args:
        model_size: Whisper model size
        
    Returns:
        ASREngine instance
    """
    global _asr_engine
    if _asr_engine is None:
        _asr_engine = ASREngine(model_size=model_size)
    return _asr_engine


def transcribe_audio(audio_path: str, language: str = "en") -> str:
    """
    Convenience function to transcribe audio file.
    
    Args:
        audio_path: Path to audio file
        language: Language code
        
    Returns:
        Transcribed text
    """
    engine = get_asr_engine()
    result = engine.transcribe_file(audio_path, language=language)
    return result['text']


def transcribe_bytes(audio_bytes: bytes, format: str = "wav", language: str = "en") -> str:
    """
    Convenience function to transcribe audio bytes.
    
    Args:
        audio_bytes: Audio data
        format: Audio format
        language: Language code
        
    Returns:
        Transcribed text
    """
    engine = get_asr_engine()
    result = engine.transcribe_bytes(audio_bytes, format=format, language=language)
    return result['text']


# CLI test
if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("ASR ENGINE TEST")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python asr.py <audio_file>")
        print("Example: python asr.py test_audio.wav")
        print("\nSupported formats: wav, mp3, m4a, flac, ogg")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not os.path.exists(audio_file):
        print(f"Error: File not found: {audio_file}")
        sys.exit(1)
    
    print(f"\nTranscribing: {audio_file}")
    print("This may take a moment on first run (downloading model)...\n")
    
    try:
        engine = ASREngine(model_size="small.en")
        result = engine.transcribe_file(audio_file)
        
        print("\n--- TRANSCRIPTION RESULT ---")
        print(f"Text: {result['text']}")
        print(f"\nLanguage: {result['language']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print(f"Segments: {len(result['segments'])}")
        
        if result['segments']:
            print("\n--- SEGMENTS (with timestamps) ---")
            for seg in result['segments'][:5]:  # Show first 5
                print(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
            
            if len(result['segments']) > 5:
                print(f"... and {len(result['segments']) - 5} more segments")
        
        print("\n✓ ASR test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)