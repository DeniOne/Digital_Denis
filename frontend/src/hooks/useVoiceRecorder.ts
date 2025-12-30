import { useState, useRef, useCallback, useEffect } from 'react';
import { AudioRecorder } from '../lib/audio/recorder';

export function useVoiceRecorder(onDataAvailable: (blob: Blob) => void) {
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const recorderRef = useRef<AudioRecorder | null>(null);

    useEffect(() => {
        recorderRef.current = new AudioRecorder();
        return () => {
            recorderRef.current?.stop();
        };
    }, []);

    const startRecording = useCallback(async () => {
        setError(null);
        try {
            await recorderRef.current?.start({
                onDataAvailable,
            });
            setIsRecording(true);
        } catch (err) {
            setError('Could not access microphone');
            setIsRecording(false);
        }
    }, [onDataAvailable]);

    const stopRecording = useCallback(() => {
        recorderRef.current?.stop();
        setIsRecording(false);
    }, []);

    const toggleRecording = useCallback(() => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }, [isRecording, startRecording, stopRecording]);

    return {
        isRecording,
        error,
        startRecording,
        stopRecording,
        toggleRecording,
    };
}
