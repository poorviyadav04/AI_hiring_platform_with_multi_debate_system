"use client";

import type { DebateEntry } from "@/lib/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
function agentColor(role: string) {
  const lower = role.toLowerCase();
  if (lower.includes("evaluator")) return "bg-blue-500/20 text-blue-400";
  if (lower.includes("advocate")) return "bg-emerald-500/20 text-emerald-400";
  if (lower.includes("skeptic")) return "bg-red-500/20 text-red-400";
  if (lower.includes("moderator")) return "bg-purple-500/20 text-purple-400";
  return "bg-zinc-500/20 text-zinc-400";
}

export default function DebateTranscript({
  transcript,
}: {
  transcript: DebateEntry[];
}) {
  if (!transcript.length) return null;

  return (
    <div className="rounded-xl border border-white/10 bg-zinc-800/50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-zinc-300">
        Multi-Agent Debate
      </h4>
      <Tabs defaultValue={transcript[0]?.agent ?? ""}>
        <TabsList className="mb-3">
          {transcript.map((entry) => (
            <TabsTrigger key={entry.agent} value={entry.agent}>
              {entry.agent}
            </TabsTrigger>
          ))}
        </TabsList>
        {transcript.map((entry) => (
          <TabsContent key={entry.agent} value={entry.agent}>
            <div className="space-y-2">
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${agentColor(entry.agent)}`}
              >
                {entry.agent}
              </span>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
                {entry.summary}
              </p>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
