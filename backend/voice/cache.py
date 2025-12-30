import hashlib
import os
from pathlib import Path
from typing import Optional

class AudioCache:
    """
    Simple file-based cache for generated audio.
    """
    def __init__(self, cache_dir: str = "cache/audio"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_hash(self, text: str, voice_id: str) -> str:
        """Generate a unique hash for text and voice combo."""
        return hashlib.md5(f"{text}:{voice_id}".encode()).hexdigest()

    def get(self, text: str, voice_id: str) -> Optional[bytes]:
        """Retrieve audio from cache if exists."""
        file_path = self.cache_dir / f"{self._get_hash(text, voice_id)}.mp3"
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def set(self, text: str, voice_id: str, audio_data: bytes):
        """Save audio to cache."""
        file_path = self.cache_dir / f"{self._get_hash(text, voice_id)}.mp3"
        file_path.write_bytes(audio_data)

audio_cache = AudioCache()
