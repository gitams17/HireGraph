"use client";

import { ResumeAnalysis } from "@/types";

interface ResumeAnalysisPanelProps {
  analysis: ResumeAnalysis | null;
  loading: boolean;
  onAnalyzeClick: () => void;
}

export function ResumeAnalysisPanel({
  analysis,
  loading,
  onAnalyzeClick,
}: ResumeAnalysisPanelProps) {
  if (!analysis) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-2xl">
          📄
        </div>
        <h3 className="mt-3 text-base font-semibold text-zinc-900">
          No AI Screening Performed Yet
        </h3>
        <p className="mx-auto mt-1 max-w-md text-xs text-zinc-500">
          Run LangGraph AI screening to parse the candidate&apos;s resume, extract structured skills and work history, and generate an evidence-based assessment against the job requirements.
        </p>
        <button
          onClick={onAnalyzeClick}
          disabled={loading}
          className="mt-5 rounded-lg bg-zinc-900 px-5 py-2 text-sm font-semibold text-white hover:bg-zinc-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "Analyzing resume…" : "✨ Run AI Screening"}
        </button>
      </div>
    );
  }

  const score = analysis.ats_score ?? 0;
  const assessment = analysis.assessment || {};
  const rec = assessment.reviewer_recommendation || "requires_human_review";

  const recLabels: Record<string, { label: string; color: string }> = {
    strong_match: { label: "Strong Match", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    potential_match: { label: "Potential Match", color: "bg-blue-50 text-blue-700 border-blue-200" },
    requires_human_review: { label: "Requires Human Review", color: "bg-amber-50 text-amber-700 border-amber-200" },
    does_not_meet_minimum: { label: "Does Not Meet Minimum", color: "bg-red-50 text-red-700 border-red-200" },
  };

  const currentRec = recLabels[rec] || recLabels.requires_human_review;

  let scoreColor = "text-zinc-900";
  let scoreRing = "stroke-zinc-900";
  if (score >= 80) {
    scoreColor = "text-emerald-600";
    scoreRing = "stroke-emerald-600";
  } else if (score >= 60) {
    scoreColor = "text-blue-600";
    scoreRing = "stroke-blue-600";
  } else if (score >= 40) {
    scoreColor = "text-amber-600";
    scoreRing = "stroke-amber-600";
  } else {
    scoreColor = "text-red-600";
    scoreRing = "stroke-red-600";
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-zinc-100">
        <div className="flex items-center space-x-5">
          {/* Circular ATS score dial */}
          <div className="relative flex h-20 w-20 shrink-0 items-center justify-center">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
              <path
                className="stroke-zinc-100"
                strokeWidth="3.5"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={scoreRing}
                strokeDasharray={`${score}, 100`}
                strokeWidth="3.5"
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute text-center">
              <span className={`text-xl font-extrabold ${scoreColor}`}>{score}</span>
              <span className="block text-[9px] uppercase font-bold text-zinc-400">ATS</span>
            </div>
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span
                className={`rounded-full border px-3 py-0.5 text-xs font-semibold ${currentRec.color}`}
              >
                {currentRec.label}
              </span>
              <span className="text-xs text-zinc-400">
                Model: {analysis.model_name} • {new Date(analysis.created_at).toLocaleDateString()}
              </span>
            </div>
            <h2 className="mt-1.5 text-base font-bold text-zinc-900">
              {assessment.summary_headline || "Candidate Resume Assessment"}
            </h2>
            <p className="mt-1 text-xs text-zinc-500 max-w-2xl">
              {assessment.recommendation_rationale}
            </p>
          </div>
        </div>

        <button
          onClick={onAnalyzeClick}
          disabled={loading}
          className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 shrink-0"
        >
          {loading ? "Re-screening…" : "🔄 Re-run Screening"}
        </button>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-400">
        <span>
          ⚖️ <strong>Advisory Tool:</strong> ATS score assists human reviewers; it does not replace recruiter decisions or automatically filter candidates.
        </span>
      </div>
    </div>
  );
}
