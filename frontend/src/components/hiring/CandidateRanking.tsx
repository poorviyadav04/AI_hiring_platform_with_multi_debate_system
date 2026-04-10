"use client";

import { useState } from "react";
import type { HiringEvaluationResult } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import GitHubBadge from "@/components/hiring/GitHubBadge";
import DebateTranscript from "@/components/hiring/DebateTranscript";

function scoreColor(score: number) {
  if (score >= 75) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  return "text-red-400";
}

function decisionBadge(decision: string) {
  if (decision.includes("strong_hire") || decision === "hire")
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  if (decision.includes("conditional"))
    return "bg-amber-500/20 text-amber-400 border-amber-500/30";
  return "bg-red-500/20 text-red-400 border-red-500/30";
}

export default function CandidateRanking({
  result,
}: {
  result: HiringEvaluationResult;
}) {
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  return (
    <Card className="border-0 bg-zinc-900/60 ring-white/10">
      <CardHeader>
        <CardTitle className="text-white">
          Candidate Rankings
          <span className="ml-2 text-sm font-normal text-zinc-400">
            {result.total_candidates} evaluated
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/10 hover:bg-transparent">
              <TableHead className="text-zinc-400">Rank</TableHead>
              <TableHead className="text-zinc-400">Name</TableHead>
              <TableHead className="text-zinc-400">Score</TableHead>
              <TableHead className="text-zinc-400">Skills</TableHead>
              <TableHead className="text-zinc-400">Experience</TableHead>
              <TableHead className="text-zinc-400">GitHub</TableHead>
              <TableHead className="text-zinc-400">Decision</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {result.rankings.map((c, idx) => (
              <>
                <TableRow
                  key={`row-${idx}`}
                  className="cursor-pointer border-white/5 transition-colors hover:bg-white/5"
                  onClick={() =>
                    setExpandedRow(expandedRow === idx ? null : idx)
                  }
                >
                  <TableCell className="font-bold text-zinc-300">
                    #{idx + 1}
                  </TableCell>
                  <TableCell className="font-medium text-white">
                    {c.candidate_name}
                  </TableCell>
                  <TableCell>
                    <span
                      className={`text-lg font-bold tabular-nums ${scoreColor(c.overall_score)}`}
                    >
                      {Math.round(c.overall_score)}
                    </span>
                  </TableCell>
                  <TableCell className={scoreColor(c.component_scores.skills)}>
                    {Math.round(c.component_scores.skills)}
                  </TableCell>
                  <TableCell className={scoreColor(c.component_scores.experience)}>
                    {Math.round(c.component_scores.experience)}
                  </TableCell>
                  <TableCell>
                    {c.github_verification ? (
                      <GitHubBadge verification={c.github_verification} />
                    ) : (
                      <span className="text-zinc-600">--</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${decisionBadge(c.recommendation)}`}
                    >
                      {c.recommendation.replace(/_/g, " ")}
                    </span>
                  </TableCell>
                </TableRow>

                {expandedRow === idx && (
                  <TableRow
                    key={`expanded-${idx}`}
                    className="border-white/5 hover:bg-transparent"
                  >
                    <TableCell colSpan={7} className="p-4">
                      <div className="space-y-3">
                        {c.key_strengths.length > 0 && (
                          <div>
                            <p className="text-xs font-medium uppercase text-zinc-500">Strengths</p>
                            <ul className="mt-1 space-y-0.5">
                              {c.key_strengths.map((s, i) => (
                                <li key={i} className="text-sm text-emerald-400">+ {s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {c.key_concerns.length > 0 && (
                          <div>
                            <p className="text-xs font-medium uppercase text-zinc-500">Concerns</p>
                            <ul className="mt-1 space-y-0.5">
                              {c.key_concerns.map((s, i) => (
                                <li key={i} className="text-sm text-red-400">- {s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {c.debate_summary.length > 0 && (
                          <DebateTranscript transcript={c.debate_summary} />
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
