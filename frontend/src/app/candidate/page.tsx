"use client";

import { useState, useCallback, useRef } from "react";
import type { CandidateAnalysisResult } from "@/lib/types";
import { analyzeCandidate } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import ScoreCard from "@/components/candidate/ScoreCard";
import GapAnalysis from "@/components/candidate/GapAnalysis";
import Roadmap from "@/components/candidate/Roadmap";

export default function CandidatePage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CandidateAnalysisResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type === "application/pdf") {
      setFile(dropped);
    }
  }, []);

  const handleSubmit = async () => {
    if (!file || !jobDescription.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeCandidate(file, jobDescription);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Candidate Analysis</h1>
        <p className="mt-2 text-zinc-400">
          Upload your resume and paste the job description to see how well you
          match.
        </p>
      </div>

      <div className="space-y-6">
        {/* Upload area */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 transition-colors ${
            dragActive
              ? "border-emerald-500 bg-emerald-500/5"
              : file
                ? "border-emerald-500/30 bg-emerald-500/5"
                : "border-white/10 bg-zinc-900/40 hover:border-white/20"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) setFile(f);
            }}
          />
          <svg
            className={`size-10 ${file ? "text-emerald-400" : "text-zinc-500"}`}
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
            />
          </svg>
          {file ? (
            <p className="text-sm text-emerald-400">{file.name}</p>
          ) : (
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">
                Drop your resume here or click to browse
              </p>
              <p className="mt-1 text-xs text-zinc-500">PDF files only</p>
            </div>
          )}
        </div>

        {/* Job description */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-zinc-300">
            Job Description
          </label>
          <Textarea
            placeholder="Paste the full job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            className="min-h-[180px] resize-y border-white/10 bg-zinc-900/40 text-zinc-200 placeholder:text-zinc-600"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Submit */}
        <Button
          onClick={handleSubmit}
          disabled={!file || !jobDescription.trim() || loading}
          size="lg"
          className="w-full bg-gradient-to-r from-emerald-600 to-cyan-600 text-white hover:from-emerald-500 hover:to-cyan-500 disabled:opacity-40"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg
                className="size-4 animate-spin"
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
              Analyzing...
            </span>
          ) : (
            "Analyze My Fit"
          )}
        </Button>
      </div>

      {/* Results */}
      {result && (
        <div className="mt-12 space-y-8">
          <ScoreCard result={result} />
          <GapAnalysis gaps={result.gaps} />
          <Roadmap items={result.roadmap} />
        </div>
      )}
    </div>
  );
}
