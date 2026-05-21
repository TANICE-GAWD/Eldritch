"use client";

import { useState } from "react";




const DAY1 = "2026-05-21";
const DAY2 = "2026-05-22";

interface TimeSlot {
  start: string;
  end: string;
  confidence: number;
  timezone: string;
}

function makeSlots(day: string): TimeSlot[] {
  return Array.from({ length: 8 }, (_, i) => {
    const hour = 9 + i;
    const pad = (n: number) => String(n).padStart(2, "0");
    return {
      start: `${day}T${pad(hour)}:00:00`,
      end: `${day}T${pad(hour + 1)}:00:00`,
      confidence: 1.0,
      timezone: "UTC",
    };
  });
}

const ALL_SLOTS = [...makeSlots(DAY1), ...makeSlots(DAY2)];

const DEMO_INTERVIEWERS = [
  {
    id: "iv1",
    name: "Alex Chen",
    available_slots: ALL_SLOTS,
    max_interviews_per_day: 3,
  },
  {
    id: "iv2",
    name: "Maya Patel",
    available_slots: ALL_SLOTS,
    max_interviews_per_day: 3,
  },
  {
    id: "iv3",
    name: "Jordan Lee",
    available_slots: ALL_SLOTS,
    max_interviews_per_day: 3,
  },
];

const DEMO_CANDIDATES = [
  { id: "c1", name: "Sam Rivera", preferred_slots: [] },
  { id: "c2", name: "Taylor Kim", preferred_slots: [] },
  { id: "c3", name: "Morgan Blake", preferred_slots: [] },
  { id: "c4", name: "Casey Wong", preferred_slots: [] },
  { id: "c5", name: "Drew Santos", preferred_slots: [] },
];



interface Assignment {
  candidate_id: string;
  interviewer_id: string;
  slot: TimeSlot;
  explanation?: string;
}

interface ScheduleResult {
  assignments: Assignment[];
  unscheduled: string[];
  stats: {
    total_scheduled?: number;
    avg_interviewer_load?: number;
    [key: string]: unknown;
  };
}



