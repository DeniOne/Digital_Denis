import httpx
from typing import AsyncGenerator, Optional
from core.config import settings

class TTSClient:
    """
    Client for ElevenLabs Text-to-Speech API.
    """
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = settings.elevenlabs_voice_id
        self.default_model_id = settings.elevenlabs_model_id

    async def synthesize_stream(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize text to speech and yield audio chunks.
        """
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set")

        voice = voice_id or self.default_voice_id
        model = model_id or self.default_model_id
        
        url = f"{self.base_url}/text-to-speech/{voice}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    raise Exception(f"ElevenLabs API error ({response.status_code}): {error_detail.decode()}")
                
                async for chunk in response.aiter_bytes():
                    yield chunk

tts_client = TTSClient()
