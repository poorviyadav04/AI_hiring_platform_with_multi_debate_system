"use client";

import { useState, useCallback, useRef } from "react";
import type { HiringEvaluationResult } from "@/lib/types";
import { evaluateCandidates } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import CandidateRanking from "@/components/hiring/CandidateRanking";

export default function HiringPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HiringEvaluationResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === "application/pdf"
    );
    if (dropped.length) {
      setFiles((prev) => {
        const combined = [...prev, ...dropped];
        return combined.slice(0, 20);
      });
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    setFiles((prev) => {
      const combined = [...prev, ...selected];
      return combined.slice(0, 20);
    });
    // Reset so the same files can be re-selected if needed
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!files.length || !jobDescription.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await evaluateCandidates(files, jobDescription);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Hiring Evaluation</h1>
        <p className="mt-2 text-zinc-400">
          Upload candidate resumes and the job description to get AI-powered
          rankings.
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
              ? "border-cyan-500 bg-cyan-500/5"
              : files.length
                ? "border-cyan-500/30 bg-cyan-500/5"
                : "border-white/10 bg-zinc-900/40 hover:border-white/20"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />
          <svg
            className={`size-10 ${files.length ? "text-cyan-400" : "text-zinc-500"}`}
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75"
            />
          </svg>
          <div className="text-center">
            <p className="text-sm font-medium text-zinc-300">
              {files.length
                ? `${files.length} resume${files.length > 1 ? "s" : ""} selected`
                : "Drop resumes here or click to browse"}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              PDF files only, up to 20
            </p>
          </div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {files.map((f, i) => (
              <span
                key={`${f.name}-${i}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-zinc-800/50 px-3 py-1.5 text-sm text-zinc-300"
              >
                {f.name}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(i);
                  }}
                  className="ml-1 text-zinc-500 transition-colors hover:text-red-400"
                >
                  <svg
                    className="size-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18 18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        )}

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
          disabled={!files.length || !jobDescription.trim() || loading}
          size="lg"
          className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 disabled:opacity-40"
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
              Evaluating {files.length} candidate
              {files.length > 1 ? "s" : ""}...
            </span>
          ) : (
            "Evaluate All Candidates"
          )}
        </Button>
      </div>

      {/* Results */}
      {result && (
        <div className="mt-12">
          <CandidateRanking result={result} />
        </div>
      )}
    </div>
  );
}
