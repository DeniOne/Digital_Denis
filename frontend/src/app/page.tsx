"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  PlusCircle,
  ArrowUpRight,
  Zap,
  Brain,
  History,
  TrendingUp,
  AlertCircle
} from "lucide-react";
import { memoryApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    decisions: 0,
    insights: 0,
    anomalies: 0,
    mentalLoad: "Low"
  });

  return (
    <div className="max-w-7xl mx-auto space-y-10">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-zinc-500 bg-clip-text text-transparent">
          Добро пожаловать, Профессионал.
        </h1>
        <p className="text-zinc-500 text-lg">
          Система Digital Denis активна. Когнитивный слой синхронизирован.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Решения"
          value="12"
          sub="За последние 7 дней"
          icon={Zap}
          color="text-blue-500"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="Инсайты"
          value="48"
          sub="+12% к прошлой неделе"
          icon={Brain}
          color="text-purple-500"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="Аномалии"
          value="2"
          sub="Требуют внимания"
          icon={AlertCircle}
          color="text-orange-500"
          bg="bg-orange-500/10"
        />
        <StatCard
          title="Когнит. нагрузка"
          value="Низкая"
          sub="Оптимальное состояние"
          icon={TrendingUp}
          color="text-emerald-500"
          bg="bg-emerald-500/10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Memory */}
        <div className="lg:col-span-2 rounded-3xl bg-[#0a0a0a]/50 border border-white/5 p-8 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <History className="text-zinc-400" />
              <h2 className="text-xl font-semibold">Последние записи памяти</h2>
            </div>
            <Link href="/memory" className="text-zinc-500 hover:text-white transition-colors flex items-center gap-1 text-sm font-medium">
              Смотреть все <ArrowUpRight size={16} />
            </Link>
          </div>

          <div className="space-y-4">
            <MemoryStub
              type="Decision"
              title="Переход на многослойную архитектуру памяти"
              date="2 часа назад"
            />
            <MemoryStub
              type="Insight"
              title="Корреляция между временем отдыха и качеством логики"
              date="Вчера"
            />
            <MemoryStub
              type="Fact"
              title="Текущий стек: FastAPI + Next.js + PostgreSQL"
              date="29 Дек"
            />
          </div>
        </div>

        {/* Action Panel */}
        <div className="rounded-3xl bg-gradient-to-b from-blue-600/10 to-transparent border border-blue-500/10 p-8">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-3">
            <PlusCircle className="text-blue-500" />
            Быстрые действия
          </h2>
          <div className="space-y-3">
            <Link href="/chat" className="block">
              <ActionButton label="Зафиксировать решение" />
            </Link>
            <Link href="/chat" className="block">
              <ActionButton label="Начать сессию анализа" primary />
            </Link>
            <Link href="/chat" className="block">
              <ActionButton label="Задать вопрос системе" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, sub, icon: Icon, color, bg }: any) {
  return (
    <div className="p-6 rounded-3xl bg-[#0a0a0a]/50 border border-white/5 hover:border-white/10 transition-all group">
      <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110", bg)}>
        <Icon size={24} className={color} />
      </div>
      <div className="text-zinc-500 text-sm font-medium mb-1">{title}</div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-zinc-600 text-xs">{sub}</div>
    </div>
  );
}

function MemoryStub({ type, title, date }: any) {
  return (
    <div className="p-4 rounded-2xl bg-white/5 border border-transparent hover:border-white/5 hover:bg-white/10 transition-all cursor-pointer flex items-center gap-4">
      <div className={cn(
        "px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider",
        type === 'Decision' ? "bg-blue-500/20 text-blue-400" : "bg-purple-500/20 text-purple-400"
      )}>
        {type}
      </div>
      <div className="flex-1 font-medium truncate">{title}</div>
      <div className="text-zinc-600 text-xs whitespace-nowrap">{date}</div>
    </div>
  );
}

function ActionButton({ label, primary }: any) {
  return (
    <button className={cn(
      "w-full py-3 px-4 rounded-xl font-medium transition-all text-sm",
      primary
        ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20 hover:bg-blue-500"
        : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10"
    )}>
      {label}
    </button>
  );
}
