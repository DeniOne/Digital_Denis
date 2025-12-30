import { useState, useCallback, useRef, useEffect } from 'react';
import { streamPlayer } from '../lib/audio/player';

export function useAudioPlayer() {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const playTTS = useCallback(async (text: string, voiceId?: string) => {
        setIsLoading(true);

        try {
            // We will use a POST request to get the audio stream URL or directly stream.
            // For standard <audio> tag, we might need a GET endpoint or use Blob URL.
            // But ElevenLabs returns a stream, and browser <audio> supports streaming MP3.

            const response = await fetch('/api/v1/voice/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Note: Token might be needed if not using cookie auth
                },
                body: JSON.stringify({ text, voice_id: voiceId })
            });

            if (!response.ok) throw new Error('TTS request failed');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            setIsLoading(false);
            setIsPlaying(true);

            streamPlayer.play(url, () => {
                setIsPlaying(false);
                URL.revokeObjectURL(url);
            });

        } catch (error) {
            console.error('Audio playback error:', error);
            setIsLoading(false);
            setIsPlaying(false);
        }
    }, []);

    const stop = useCallback(() => {
        streamPlayer.stop();
        setIsPlaying(false);
    }, []);

    return { isPlaying, isLoading, playTTS, stop };
}
