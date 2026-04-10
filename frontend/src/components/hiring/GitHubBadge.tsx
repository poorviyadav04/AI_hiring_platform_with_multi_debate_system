"use client";

import { useState } from "react";
import type { GitHubVerificationResult } from "@/lib/types";

function trustColor(score: number) {
  if (score >= 75) return "text-emerald-400";
  if (score >= 50) return "text-amber-400";
  return "text-red-400";
}

function trustBg(score: number) {
  if (score >= 75) return "bg-emerald-500/20 border-emerald-500/30";
  if (score >= 50) return "bg-amber-500/20 border-amber-500/30";
  return "bg-red-500/20 border-red-500/30";
}

export default function GitHubBadge({
  verification,
}: {
  verification: GitHubVerificationResult;
}) {
  const [expanded, setExpanded] = useState(false);
  const score = verification.overall_trust_score;

  const verified = verification.skill_verification?.filter((s) => s.verified) ?? [];
  const unverified = verification.skill_verification?.filter((s) => !s.verified) ?? [];

  return (
    <div className="inline-flex flex-col">
      <button
        onClick={() => setExpanded(!expanded)}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors hover:opacity-80 ${trustBg(score)}`}
      >
        {verification.flags.length > 0 && (
          <svg
            className="size-3 text-amber-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
        )}
        <span className={trustColor(score)}>{Math.round(score)}</span>
        <span className="text-zinc-400">{verification.trust_label}</span>
      </button>

      {expanded && (
        <div className="mt-2 w-72 rounded-lg border border-white/10 bg-zinc-900 p-3 text-sm shadow-xl">
          <p className="mb-2 text-zinc-300">{verification.analysis_summary}</p>

          {verified.length > 0 && (
            <div className="mb-2">
              <p className="text-xs font-medium text-zinc-500">Verified Skills</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {verified.map((s) => (
                  <span
                    key={s.skill}
                    className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400"
                  >
                    {s.skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {unverified.length > 0 && (
            <div className="mb-2">
              <p className="text-xs font-medium text-zinc-500">Unverified Skills</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {unverified.map((s) => (
                  <span
                    key={s.skill}
                    className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs text-red-400"
                  >
                    {s.skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {verification.flags.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-500">Flags</p>
              <ul className="mt-1 space-y-0.5">
                {verification.flags.map((f, i) => (
                  <li key={i} className="text-xs text-amber-400">
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
