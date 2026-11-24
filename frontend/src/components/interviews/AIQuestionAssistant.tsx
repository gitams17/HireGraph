"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { PreparedQuestion, SuggestedQuestion, SuggestedQuestionsResponse } from "@/types";

interface AIQuestionAssistantProps {
  interviewId: string;
  interviewType: string;
  onAddQuestion: (question: PreparedQuestion) => void;
}

export default function AIQuestionAssistant({
  interviewId,
  interviewType,
  onAddQuestion,
}: AIQuestionAssistantProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<SuggestedQuestionsResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"technical" | "behavioural" | "project" | "competency">("technical");
  const [focusInput, setFocusInput] = useState("");
  const [addedIds, setAddedIds] = useState<Set<string>>(new Set());

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const focusAreas = focusInput
        ? focusInput.split(",").map((s) => s.trim()).filter(Boolean)
        : [];
      const res = await api.post<SuggestedQuestionsResponse>(
        `/api/v1/interviews/${interviewId}/generate-questions/`,
        {
          focus_areas: focusAreas,
          interview_type: interviewType,
        }
      );
      setQuestions(res);
    } catch {
      setError("Failed to generate AI interview questions. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = (q: SuggestedQuestion) => {
    onAddQuestion({
      id: q.id,
      question: q.question,
      category: q.category,
      evaluation_criteria: q.evaluation_criteria,
      notes: q.follow_up_hint,
    });
    setAddedIds((prev) => new Set(prev).add(q.id));
  };

  const currentQuestions: SuggestedQuestion[] = questions
    ? activeTab === "technical"
      ? questions.technical_questions
      : activeTab === "behavioural"
      ? questions.behavioural_questions
      : activeTab === "project"
      ? questions.project_questions
      : questions.competency_questions
    : [];

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-base font-bold text-zinc-900">✨ AI Interview Assistant</h2>
            <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700">
              LangGraph & LLM Assisted
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-0.5">
            Generate tailored technical, behavioural, and project-based questions grounded in the job requirements and candidate profile.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-white hover:bg-zinc-800 disabled:opacity-50 transition-colors shrink-0"
        >
          {loading ? "Generating Questions…" : questions ? "Regenerate Questions" : "Generate Questions"}
        </button>
      </div>

      {/* Focus Area input */}
      <div className="flex items-center space-x-2">
        <label className="text-xs font-semibold text-zinc-600 shrink-0">Focus Areas (Optional):</label>
        <input
          type="text"
          value={focusInput}
          onChange={(e) => setFocusInput(e.target.value)}
          placeholder="e.g. Distributed Caching, High Concurrency, Conflict Management"
          className="flex-1 rounded-lg border border-zinc-200 px-3 py-1.5 text-xs focus:border-zinc-900 focus:outline-none"
        />
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-700">
          {error}
        </div>
      )}

      {/* Tabs */}
      {questions && (
        <div className="space-y-4">
          <div className="flex space-x-2 border-b border-zinc-200 pb-2">
            {[
              { key: "technical", label: "Technical Depth", count: questions.technical_questions.length },
              { key: "behavioural", label: "Behavioural", count: questions.behavioural_questions.length },
              { key: "project", label: "Project Deep-Dives", count: questions.project_questions.length },
              { key: "competency", label: "Role Competency", count: questions.competency_questions.length },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                  activeTab === tab.key
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-600 hover:bg-zinc-100"
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-3">
            {currentQuestions.map((q) => {
              const isAdded = addedIds.has(q.id);
              return (
                <div
                  key={q.id}
                  className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-4 space-y-2 hover:border-zinc-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="font-semibold text-xs text-zinc-900 leading-relaxed">
                      {q.question}
                    </div>
                    <button
                      onClick={() => handleAdd(q)}
                      disabled={isAdded}
                      className={`rounded-lg px-3 py-1 text-[11px] font-bold shrink-0 transition-colors ${
                        isAdded
                          ? "bg-emerald-100 text-emerald-800 cursor-default"
                          : "bg-white border border-zinc-300 text-zinc-800 hover:bg-zinc-100"
                      }`}
                    >
                      {isAdded ? "✓ Added" : "+ Add to Checklist"}
                    </button>
                  </div>

                  <div className="text-[11px] text-zinc-600 bg-white p-2.5 rounded-lg border border-zinc-100 space-y-1">
                    <div>
                      <span className="font-bold text-zinc-800">Evaluation Criteria:</span>{" "}
                      {q.evaluation_criteria}
                    </div>
                    {q.follow_up_hint && (
                      <div className="text-zinc-500 italic">
                        <span className="font-semibold text-zinc-700">Follow-up Probe:</span>{" "}
                        {q.follow_up_hint}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
