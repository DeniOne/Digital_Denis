"use client";

import { useState, useEffect } from "react";
import { scheduleApi, ScheduleItem } from "@/lib/api";

// Дни недели
const WEEKDAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const MONTHS = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

// Типы элементов
const itemTypeConfig = {
    event: { emoji: '📌', label: 'Встреча', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
    task: { emoji: '📝', label: 'Задача', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
    reminder: { emoji: '🔔', label: 'Напоминание', color: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
    recurring: { emoji: '🔄', label: 'Повторяющееся', color: 'bg-green-500/10 text-green-400 border-green-500/30' },
};

export default function SchedulePage() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
    const [items, setItems] = useState<ScheduleItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCompleted, setShowCompleted] = useState(false);

    // Загрузка данных
    useEffect(() => {
        loadSchedule();
    }, [selectedDate, showCompleted]);

    const loadSchedule = async () => {
        if (!selectedDate) return;
        setIsLoading(true);
        try {
            // Format dates using local time, not UTC
            const pad = (n: number) => n.toString().padStart(2, '0');
            const dateStr = `${selectedDate.getFullYear()}-${pad(selectedDate.getMonth() + 1)}-${pad(selectedDate.getDate())}`;

            const nextDay = new Date(selectedDate);
            nextDay.setDate(nextDay.getDate() + 1);
            const endStr = `${nextDay.getFullYear()}-${pad(nextDay.getMonth() + 1)}-${pad(nextDay.getDate())}`;

            const response = await scheduleApi.getRange(dateStr, endStr, showCompleted);
            setItems(response.items || []);
        } catch (error) {
            console.error('Failed to load schedule:', error);
            setItems([]);
        } finally {
            setIsLoading(false);
        }
    };

    // Календарь: дни месяца
    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const days: (Date | null)[] = [];

        // Пустые ячейки до первого дня
        for (let i = 0; i < firstDay.getDay(); i++) {
            days.push(null);
        }

        // Дни месяца
        for (let d = 1; d <= lastDay.getDate(); d++) {
            days.push(new Date(year, month, d));
        }

        return days;
    };

    const navigateMonth = (delta: number) => {
        setCurrentDate(prev => {
            const newDate = new Date(prev);
            newDate.setMonth(newDate.getMonth() + delta);
            return newDate;
        });
    };

    const isToday = (date: Date | null) => {
        if (!date) return false;
        const today = new Date();
        return date.toDateString() === today.toDateString();
    };

    const isSelected = (date: Date | null) => {
        if (!date || !selectedDate) return false;
        return date.toDateString() === selectedDate.toDateString();
    };

    const formatTime = (isoString?: string) => {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    };

    const handleComplete = async (id: string) => {
        try {
            await scheduleApi.completeItem(id);
            loadSchedule();
        } catch (error) {
            console.error('Failed to complete item:', error);
        }
    };

    const handleSkip = async (id: string) => {
        try {
            await scheduleApi.skipItem(id);
            loadSchedule();
        } catch (error) {
            console.error('Failed to skip item:', error);
        }
    };

    const days = getDaysInMonth(currentDate);

    return (
        <div className="min-h-screen bg-zinc-950 text-white p-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold">📅 Расписание</h1>
                    <p className="text-zinc-400 mt-1">Управляйте встречами, задачами и напоминаниями</p>
                </div>

                <label className="flex items-center gap-2 text-sm text-zinc-400">
                    <input
                        type="checkbox"
                        checked={showCompleted}
                        onChange={(e) => setShowCompleted(e.target.checked)}
                        className="rounded bg-zinc-800 border-zinc-700"
                    />
                    Показать выполненные
                </label>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Calendar */}
                <div className="lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded-xl p-5">
                    {/* Month Navigation */}
                    <div className="flex justify-between items-center mb-4">
                        <button
                            onClick={() => navigateMonth(-1)}
                            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                        >
                            ←
                        </button>
                        <h2 className="text-lg font-semibold">
                            {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
                        </h2>
                        <button
                            onClick={() => navigateMonth(1)}
                            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                        >
                            →
                        </button>
                    </div>

                    {/* Weekday Headers */}
                    <div className="grid grid-cols-7 gap-1 mb-2">
                        {WEEKDAYS.map(day => (
                            <div key={day} className="text-center text-xs text-zinc-500 py-1">
                                {day}
                            </div>
                        ))}
                    </div>

                    {/* Days Grid */}
                    <div className="grid grid-cols-7 gap-1">
                        {days.map((date, idx) => (
                            <button
                                key={idx}
                                onClick={() => date && setSelectedDate(date)}
                                disabled={!date}
                                className={`
                                    aspect-square flex items-center justify-center rounded-lg text-sm
                                    transition-all duration-200
                                    ${!date ? 'invisible' : ''}
                                    ${isToday(date) ? 'ring-2 ring-blue-500' : ''}
                                    ${isSelected(date) ? 'bg-blue-600 text-white' : 'hover:bg-zinc-800'}
                                `}
                            >
                                {date?.getDate()}
                            </button>
                        ))}
                    </div>

                    {/* Quick Actions */}
                    <div className="mt-6 pt-4 border-t border-zinc-800">
                        <button
                            onClick={() => setSelectedDate(new Date())}
                            className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors"
                        >
                            Сегодня
                        </button>
                    </div>
                </div>

                {/* Schedule Items */}
                <div className="lg:col-span-2">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
                        <h2 className="text-lg font-semibold mb-4">
                            {selectedDate ? (
                                <>
                                    {selectedDate.toLocaleDateString('ru-RU', {
                                        weekday: 'long',
                                        day: 'numeric',
                                        month: 'long'
                                    })}
                                </>
                            ) : 'Выберите дату'}
                        </h2>

                        {isLoading ? (
                            <div className="space-y-3">
                                {[...Array(3)].map((_, i) => (
                                    <div key={i} className="h-20 bg-zinc-800/50 rounded-lg animate-pulse" />
                                ))}
                            </div>
                        ) : items.length > 0 ? (
                            <div className="space-y-3">
                                {items.map(item => {
                                    const config = itemTypeConfig[item.item_type as keyof typeof itemTypeConfig] || itemTypeConfig.reminder;
                                    const isCompleted = item.status === 'completed' || item.status === 'confirmed';

                                    return (
                                        <div
                                            key={item.id}
                                            className={`
                                                p-4 rounded-lg border transition-all
                                                ${isCompleted ? 'opacity-50' : ''}
                                                ${config.color}
                                            `}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span>{config.emoji}</span>
                                                        <span className={`font-medium ${isCompleted ? 'line-through' : ''}`}>
                                                            {item.title}
                                                        </span>
                                                        <span className="text-xs px-2 py-0.5 rounded bg-zinc-800/50">
                                                            {config.label}
                                                        </span>
                                                    </div>

                                                    <div className="text-sm text-zinc-400">
                                                        {item.start_at && (
                                                            <span>⏰ {formatTime(item.start_at)}</span>
                                                        )}
                                                        {item.end_at && (
                                                            <span> — {formatTime(item.end_at)}</span>
                                                        )}
                                                        {item.due_at && (
                                                            <span>⏰ До {formatTime(item.due_at)}</span>
                                                        )}
                                                    </div>

                                                    {item.description && (
                                                        <p className="text-sm text-zinc-500 mt-2">
                                                            {item.description}
                                                        </p>
                                                    )}
                                                </div>

                                                {!isCompleted && (
                                                    <div className="flex gap-2 ml-4">
                                                        <button
                                                            onClick={() => handleComplete(item.id)}
                                                            className="p-2 bg-green-500/20 hover:bg-green-500/30 rounded-lg transition-colors"
                                                            title="Выполнено"
                                                        >
                                                            ✅
                                                        </button>
                                                        <button
                                                            onClick={() => handleSkip(item.id)}
                                                            className="p-2 bg-zinc-700/50 hover:bg-zinc-700 rounded-lg transition-colors"
                                                            title="Пропустить"
                                                        >
                                                            ❌
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
                                <span className="text-4xl mb-4">🗓️</span>
                                <p>Нет запланированных дел</p>
                                <p className="text-sm mt-2">
                                    Скажите в чат: "Напомни позвонить маме в 15:00"
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
