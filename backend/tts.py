"""
Text-to-Speech (TTS) using Piper.
Converts text to natural-sounding speech for voice responses.
"""
import os
import subprocess
import tempfile
from typing import Optional
import wave


class TTSEngine:
    """Text-to-speech engine using Piper."""
    
    def __init__(self, voice_path: Optional[str] = None):
        """
        Initialize TTS engine.
        
        Args:
            voice_path: Path to Piper voice model (.onnx file)
                       If None, will look in runtime/voices/ directory
        """
        self.voice_path = voice_path or self._find_voice()
        
        if not self.voice_path or not os.path.exists(self.voice_path):
            raise FileNotFoundError(
                "No Piper voice model found. Please download a voice:\n"
                "1. Visit: https://github.com/rhasspy/piper/releases\n"
                "2. Download a voice (e.g., en_US-amy-low.onnx + .json)\n"
                "3. Place in runtime/voices/ directory"
            )
        
        print(f"Using TTS voice: {os.path.basename(self.voice_path)}")
        
        # Check if piper is installed
        if not self._check_piper():
            raise RuntimeError(
                "Piper not found. Install with:\n"
                "pip install piper-tts"
            )
    
    def _find_voice(self) -> Optional[str]:
        """Find the first available Piper voice."""
        voice_dirs = [
            "runtime/voices",
            "../runtime/voices",
            os.path.expanduser("~/.local/share/piper/voices")
        ]
        
        for voice_dir in voice_dirs:
            if os.path.exists(voice_dir):
                for file in os.listdir(voice_dir):
                    if file.endswith(".onnx"):
                        return os.path.join(voice_dir, file)
        
        return None
    
    def _check_piper(self) -> bool:
        """Check if piper command is available."""
        try:
            subprocess.run(["piper", "--version"], 
                          capture_output=True, 
                          check=True,
                          timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def synthesize(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize
            output_path: Optional path to save WAV file
                        If None, uses temporary file
            
        Returns:
            Audio data as bytes (WAV format)
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Create output file path
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_path = tmp.name
            tmp.close()
            cleanup = True
        else:
            cleanup = False
        
        try:
            # Run piper command
            # piper reads from stdin and writes to file specified by -f
            process = subprocess.run(
                ["piper", "-m", self.voice_path, "-f", output_path],
                input=text.encode('utf-8'),
                capture_output=True,
                check=True,
                timeout=30
            )
            
            # Read the generated audio
            with open(output_path, "rb") as f:
                audio_bytes = f.read()
            
            return audio_bytes
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("TTS synthesis timed out")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper error: {e.stderr.decode()}")
        finally:
            # Clean up temp file if we created it
            if cleanup and os.path.exists(output_path):
                os.remove(output_path)
    
    def synthesize_to_file(self, text: str, output_path: str) -> str:
        """
        Synthesize text and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save WAV file
            
        Returns:
            Path to saved file
        """
        audio_bytes = self.synthesize(text, output_path=output_path)
        return output_path
    
    def get_audio_info(self, audio_bytes: bytes) -> dict:
        """
        Get information about WAV audio.
        
        Args:
            audio_bytes: WAV audio data
            
        Returns:
            Dict with sample_rate, channels, duration
        """
        # Save to temp file to read with wave module
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            with wave.open(tmp_path, 'rb') as wf:
                info = {
                    'sample_rate': wf.getframerate(),
                    'channels': wf.getnchannels(),
                    'sample_width': wf.getsampwidth(),
                    'n_frames': wf.getnframes(),
                    'duration': wf.getnframes() / wf.getframerate()
                }
            return info
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# Alternative: pyttsx3 (fallback if Piper not available)
class PyTTSX3Engine:
    """Fallback TTS using pyttsx3 (more robotic but easier to install)."""
    
    def __init__(self):
        """Initialize pyttsx3 engine."""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            self.engine.setProperty('rate', 150)  # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
            
            # Try to use a better voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voices (often clearer)
                for voice in voices:
                    if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            print("Using pyttsx3 TTS (fallback)")
        except Exception as e:
            raise RuntimeError(f"Could not initialize pyttsx3: {e}")
    
    def synthesize(self, text: str, output_path: Optional[str] = None) -> bytes:
        """Synthesize text to speech."""
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_path = tmp.name
            tmp.close()
            cleanup = True
        else:
            cleanup = False
        
        try:
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            
            with open(output_path, "rb") as f:
                audio_bytes = f.read()
            
            return audio_bytes
        finally:
            if cleanup and os.path.exists(output_path):
                os.remove(output_path)


# Global TTS engine
_tts_engine = None


def get_tts_engine(use_piper: bool = True) -> TTSEngine:
    """
    Get or create global TTS engine.
    
    Args:
        use_piper: Try to use Piper first (better quality)
        
    Returns:
        TTS engine instance
    """
    global _tts_engine
    
    if _tts_engine is None:
        if use_piper:
            try:
                _tts_engine = TTSEngine()
            except (FileNotFoundError, RuntimeError) as e:
                print(f"Warning: {e}")
                print("Falling back to pyttsx3...")
                _tts_engine = PyTTSX3Engine()
        else:
            _tts_engine = PyTTSX3Engine()
    
    return _tts_engine


def synthesize(text: str) -> bytes:
    """
    Convenience function to synthesize text.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Audio bytes (WAV format)
    """
    engine = get_tts_engine()
    return engine.synthesize(text)


def synthesize_to_file(text: str, output_path: str) -> str:
    """
    Convenience function to synthesize and save to file.
    
    Args:
        text: Text to convert to speech
        output_path: Path to save WAV file
        
    Returns:
        Path to saved file
    """
    engine = get_tts_engine()
    audio_bytes = engine.synthesize(text, output_path=output_path)
    return output_path


# CLI test
if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("TTS ENGINE TEST")
    print("="*60)
    
    if len(sys.argv) < 2:
        text = "Hello! I'm your cooking assistant. Let me help you make something delicious today."
        print(f"\nUsage: python tts.py <text> [output.wav]")
        print(f"\nNo text provided, using default:")
        print(f'"{text}"')
    else:
        text = " ".join(sys.argv[1:])
    
    output_file = "test_output.wav"
    if len(sys.argv) > 2 and sys.argv[-1].endswith('.wav'):
        output_file = sys.argv[-1]
        text = " ".join(sys.argv[1:-1])
    
    print(f"\nSynthesizing: '{text}'")
    print(f"Output file: {output_file}")
    
    try:
        engine = get_tts_engine()
        audio_bytes = engine.synthesize(text, output_path=output_file)
        
        print(f"\n✓ Generated {len(audio_bytes)} bytes of audio")
        print(f"✓ Saved to: {output_file}")
        
        # Get audio info
        if isinstance(engine, TTSEngine):
            info = engine.get_audio_info(audio_bytes)
            print(f"\nAudio info:")
            print(f"  Sample rate: {info['sample_rate']} Hz")
            print(f"  Channels: {info['channels']}")
            print(f"  Duration: {info['duration']:.2f} seconds")
        
        print("\n✓ TTS test completed successfully!")
        print(f"\nPlay with: afplay {output_file}  (macOS)")
        print(f"       or: aplay {output_file}   (Linux)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)