function formatSlot(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatShortSlot(iso: string): string {
  try {
    const d = new Date(iso);
    const month = d.toLocaleString("en-US", { month: "short" });
    const day = d.getDate();
    const hour = d.getHours();
    const ampm = hour >= 12 ? "pm" : "am";
    const h = hour % 12 === 0 ? 12 : hour % 12;
    return `${month} ${day}, ${h}${ampm}`;
  } catch {
    return iso;
  }
}



export default function ScheduleGrid() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScheduleResult | null>(null);

  async function handleRunDemo() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interviewers: DEMO_INTERVIEWERS,
          candidates: DEMO_CANDIDATES,
        }),
      });

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setResult(data.schedule as ScheduleResult);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  
  const assignmentMap = new Map<string, Map<string, Assignment>>();
  if (result) {
    for (const a of result.assignments) {
      if (!assignmentMap.has(a.candidate_id)) {
        assignmentMap.set(a.candidate_id, new Map());
      }
      assignmentMap.get(a.candidate_id)!.set(a.interviewer_id, a);
    }
  }

  
  const totalScheduled = result?.stats?.total_scheduled ?? result?.assignments.length ?? 0;
  const unscheduledCount = result?.unscheduled.length ?? 0;

  const loadPerInterviewer = DEMO_INTERVIEWERS.map((iv) => {
    const count = result?.assignments.filter(
      (a) => a.interviewer_id === iv.id
    ).length ?? 0;
    return count;
  });
  const avgLoad =
    loadPerInterviewer.length > 0
      ? (
          loadPerInterviewer.reduce((s, c) => s + c, 0) /
          loadPerInterviewer.length
        ).toFixed(1)
      : "—";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-zinc-200 mb-1">
          Interview Scheduler
        </h2>
        <p className="text-sm text-zinc-500">
          Runs a demo schedule for 5 candidates across 3 interviewers over 2
          days using Claude as the scheduling engine.
        </p>
      </div>

      {/* Run button */}
      <button
        onClick={handleRunDemo}
        disabled={loading}
        className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium text-white transition-colors"
      >
        {loading ? (
          <>
            <Spinner />
            Scheduling…
          </>
        ) : (
          "Run Demo Schedule"
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Grid */}
      {result && (
        <div className="space-y-5">
          {/* Stats bar */}
          <div className="flex flex-wrap gap-4">
            <StatPill label="Scheduled" value={String(totalScheduled)} color="emerald" />
            <StatPill label="Unscheduled" value={String(unscheduledCount)} color={unscheduledCount > 0 ? "amber" : "zinc"} />
            <StatPill label="Avg Interviewer Load" value={avgLoad} color="violet" />
          </div>

          {/* Table wrapper */}
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-zinc-900 border-b border-zinc-800">
                  <th className="text-left px-4 py-3 font-medium text-zinc-400 w-36">
                    Candidate
                  </th>
                  {DEMO_INTERVIEWERS.map((iv) => (
                    <th
                      key={iv.id}
                      className="text-center px-4 py-3 font-medium text-zinc-400"
                    >
                      <div>{iv.name}</div>
                      <div className="text-xs font-normal text-zinc-600 mt-0.5">
                        {loadPerInterviewer[DEMO_INTERVIEWERS.indexOf(iv)]} scheduled
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DEMO_CANDIDATES.map((c, ri) => {
                  const isUnscheduled =
                    result.unscheduled.includes(c.id);
                  return (
                    <tr
                      key={c.id}
                      className={`border-b border-zinc-800/60 ${ri % 2 === 0 ? "bg-zinc-900/30" : "bg-zinc-900/10"}`}
                    >
                      <td className="px-4 py-3 font-medium text-zinc-300">
                        <div>{c.name}</div>
                        {isUnscheduled && (
                          <span className="text-xs text-amber-400">
                            unscheduled
                          </span>
                        )}
                      </td>
                      {DEMO_INTERVIEWERS.map((iv) => {
                        const a = assignmentMap.get(c.id)?.get(iv.id);
                        return (
                          <td
                            key={iv.id}
                            className="px-4 py-3 text-center align-middle"
                          >
                            {a ? (
                              <AssignmentCell assignment={a} />
                            ) : (
                              <span className="text-zinc-700">—</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Unscheduled list */}
          {result.unscheduled.length > 0 && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3">
              <p className="text-xs font-medium text-amber-300 mb-1">
                Unscheduled Candidates
              </p>
              <p className="text-sm text-amber-200">
                {result.unscheduled
                  .map(
                    (id) =>
                      DEMO_CANDIDATES.find((c) => c.id === id)?.name ?? id
                  )
                  .join(", ")}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Demo data preview (collapsed) */}
      <DemoDataPreview />
    </div>
  );
}



function AssignmentCell({ assignment }: { assignment: Assignment }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        className="cursor-default rounded-md bg-violet-500/15 border border-violet-500/30 px-2 py-1.5 text-violet-300 text-xs font-medium leading-tight hover:bg-violet-500/25 transition-colors"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {formatShortSlot(assignment.slot.start)}
      </div>

      {showTooltip && assignment.explanation && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-300 shadow-xl pointer-events-none">
          <p className="font-medium text-zinc-200 mb-1">Claude's reasoning</p>
          <p className="leading-relaxed text-zinc-400">{assignment.explanation}</p>
          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-700" />
        </div>
      )}
    </div>
  );
}

function StatPill({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "emerald" | "amber" | "violet" | "zinc";
}) {
  const colorMap = {
    emerald: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300",
    amber: "bg-amber-500/10 border-amber-500/30 text-amber-300",
    violet: "bg-violet-500/10 border-violet-500/30 text-violet-300",
    zinc: "bg-zinc-800 border-zinc-700 text-zinc-400",
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-lg border px-4 py-2 ${colorMap[color]}`}
    >
      <span className="text-xs text-current opacity-70">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}

function DemoDataPreview() {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-zinc-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-xs text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40 transition-colors"
      >
        <span>Demo payload preview</span>
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs text-zinc-500 overflow-x-auto bg-zinc-900/50 border-t border-zinc-800">
          {JSON.stringify(
            {
              interviewers: DEMO_INTERVIEWERS.map((iv) => ({
                ...iv,
                available_slots: [`${DAY1}T09:00:00`, `…`, `${DAY2}T16:00:00`],
              })),
              candidates: DEMO_CANDIDATES,
            },
            null,
            2
          )}
        </pre>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
