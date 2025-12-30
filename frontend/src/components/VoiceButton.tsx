'use client';

import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { useVoiceWebSocket } from '@/hooks/useVoiceWebSocket';

interface VoiceButtonProps {
    onTranscript: (text: string, isFinal: boolean) => void;
    className?: string;
    token?: string; // JWT token for WS
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({
    onTranscript,
    className,
    token = 'dummy-dev-token' // Fallback for dev
}) => {
    const { status, processing, connect, disconnect, sendAudio } = useVoiceWebSocket(onTranscript);
    const { isRecording, toggleRecording, error } = useVoiceRecorder(sendAudio);

    useEffect(() => {
        if (isRecording && status === 'disconnected') {
            connect(token);
        } else if (!isRecording && status === 'connected') {
            // We might want to keep it connected for a bit, but for now disconnect
            // Or just leave it for the next recording
        }
    }, [isRecording, status, connect, token]);

    const handleToggle = () => {
        if (status === 'error') {
            // Retry connection
            connect(token);
            return;
        }
        toggleRecording();
    };

    return (
        <div className={cn("relative flex flex-col items-center", className)}>
            <button
                onClick={handleToggle}
                className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg",
                    isRecording
                        ? "bg-red-500 hover:bg-red-600 scale-110"
                        : "bg-blue-600 hover:bg-blue-500",
                    status === 'connecting' && "opacity-50 cursor-wait",
                    status === 'error' && "bg-zinc-700 text-red-400"
                )}
                title={error || (isRecording ? "Stop Recording" : "Start Voice Assistant")}
            >
                {status === 'connecting' ? (
                    <Loader2 className="animate-spin" size={20} />
                ) : isRecording ? (
                    <div className="relative">
                        <MicOff size={20} />
                        <div className="absolute inset-0 w-full h-full bg-white/20 rounded-full animate-ping scale-150" />
                    </div>
                ) : (
                    <Mic size={20} />
                )}
            </button>

            {processing && (
                <div className="absolute -bottom-6 flex gap-1">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" />
                </div>
            )}

            {error && <span className="absolute -top-8 text-[10px] text-red-500 font-medium whitespace-nowrap">{error}</span>}
        </div>
    );
};
