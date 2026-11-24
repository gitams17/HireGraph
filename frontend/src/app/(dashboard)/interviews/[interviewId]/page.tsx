"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { InterviewDetail, InterviewStatus, PreparedQuestion } from "@/types";
import InterviewDetails from "@/components/interviews/InterviewDetails";
import AIQuestionAssistant from "@/components/interviews/AIQuestionAssistant";
import FeedbackForm from "@/components/interviews/FeedbackForm";
import InterviewTimeline from "@/components/interviews/InterviewTimeline";
import InterviewFormModal from "@/components/interviews/InterviewFormModal";

interface PageProps {
  params: Promise<{
    interviewId: string;
  }>;
}

export default function InterviewDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const interviewId = resolvedParams.interviewId;
  const router = useRouter();

  const [interview, setInterview] = useState<InterviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);

  const fetchInterview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<InterviewDetail>(`/api/v1/interviews/${interviewId}/`);
      setInterview(data);
    } catch {
      setError("Failed to load interview details. Please check permissions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterview();
  }, [interviewId]);

  const handleStatusUpdate = async (newStatus: InterviewStatus) => {
    if (!interview) return;
    try {
      await api.patch(`/api/v1/interviews/${interview.id}/`, { status: newStatus });
      fetchInterview();
    } catch {
      alert("Failed to update interview status.");
    }
  };

  const handleAddQuestion = async (newQuestion: PreparedQuestion) => {
    if (!interview) return;
    const existing = interview.prepared_questions || [];
    const updated = [...existing, newQuestion];
    try {
      await api.patch(`/api/v1/interviews/${interview.id}/`, { prepared_questions: updated });
      setInterview((prev) => (prev ? { ...prev, prepared_questions: updated } : prev));
    } catch {
      alert("Failed to update prepared questions.");
    }
  };

  const handleRemoveQuestion = async (qId: string) => {
    if (!interview) return;
    const updated = (interview.prepared_questions || []).filter((q) => q.id !== qId);
    try {
      await api.patch(`/api/v1/interviews/${interview.id}/`, { prepared_questions: updated });
      setInterview((prev) => (prev ? { ...prev, prepared_questions: updated } : prev));
    } catch {
      alert("Failed to remove question.");
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-zinc-900 border-r-transparent"></div>
          <p className="mt-3 text-xs text-zinc-500 font-medium">Loading interview cockpit…</p>
        </div>
      </div>
    );
  }

  if (error || !interview) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center space-y-3">
        <div className="text-2xl">⚠️</div>
        <h2 className="text-base font-bold text-red-900">{error || "Interview not found"}</h2>
        <p className="text-xs text-red-700">
          The requested interview could not be found or you do not have permission in this organisation.
        </p>
        <Link
          href="/interviews"
          className="inline-block rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800"
        >
          ← Return to Interviews List
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center space-x-2 text-xs text-zinc-500">
        <Link href="/interviews" className="hover:text-zinc-900">
          Interviews
        </Link>
        <span>/</span>
        <span className="font-semibold text-zinc-900 truncate">{interview.title}</span>
      </div>

      {/* Main Details Cockpit */}
      <InterviewDetails
        interview={interview}
        onStatusUpdate={handleStatusUpdate}
        onEditClick={() => setShowEditModal(true)}
      />

      {/* AI Interview Question Assistant */}
      <AIQuestionAssistant
        interviewId={interview.id}
        interviewType={interview.interview_type}
        onAddQuestion={handleAddQuestion}
      />

      {/* Feedback Form for Panel Members */}
      <FeedbackForm interview={interview} onSuccess={fetchInterview} />

      {/* Audit Timeline, Submitted Panel Evaluations & Questions Checklist */}
      <InterviewTimeline
        participants={interview.participants}
        feedbacks={interview.feedbacks}
        preparedQuestions={interview.prepared_questions || []}
        onRemoveQuestion={handleRemoveQuestion}
      />

      {/* Edit Schedule Modal */}
      <InterviewFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSuccess={fetchInterview}
        interviewToEdit={interview}
      />
    </div>
  );
}
