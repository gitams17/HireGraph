"use client";

import type { InterviewFeedback, InterviewParticipant, PreparedQuestion } from "@/types";

interface InterviewTimelineProps {
  participants: InterviewParticipant[];
  feedbacks: InterviewFeedback[];
  preparedQuestions: PreparedQuestion[];
  onRemoveQuestion?: (qId: string) => void;
}

export default function InterviewTimeline({
  participants,
  feedbacks,
  preparedQuestions,
  onRemoveQuestion,
}: InterviewTimelineProps) {
  const getRecommendationBadge = (rec: string) => {
    switch (rec) {
      case "strong_hire":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "hire":
        return "bg-green-100 text-green-800 border-green-300";
      case "neutral":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "no_hire":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "strong_no_hire":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-zinc-100 text-zinc-700 border-zinc-200";
    }
  };

  return (
    <div className="space-y-6">
      {/* Panel Feedback Section */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-zinc-900">
              Interviewer Panel & Evaluations ({feedbacks.length}/{participants.length} submitted)
            </h2>
            <p className="text-xs text-zinc-500">
              Individual evaluations from assigned interviewers.
            </p>
          </div>
        </div>

        {/* Panel members status */}
        <div className="flex flex-wrap gap-2">
          {participants.map((p) => {
            const hasSubmitted = feedbacks.some((f) => f.interviewer.id === p.user.id);
            return (
              <div
                key={p.id}
                className={`flex items-center space-x-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold ${
                  hasSubmitted
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                    : "border-zinc-200 bg-zinc-50 text-zinc-600"
                }`}
              >
                <span>{hasSubmitted ? "✓" : "⏳"}</span>
                <span>{p.user.full_name || p.user.email}</span>
                <span className="text-[10px] text-zinc-400 font-normal">({p.role})</span>
              </div>
            );
          })}
        </div>

        {/* Feedback Cards */}
        <div className="space-y-4 pt-2">
          {feedbacks.map((f) => (
            <div
              key={f.id}
              className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-4 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs font-bold text-zinc-900">
                    {f.interviewer.full_name || f.interviewer.email}
                  </div>
                  <div className="text-[10px] text-zinc-500">
                    Submitted on {new Date(f.submitted_at).toLocaleDateString()} at{" "}
                    {new Date(f.submitted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="rounded-full bg-zinc-900 px-2.5 py-0.5 text-xs font-bold text-white">
                    {f.rating}/5 Rating
                  </span>
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase ${getRecommendationBadge(
                      f.recommendation
                    )}`}
                  >
                    {f.recommendation.replace("_", " ")}
                  </span>
                </div>
              </div>

              <div className="text-xs text-zinc-800 leading-relaxed bg-white p-3 rounded-lg border border-zinc-100">
                <span className="font-bold text-zinc-900">Summary: </span>
                {f.summary}
              </div>

              {(f.strengths || f.areas_for_improvement) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {f.strengths && (
                    <div className="rounded-lg bg-emerald-50/50 border border-emerald-100 p-2.5 text-emerald-950">
                      <span className="font-bold text-emerald-900">Strengths: </span>
                      {f.strengths}
                    </div>
                  )}
                  {f.areas_for_improvement && (
                    <div className="rounded-lg bg-amber-50/50 border border-amber-100 p-2.5 text-amber-950">
                      <span className="font-bold text-amber-900">Areas for Growth: </span>
                      {f.areas_for_improvement}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {feedbacks.length === 0 && (
            <div className="rounded-xl border border-dashed border-zinc-200 p-6 text-center text-xs text-zinc-400">
              No interview feedback submitted yet.
            </div>
          )}
        </div>
      </div>

      {/* Prepared Interview Checklist */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-zinc-900">
              Prepared Interview Questions Checklist ({preparedQuestions.length})
            </h2>
            <p className="text-xs text-zinc-500">
              Questions prepared for this interview panel. Use the AI Assistant above to add more.
            </p>
          </div>
        </div>

        {preparedQuestions.length > 0 ? (
          <div className="space-y-2">
            {preparedQuestions.map((q, idx) => (
              <div
                key={q.id || idx}
                className="flex items-start justify-between rounded-xl border border-zinc-200 bg-zinc-50/50 p-3 text-xs hover:border-zinc-300 transition-colors"
              >
                <div className="space-y-1 pr-3">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-zinc-900">Q{idx + 1}.</span>
                    <span className="font-semibold text-zinc-800">{q.question}</span>
                    <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[9px] font-bold uppercase text-zinc-600">
                      {q.category}
                    </span>
                  </div>
                  {q.evaluation_criteria && (
                    <div className="text-[11px] text-zinc-500 pl-4">
                      Criteria: {q.evaluation_criteria}
                    </div>
                  )}
                </div>

                {onRemoveQuestion && (
                  <button
                    onClick={() => onRemoveQuestion(q.id)}
                    className="text-zinc-400 hover:text-red-600 transition-colors shrink-0 text-xs font-semibold px-2"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-200 p-6 text-center text-xs text-zinc-400">
            No questions prepared yet. Click "Generate Questions" in the AI Assistant above to prepare relevant questions.
          </div>
        )}
      </div>
    </div>
  );
}
