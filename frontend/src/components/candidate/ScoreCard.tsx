"use client";

import type { CandidateAnalysisResult } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function scoreColor(score: number) {
  if (score >= 75) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  return "text-red-400";
}

function scoreBg(score: number) {
  if (score >= 75) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}

function recommendBadgeVariant(rec: string) {
  const lower = rec.toLowerCase();
  if (lower.includes("strong_hire") || lower === "hire")
    return "default" as const;
  if (lower.includes("conditional")) return "secondary" as const;
  return "destructive" as const;
}

export default function ScoreCard({
  result,
}: {
  result: CandidateAnalysisResult;
}) {
  const sc = result.score_card;
  const cs = sc.component_scores;

  const scores = [
    { label: "Skills Match", value: cs.skills },
    { label: "Experience Fit", value: cs.experience },
    { label: "Education Level", value: cs.education },
  ];

  return (
    <Card className="border-0 bg-zinc-900/60 ring-white/10">
      <CardHeader>
        <CardTitle className="text-white">Your Fit Score</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Big score */}
        <div className="flex items-center gap-6">
          <div className="flex flex-col items-center">
            <span
              className={`text-6xl font-black tabular-nums ${scoreColor(sc.overall_score)}`}
            >
              {Math.round(sc.overall_score)}
            </span>
            <span className="text-xs text-zinc-500">out of 100</span>
          </div>

          <div className="flex flex-col gap-2">
            <Badge variant={recommendBadgeVariant(sc.recommendation)}>
              {sc.recommendation.replace(/_/g, " ")}
            </Badge>
            {sc.key_factors.missing_required_skills.length > 0 && (
              <p className="max-w-md text-sm text-zinc-400">
                Missing: {sc.key_factors.missing_required_skills.join(", ")}
              </p>
            )}
          </div>
        </div>

        {/* Component scores */}
        <div className="space-y-3">
          {scores.map((s) => (
            <div key={s.label}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-zinc-300">
                  {s.label}
                </span>
                <span
                  className={`text-sm tabular-nums ${scoreColor(s.value)}`}
                >
                  {Math.round(s.value)}
                </span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-zinc-800">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${scoreBg(s.value)}`}
                  style={{ width: `${s.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
