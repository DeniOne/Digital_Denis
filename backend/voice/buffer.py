import io
from typing import Optional

class AudioBuffer:
    """
    Buffer for accumulating audio chunks before transcription.
    """
    def __init__(self, min_size_bytes: int = 32000): # ~1sec of 16k mono 16bit
        self.buffer = io.BytesIO()
        self.min_size_bytes = min_size_bytes
        self.current_size = 0

    def add(self, chunk: bytes):
        """Add binary chunk to buffer."""
        size = self.buffer.write(chunk)
        self.current_size += size

    def is_ready(self) -> bool:
        """Check if buffer has enough data to process."""
        return self.current_size >= self.min_size_bytes

    def flush(self) -> bytes:
        """Return accumulated bytes and reset buffer."""
        data = self.buffer.getvalue()
        
        # Reset
        self.buffer = io.BytesIO()
        self.current_size = 0
        
        return data

    def clear(self):
        """Clear buffer without returning."""
        self.buffer = io.BytesIO()
        self.current_size = 0
