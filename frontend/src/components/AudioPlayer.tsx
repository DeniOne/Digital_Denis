'use client';

import React from 'react';
import { Volume2, Square, Loader2 } from 'lucide-react';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';
import { cn } from '@/lib/utils';

interface AudioPlayerProps {
    text: string;
    className?: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ text, className }) => {
    const { isPlaying, isLoading, playTTS, stop } = useAudioPlayer();

    const handleToggle = () => {
        if (isPlaying) {
            stop();
        } else {
            const voiceId = localStorage.getItem('dd-voice-id') || undefined;
            playTTS(text, voiceId);
        }
    };

    return (
        <button
            onClick={handleToggle}
            className={cn(
                "flex items-center gap-2 px-2 py-1 rounded-md transition-all",
                isPlaying ? "bg-blue-600/20 text-blue-400" : "bg-white/5 text-zinc-500 hover:text-white hover:bg-white/10",
                className
            )}
            disabled={isLoading}
            title={isPlaying ? "Stop" : "Read Aloud"}
        >
            {isLoading ? (
                <Loader2 className="animate-spin" size={12} />
            ) : isPlaying ? (
                <Square size={12} fill="currentColor" />
            ) : (
                <Volume2 size={12} />
            )}
            <span className="text-[10px] uppercase tracking-widest font-bold">
                {isLoading ? "Generating..." : isPlaying ? "Playing" : "Read"}
            </span>
        </button>
    );
};
