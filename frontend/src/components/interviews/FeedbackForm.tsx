"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { InterviewDetail, PreparedQuestion, QuestionScore, Recommendation } from "@/types";

interface FeedbackFormProps {
  interview: InterviewDetail;
  onSuccess: () => void;
}

export default function FeedbackForm({ interview, onSuccess }: FeedbackFormProps) {
  const [rating, setRating] = useState<number>(4);
  const [recommendation, setRecommendation] = useState<Recommendation>("hire");
  const [summary, setSummary] = useState("");
  const [strengths, setStrengths] = useState("");
  const [areasForImprovement, setAreasForImprovement] = useState("");
  const [questionScores, setQuestionScores] = useState<Record<string, { score: number; notes: string }>>({});

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleScoreChange = (qId: string, score: number, notes?: string) => {
    setQuestionScores((prev) => ({
      ...prev,
      [qId]: {
        score,
        notes: notes !== undefined ? notes : prev[qId]?.notes || "",
      },
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const formattedScores: QuestionScore[] = Object.entries(questionScores).map(
        ([question_id, val]) => ({
          question_id,
          score: val.score,
          notes: val.notes,
        })
      );

      const payload = {
        rating,
        recommendation,
        summary,
        strengths,
        areas_for_improvement: areasForImprovement,
        question_scores: formattedScores,
      };

      await api.post(`/api/v1/interviews/${interview.id}/feedback/`, payload);
      setSuccessMsg("Feedback submitted successfully!");
      onSuccess();
    } catch (err: any) {
      const msg = err?.data?.detail || "Failed to submit feedback. Check permissions.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-5">
      <div className="border-b border-zinc-100 pb-3">
        <h2 className="text-base font-bold text-zinc-900">Submit Interviewer Feedback</h2>
        <p className="text-xs text-zinc-500">
          Provide independent quantitative ratings and structured feedback for candidate evaluation.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-700">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="rounded-lg bg-emerald-50 p-3 text-xs font-medium text-emerald-800">
          ✓ {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Overall Rating & Recommendation */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1.5">
              Overall Rating (1 to 5) *
            </label>
            <div className="flex items-center space-x-2">
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setRating(val)}
                  className={`h-9 w-9 rounded-lg border text-xs font-bold transition-all ${
                    rating === val
                      ? "bg-zinc-900 border-zinc-900 text-white shadow-sm"
                      : "bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-100"
                  }`}
                >
                  {val}
                </button>
              ))}
              <span className="text-xs text-zinc-500 font-medium ml-2">
                {rating === 5
                  ? "5 - Strong Yes"
                  : rating === 4
                  ? "4 - Yes"
                  : rating === 3
                  ? "3 - Neutral"
                  : rating === 2
                  ? "2 - No"
                  : "1 - Strong No"}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1.5">
              Hiring Recommendation *
            </label>
            <select
              value={recommendation}
              onChange={(e) => setRecommendation(e.target.value as Recommendation)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
            >
              <option value="strong_hire">Strong Hire</option>
              <option value="hire">Hire</option>
              <option value="neutral">Neutral / Undecided</option>
              <option value="no_hire">No Hire</option>
              <option value="strong_no_hire">Strong No Hire</option>
            </select>
          </div>
        </div>

        {/* Executive Summary */}
        <div>
          <label className="block text-xs font-semibold text-zinc-700 mb-1">
            Executive Summary *
          </label>
          <textarea
            required
            rows={3}
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="High-level synthesis of candidate performance, technical depth, and suitability…"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
          />
        </div>

        {/* Strengths & Areas for Improvement */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1">
              Key Strengths Observed
            </label>
            <textarea
              rows={3}
              value={strengths}
              onChange={(e) => setStrengths(e.target.value)}
              placeholder="e.g. In-depth understanding of PostgreSQL index architectures, concise communication…"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1">
              Areas for Improvement / Risks
            </label>
            <textarea
              rows={3}
              value={areasForImprovement}
              onChange={(e) => setAreasForImprovement(e.target.value)}
              placeholder="e.g. Limited hands-on experience with asynchronous background task runners…"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
            />
          </div>
        </div>

        {/* Prepared Questions Evaluation */}
        {interview.prepared_questions && interview.prepared_questions.length > 0 && (
          <div className="space-y-3 pt-3 border-t border-zinc-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-600">
              Prepared Question Rubric ({interview.prepared_questions.length} questions)
            </h3>
            <div className="space-y-3">
              {interview.prepared_questions.map((q, idx) => (
                <div
                  key={q.id || idx}
                  className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-3 space-y-2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="text-xs font-semibold text-zinc-900">
                      Q{idx + 1}: {q.question}
                    </div>
                    <div className="flex items-center space-x-1 shrink-0">
                      {[1, 2, 3, 4, 5].map((score) => (
                        <button
                          key={score}
                          type="button"
                          onClick={() => handleScoreChange(q.id || String(idx), score)}
                          className={`h-6 w-6 rounded text-[10px] font-bold border transition-colors ${
                            questionScores[q.id || String(idx)]?.score === score
                              ? "bg-zinc-900 border-zinc-900 text-white"
                              : "bg-white border-zinc-300 text-zinc-700 hover:bg-zinc-100"
                          }`}
                        >
                          {score}
                        </button>
                      ))}
                    </div>
                  </div>
                  <input
                    type="text"
                    value={questionScores[q.id || String(idx)]?.notes || ""}
                    onChange={(e) =>
                      handleScoreChange(
                        q.id || String(idx),
                        questionScores[q.id || String(idx)]?.score || 3,
                        e.target.value
                      )
                    }
                    placeholder="Interviewer notes on response…"
                    className="w-full rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-[11px] focus:outline-none"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end pt-3 border-t border-zinc-200">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-zinc-900 px-5 py-2 text-xs font-bold text-white hover:bg-zinc-800 disabled:opacity-50 transition-colors"
          >
            {loading ? "Submitting Feedback…" : "Submit Independent Feedback"}
          </button>
        </div>
      </form>
    </div>
  );
}
