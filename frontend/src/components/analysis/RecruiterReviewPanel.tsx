"use client";

import { useState } from "react";
import { api, extractApiErrors } from "@/lib/api";
import { ResumeAnalysis } from "@/types";

interface RecruiterReviewPanelProps {
  applicationId: string;
  analysis: ResumeAnalysis;
  onAnalysisUpdated: (updated: ResumeAnalysis) => void;
}

export function RecruiterReviewPanel({
  applicationId,
  analysis,
  onAnalysisUpdated,
}: RecruiterReviewPanelProps) {
  const [adjustedScore, setAdjustedScore] = useState<number>(analysis.ats_score ?? 75);
  const [recruiterNotes, setRecruiterNotes] = useState<string>(
    analysis.recruiter_feedback?.notes || ""
  );
  const [humanVerified, setHumanVerified] = useState<boolean>(
    Boolean(analysis.recruiter_feedback?.verified)
  );
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ text: string; isError: boolean } | null>(null);

  async function handleSaveReview(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMsg(null);

    try {
      const payload = {
        ats_score: adjustedScore,
        recruiter_feedback: {
          ...analysis.recruiter_feedback,
          verified: humanVerified,
          notes: recruiterNotes.trim(),
          reviewed_at: new Date().toISOString(),
        },
      };

      const updated = await api.patch<ResumeAnalysis>(
        `/api/v1/applications/${applicationId}/analysis/${analysis.id}/`,
        payload
      );
      setMsg({ text: "Recruiter review and adjustments saved successfully.", isError: false });
      onAnalysisUpdated(updated);
    } catch (err) {
      setMsg({ text: extractApiErrors(err), isError: true });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-zinc-900 mb-1">
        Human Recruiter Review & Overrides
      </h3>
      <p className="text-xs text-zinc-500 mb-4">
        Validate or adjust the AI-generated assessment. Record human notes to ensure fair and accurate evaluation.
      </p>

      {msg && (
        <div
          className={`mb-4 rounded-lg p-3 text-xs ${
            msg.isError
              ? "border border-red-200 bg-red-50 text-red-700"
              : "border border-emerald-200 bg-emerald-50 text-emerald-700"
          }`}
        >
          {msg.text}
        </div>
      )}

      <form onSubmit={handleSaveReview} className="space-y-4 text-xs">
        <div className="flex items-center space-x-3">
          <input
            id="humanVerified"
            type="checkbox"
            checked={humanVerified}
            onChange={(e) => setHumanVerified(e.target.checked)}
            className="h-4 w-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-400"
          />
          <label htmlFor="humanVerified" className="font-medium text-zinc-700">
            Mark as human-verified (confirm evidence was manually inspected)
          </label>
        </div>

        <div>
          <label className="block font-medium text-zinc-700 mb-1">
            Recruiter ATS Score Override:{" "}
            <span className="font-bold text-zinc-900">{adjustedScore} / 100</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={adjustedScore}
            onChange={(e) => setAdjustedScore(parseInt(e.target.value, 10))}
            className="w-full accent-zinc-900"
          />
        </div>

        <div>
          <label className="block font-medium text-zinc-700 mb-1">
            Human Review Notes & Interview Recommendations
          </label>
          <textarea
            rows={3}
            value={recruiterNotes}
            onChange={(e) => setRecruiterNotes(e.target.value)}
            placeholder="e.g. Verified candidate GitHub repositories. Projects demonstrate significant Docker and Redis expertise."
            className="w-full rounded-lg border border-zinc-300 p-2.5 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            {saving ? "Saving review…" : "Save recruiter review"}
          </button>
        </div>
      </form>
    </div>
  );
}
