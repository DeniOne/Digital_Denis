"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, BrainCircuit, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { messagesApi } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { VoiceButton } from "@/components/VoiceButton";
import { TranscriptDisplay } from "@/components/TranscriptDisplay";

export default function ChatPage() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<any[]>([]);
    const [liveTranscript, setLiveTranscript] = useState("");
    const { sessionId, setSessionId, isLoading, setIsLoading } = useAppStore();
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleTranscript = (text: string, isFinal: boolean) => {
        setLiveTranscript(text);
        if (isFinal) {
            setInput((prev) => prev + (prev ? " " : "") + text);
            // Auto-clear after a delay or keep it? 
            // Usually we clear live display when it's finalized into input
            setTimeout(() => setLiveTranscript(""), 2000);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLiveTranscript("");
        setIsLoading(true);

        try {
            const data = await messagesApi.send(input, sessionId || undefined);
            if (data.session_id) setSessionId(data.session_id);

            setMessages((prev) => [...prev, {
                role: "assistant",
                content: data.response,
                agent: data.agent,
                memory_saved: data.memory_saved
            }]);
        } catch (error) {
            console.error(error);
            setMessages((prev) => [...prev, {
                role: "assistant",
                content: "Произошла ошибка при связи с когнитивным слоем."
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full max-w-5xl mx-auto px-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                        <BrainCircuit className="text-blue-500" size={24} />
                    </div>
                    <div>
                        <h1 className="font-bold text-xl">Когнитивная сессия</h1>
                        <p className="text-zinc-500 text-xs uppercase tracking-widest font-medium">Digital Twin Sync Active</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.2 rounded-full bg-white/5 border border-white/5 text-[10px] font-bold text-zinc-400">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    SYSTEM_LANGUAGE: RU
                </div>
            </div>

            {/* Chat History */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto space-y-6 pr-4 custom-scrollbar mb-6 relative"
            >
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8">
                        <div className="w-20 h-20 rounded-3xl bg-blue-500/5 flex items-center justify-center mb-6">
                            <Sparkles className="text-blue-500/40" size={40} />
                        </div>
                        <h2 className="text-2xl font-bold mb-2 text-zinc-200">Как я могу усилить твою мысль сегодня?</h2>
                        <p className="text-zinc-500 max-w-sm">
                            Я здесь, чтобы помочь структурировать решения, анализировать идеи и сохранять твой цифровой опыт.
                        </p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={cn(
                            "flex gap-4 max-w-[85%]",
                            msg.role === "user" ? "ml-auto flex-row-reverse" : ""
                        )}
                    >
                        <div className={cn(
                            "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1",
                            msg.role === "user" ? "bg-zinc-800" : "bg-blue-600 shadow-lg shadow-blue-600/20"
                        )}>
                            {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={cn(
                            "p-4 rounded-2xl text-sm leading-relaxed",
                            msg.role === "user"
                                ? "bg-white/10 text-white rounded-tr-none"
                                : "bg-white/5 border border-white/10 text-zinc-100 rounded-tl-none"
                        )}>
                            {msg.content}
                            {msg.memory_saved && (
                                <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-2 text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                                    <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                    Insight recorded to long-term memory
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {liveTranscript && (
                    <div className="sticky bottom-0 left-0 right-0 z-10 pb-4">
                        <TranscriptDisplay text={liveTranscript} />
                    </div>
                )}

                {isLoading && (
                    <div className="flex gap-4 max-w-[85%] animate-pulse">
                        <div className="w-8 h-8 rounded-lg bg-blue-600/50 flex items-center justify-center flex-shrink-0">
                            <Bot size={16} />
                        </div>
                        <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-zinc-500 text-sm italic">
                            Digital Denis анализирует контекст...
                        </div>
                    </div>
                )}
            </div>

            {/* Input Wrapper */}
            <div className="flex gap-4 items-end mb-4">
                {/* Input Container */}
                <div className="relative group flex-1">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-20 group-focus-within:opacity-40 transition-opacity" />
                    <div className="relative flex bg-[#0f0f0f] rounded-2xl p-2 border border-white/10 group-focus-within:border-white/20 transition-all">
                        <textarea
                            rows={1}
                            value={input}
                            onChange={(e) => {
                                setInput(e.target.value);
                                e.target.style.height = 'inherit';
                                e.target.style.height = `${e.target.scrollHeight}px`;
                            }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder="Опиши решение или задай аналитический вопрос..."
                            className="flex-1 bg-transparent border-none focus:ring-0 text-white p-3 resize-none max-h-32 text-sm placeholder:text-zinc-600"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed my-auto ml-2"
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>

                {/* Voice Button */}
                <VoiceButton
                    onTranscript={handleTranscript}
                />
            </div>
        </div>
    );
}
