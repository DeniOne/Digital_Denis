from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from core.auth import get_current_user
from voice.tts import tts_client
from voice.cache import audio_cache
from pydantic import BaseModel

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None

@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    user=Depends(get_current_user)
):
    """
    Generate speech from text and stream response.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")

    # Check cache (simplified for non-streaming)
    # Note: For streaming, we usually bypass cache or cache the whole stream after first run
    
    async def stream_generator():
        try:
            async for chunk in tts_client.synthesize_stream(
                text=request.text, 
                voice_id=request.voice_id
            ):
                yield chunk
        except Exception as e:
            print(f"TTS Streaming Error: {e}")
            # We can't easily change status code once streaming starts
            pass

    return StreamingResponse(
        stream_generator(), 
        media_type="audio/mpeg"
    )
