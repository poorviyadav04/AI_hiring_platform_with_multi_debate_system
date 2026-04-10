"use client";

import type { GapItem } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function severityBadge(severity: GapItem["severity"]) {
  const map = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    moderate: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    minor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };
  return map[severity];
}

export default function GapAnalysis({ gaps }: { gaps: GapItem[] }) {
  if (!gaps.length) return null;

  return (
    <Card className="border-0 bg-zinc-900/60 ring-white/10">
      <CardHeader>
        <CardTitle className="text-white">Gap Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-white/10 hover:bg-transparent">
              <TableHead className="text-zinc-400">Category</TableHead>
              <TableHead className="text-zinc-400">Gap</TableHead>
              <TableHead className="text-zinc-400">Severity</TableHead>
              <TableHead className="text-zinc-400">Impact</TableHead>
              <TableHead className="text-zinc-400">Suggestion</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {gaps.map((gap, i) => (
              <TableRow key={i} className="border-white/5">
                <TableCell className="font-medium text-zinc-200">
                  {gap.category}
                </TableCell>
                <TableCell className="max-w-[200px] text-zinc-300">
                  {gap.item}
                </TableCell>
                <TableCell>
                  <span
                    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${severityBadge(gap.severity)}`}
                  >
                    {gap.severity}
                  </span>
                </TableCell>
                <TableCell className="max-w-[180px] text-zinc-400">
                  +{gap.impact_points} pts
                </TableCell>
                <TableCell className="max-w-[220px] text-zinc-400">
                  {gap.suggestion}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
