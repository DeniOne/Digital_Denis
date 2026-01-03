'use client';

import React, { useState, useEffect } from 'react';
import { Settings, Volume2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface VoiceOption {
    id: string;
    name: string;
    preview_url?: string;
}

const DEFAULT_VOICES: VoiceOption[] = [
    { id: 'pMsXg9Y9C95gIn6ycYid', name: 'Den (Deep)' },
    { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Bella (Soft)' },
    { id: 'ErXwVqcDCOwaoxvTidca', name: 'Antoni (Professional)' },
];

export const VoiceSettings: React.FC = () => {
    const [selectedVoice, setSelectedVoice] = useState(DEFAULT_VOICES[0].id);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        // Safe access to localStorage
        const saved = typeof window !== 'undefined' ? localStorage.getItem('dd-voice-id') : null;
        if (saved && saved !== selectedVoice) {
            setSelectedVoice(saved);
        }
    }, []);

    const handleSelect = (id: string) => {
        setSelectedVoice(id);
        localStorage.setItem('dd-voice-id', id);
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 rounded-lg bg-zinc-900 border border-white/5 hover:bg-zinc-800 transition-colors"
                title="Voice Settings"
            >
                <Volume2 size={18} className="text-zinc-400" />
            </button>

            {isOpen && (
                <div className="absolute bottom-full mb-2 right-0 w-48 p-3 rounded-xl bg-zinc-900 border border-white/10 shadow-2xl z-50">
                    <div className="flex items-center gap-2 mb-3 px-1">
                        <Settings size={14} className="text-zinc-500" />
                        <span className="text-[10px] uppercase tracking-widest font-bold text-zinc-500">Voice Profile</span>
                    </div>

                    <div className="space-y-1">
                        {DEFAULT_VOICES.map((voice) => (
                            <button
                                key={voice.id}
                                onClick={() => handleSelect(voice.id)}
                                className={cn(
                                    "w-full text-left px-3 py-2 rounded-lg text-xs transition-colors",
                                    selectedVoice === voice.id
                                        ? "bg-blue-600 text-white"
                                        : "text-zinc-400 hover:bg-white/5 hover:text-white"
                                )}
                            >
                                {voice.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
