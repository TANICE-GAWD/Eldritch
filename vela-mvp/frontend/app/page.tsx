"use client";

import { useState } from "react";
import ExtractView from "./components/ExtractView";
import ScheduleGrid from "./components/ScheduleGrid";

type Tab = "extract" | "schedule";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>("extract");

  return (
    <div className="min-h-full flex flex-col">
      
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight text-zinc-100">
            Vela
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 font-medium border border-violet-500/30">
            MVP
          </span>
          <span className="ml-auto text-xs text-zinc-500">
            Scheduling AI Demo
          </span>
        </div>
      </header>

      
      <div className="border-b border-zinc-800 px-6">
        <div className="max-w-5xl mx-auto flex gap-0">
          {(["extract", "schedule"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors capitalize ${
                activeTab === tab
                  ? "border-violet-500 text-violet-300"
                  : "border-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {tab === "extract" ? "Extract" : "Schedule"}
            </button>
          ))}
        </div>
      </div>

      
      <main className="flex-1 px-6 py-8">
        <div className="max-w-5xl mx-auto">
          {activeTab === "extract" ? <ExtractView /> : <ScheduleGrid />}
        </div>
      </main>
    </div>
  );
}
