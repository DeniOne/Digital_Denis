'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface TranscriptDisplayProps {
    text: string;
    isProcessing?: boolean;
    className?: string;
}

export const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({
    text,
    isProcessing,
    className
}) => {
    if (!text && !isProcessing) return null;

    return (
        <div className={cn(
            "p-4 rounded-2xl bg-zinc-900/80 backdrop-blur-md border border-white/5 shadow-2xl transition-all duration-500",
            text ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
            className
        )}>
            <div className="flex items-center gap-2 mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-[10px] uppercase tracking-widest font-bold text-zinc-500">Live Transcript</span>
            </div>

            <p className={cn(
                "text-sm leading-relaxed",
                text ? "text-zinc-200" : "text-zinc-500 italic"
            )}>
                {text || "Слушаю..."}
            </p>

            {isProcessing && !text && (
                <div className="mt-2 flex gap-1">
                    <div className="w-1 h-1 bg-zinc-600 rounded-full animate-bounce" />
                    <div className="w-1 h-1 bg-zinc-600 rounded-full animate-bounce [animation-delay:0.2s]" />
                    <div className="w-1 h-1 bg-zinc-600 rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
            )}
        </div>
    );
};
