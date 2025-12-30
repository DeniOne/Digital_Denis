import { useState, useEffect, useRef, useCallback } from 'react';

interface VoiceMessage {
    type: 'transcript' | 'status' | 'error';
    text?: string;
    state?: string;
    code?: number;
    message?: string;
    is_final?: boolean;
}

export function useVoiceWebSocket(onTranscript: (text: string, isFinal: boolean) => void) {
    const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
    const [processing, setProcessing] = useState(false);
    const socketRef = useRef<WebSocket | null>(null);

    const connect = useCallback((token: string) => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = process.env.NEXT_PUBLIC_API_URL?.replace('http://', '').replace('https://', '').split('/')[0] || 'localhost:8000';
        const url = `${protocol}//${host}/api/v1/ws/voice?token=${token}`;

        setStatus('connecting');
        const socket = new WebSocket(url);
        socketRef.current = socket;

        socket.onopen = () => {
            setStatus('connected');
            console.log('Voice WebSocket connected');
        };

        socket.onmessage = (event) => {
            try {
                const data: VoiceMessage = JSON.parse(event.data);
                if (data.type === 'transcript' && data.text) {
                    onTranscript(data.text, data.is_final || false);
                } else if (data.type === 'status') {
                    setProcessing(data.state === 'processing');
                } else if (data.type === 'error') {
                    console.error('Voice WS Error:', data.message);
                    setStatus('error');
                }
            } catch (err) {
                console.error('Failed to parse WS message:', err);
            }
        };

        socket.onclose = () => {
            setStatus('disconnected');
            setProcessing(false);
            socketRef.current = null;
        };

        socket.onerror = () => {
            setStatus('error');
        };
    }, [onTranscript]);

    const disconnect = useCallback(() => {
        socketRef.current?.close();
    }, []);

    const sendAudio = useCallback((blob: Blob) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            // Send as array buffer
            blob.arrayBuffer().then((buffer) => {
                socketRef.current?.send(buffer);
            });
        }
    }, []);

    useEffect(() => {
        return () => {
            socketRef.current?.close();
        };
    }, []);

    return {
        status,
        processing,
        connect,
        disconnect,
        sendAudio,
    };
}
