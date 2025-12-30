import io
from groq import AsyncGroq
from core.config import settings

# Initialize Groq client
client = AsyncGroq(api_key=settings.groq_api_key)

async def transcribe_chunk(audio_bytes: bytes, language: str = "ru") -> str:
    """
    Transcribe audio chunk using Groq Whisper.
    
    Args:
        audio_bytes: Raw audio bytes buffer
        language: Language code (default: ru)
        
    Returns:
        Transcribed text
    """
    if not audio_bytes:
        return ""
        
    try:
        # Create a file-like object with a name and content
        # Groq needs a filename to determine format, usually .m4a, .mp3, .wav
        # We assume the client sends something compatible or raw that we treat as wav/webm
        # If it's pure raw PCM, it might need headers. 
        # For this MVP, we assume client sends a valid container format (e.g. webm/opus) 
        # or we rely on Groq's ability to handle it.
        # Naming it 'audio.webm' usually works for web audio streams.
        
        file_obj = ("audio.webm", audio_bytes, "audio/webm")
        
        transcription = await client.audio.transcriptions.create(
            file=file_obj,
            model=settings.groq_whisper_model,
            language=language,
            response_format="json"
        )
        
        return transcription.text.strip()
        
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""
