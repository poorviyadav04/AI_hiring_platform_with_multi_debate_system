"use client";

import type { RoadmapItem } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function priorityClass(priority: RoadmapItem["priority"]) {
  const map = {
    high: "bg-red-500/20 text-red-400 border-red-500/30",
    medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    low: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };
  return map[priority];
}

export default function Roadmap({ items }: { items: RoadmapItem[] }) {
  if (!items.length) return null;

  return (
    <Card className="border-0 bg-zinc-900/60 ring-white/10">
      <CardHeader>
        <CardTitle className="text-white">Learning Roadmap</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-xl border border-white/10 bg-zinc-800/50 p-4"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-white">{item.skill}</h4>
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${priorityClass(item.priority)}`}
                >
                  {item.priority}
                </span>
              </div>

              <div className="flex items-center gap-4 text-sm text-zinc-400">
                <span>{item.estimated_weeks} weeks</span>
                <span className="text-emerald-400">
                  +{item.impact_on_score} pts
                </span>
              </div>

              {item.resources.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Resources
                  </p>
                  <ul className="space-y-0.5">
                    {item.resources.map((r, j) => (
                      <li
                        key={j}
                        className="text-sm text-zinc-400 before:mr-1.5 before:text-emerald-500 before:content-['->']"
                      >
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
