"use client";

import { useState } from "react";



interface ProposedSlot {
  start: string;
  end: string;
  confidence: number;
  timezone: string;
}

interface Participant {
  name: string;
  email?: string;
  role?: string;
}

interface ExtractResult {
  intent: string;
  raw_summary: string;
  next_action: string;
  proposed_slots: ProposedSlot[];
  participants: Participant[];
}



const INTENT_STYLES: Record<string, { label: string; classes: string }> = {
  scheduling_request: {
    label: "Scheduling Request",
    classes: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  },
  counter_proposal: {
    label: "Counter Proposal",
    classes: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  },
  confirmation: {
    label: "Confirmation",
    classes: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  },
  rejection: {
    label: "Rejection",
    classes: "bg-red-500/20 text-red-300 border-red-500/30",
  },
  ghost: {
    label: "Ghost",
    classes: "bg-zinc-700/50 text-zinc-400 border-zinc-600",
  },
};

const ROLE_STYLES: Record<string, string> = {
  organizer: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  interviewer: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  candidate: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  attendee: "bg-zinc-700/50 text-zinc-400 border-zinc-600",
};

function intentStyle(intent: string) {
  return INTENT_STYLES[intent] ?? INTENT_STYLES.unknown;
}

function roleStyle(role?: string) {
  if (!role) return ROLE_STYLES.attendee;
  return ROLE_STYLES[role.toLowerCase()] ?? ROLE_STYLES.attendee;
}

function confidenceColor(conf: number): string {
  if (conf >= 0.8) return "bg-emerald-500";
  if (conf >= 0.5) return "bg-amber-500";
  return "bg-red-500";
}

function formatDatetime(dt: string): string {
  try {
    return new Date(dt).toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return dt;
  }
}



const PLACEHOLDER = `Paste an email thread here, e.g.:

From: hiring@acme.com
To: sam@example.com
Subject: Interview invitation

Hi Sam, we'd love to schedule a 1-hour technical interview.
Could you be available on May 21st at 10am or May 22nd at 2pm PST?

Best,
Alex – ACME Recruiting`;

export default function ExtractView() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractResult | null>(null);

  async function handleExtract() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_text: text }),
      });

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `HTTP ${res.status}`);
      }

      const data: ExtractResult = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-zinc-200 mb-1">
          Email Thread Extraction
        </h2>
        <p className="text-sm text-zinc-500">
          Paste a raw email thread and Vela will extract scheduling intent,
          proposed slots, and participants.
        </p>
      </div>

      {/* Input area */}
      <div className="space-y-3">
        <textarea
          className="w-full h-48 rounded-lg bg-zinc-900 border border-zinc-700 px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-600 resize-none focus:outline-none focus:ring-1 focus:ring-violet-500 focus:border-violet-500 transition-colors"
          placeholder={PLACEHOLDER}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading}
        />
        <button
          onClick={handleExtract}
          disabled={loading || !text.trim()}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium text-white transition-colors"
        >
          {loading ? (
            <>
              <Spinner />
              Extracting…
            </>
          ) : (
            "Extract"
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-5 border border-zinc-800 rounded-xl p-5 bg-zinc-900/50">
          {/* Intent badge */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
              Intent
            </span>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-medium border ${intentStyle(result.intent).classes}`}
            >
              {intentStyle(result.intent).label}
            </span>
          </div>

          {/* Summary */}
          <div>
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">
              Summary
            </p>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {result.raw_summary}
            </p>
          </div>

          {/* Next action */}
          <div>
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">
              Next Action
            </p>
            <p className="text-sm text-zinc-200 font-medium">
              {result.next_action}
            </p>
          </div>

          {/* Proposed slots */}
          {result.proposed_slots?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-3">
                Proposed Slots
              </p>
              <ul className="space-y-2">
                {result.proposed_slots.map((slot, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-zinc-700/60 bg-zinc-800/50 px-4 py-3"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <span className="text-sm text-zinc-200">
                        {formatDatetime(slot.start)} – {formatDatetime(slot.end)}
                      </span>
                      <span className="text-xs text-zinc-400 shrink-0">
                        {Math.round(slot.confidence * 100)}% · {slot.timezone}
                      </span>
                    </div>
                    {/* Confidence bar */}
                    <div className="h-1 w-full rounded-full bg-zinc-700">
                      <div
                        className={`h-1 rounded-full transition-all ${confidenceColor(slot.confidence)}`}
                        style={{ width: `${slot.confidence * 100}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Participants */}
          {result.participants?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-3">
                Participants
              </p>
              <div className="flex flex-wrap gap-2">
                {result.participants.map((p, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 rounded-lg border border-zinc-700/60 bg-zinc-800/50 px-3 py-2"
                  >
                    <span className="text-sm text-zinc-200">{p.name}</span>
                    {p.email && (
                      <span className="text-xs text-zinc-500">{p.email}</span>
                    )}
                    {p.role && (
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-medium ${roleStyle(p.role)}`}
                      >
                        {p.role}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
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
