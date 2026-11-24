"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { WorkflowExecutionDetail } from "@/types";

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  execution: WorkflowExecutionDetail | null;
}

export default function ApprovalModal({
  isOpen,
  onClose,
  onSuccess,
  execution,
}: ApprovalModalProps) {
  const [decision, setDecision] = useState<"approved" | "rejected" | "negotiate">("approved");
  const [feedback, setFeedback] = useState("");
  const [counterSalary, setCounterSalary] = useState<number | "">("");
  const [candidateResponse, setCandidateResponse] = useState<"accepted" | "negotiation" | "rejected">("accepted");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !execution) return null;

  const isOfferGate = execution.current_step === "offer_approval_interrupt";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: Record<string, any> = {
        decision,
        feedback,
      };

      if (isOfferGate) {
        payload.candidate_response = candidateResponse;
        if (counterSalary) payload.counter_salary = Number(counterSalary);
        if (feedback) payload.negotiation_notes = feedback;
      }

      await api.post(`/api/v1/workflows/${execution.id}/resume/`, payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.data?.detail || "Failed to resume workflow decision.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl my-8 space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-zinc-900">
              {isOfferGate ? "Human Offer Approval & Candidate Terms" : "Review & Decide Job Description"}
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Thread: <span className="font-mono text-zinc-700">{execution.thread_id}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-colors"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Decision Selector */}
          <div>
            <label className="block font-semibold text-zinc-700 mb-1.5">
              Human Reviewer Decision *
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDecision("approved")}
                className={`rounded-lg border p-2.5 text-center font-bold transition-all ${
                  decision === "approved"
                    ? "bg-emerald-600 border-emerald-600 text-white"
                    : "bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-50"
                }`}
              >
                ✓ Approve & Advance
              </button>
              <button
                type="button"
                onClick={() => setDecision("rejected")}
                className={`rounded-lg border p-2.5 text-center font-bold transition-all ${
                  decision === "rejected"
                    ? "bg-red-600 border-red-600 text-white"
                    : "bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-50"
                }`}
              >
                ✕ Request Revision / Reject
              </button>
            </div>
          </div>

          {/* Feedback textarea */}
          <div>
            <label className="block font-semibold text-zinc-700 mb-1">
              {decision === "rejected" ? "Revision Feedback / Reason *" : "Reviewer Notes (Optional)"}
            </label>
            <textarea
              rows={3}
              required={decision === "rejected"}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder={
                decision === "rejected"
                  ? "Explain what requirements or compensation should be adjusted…"
                  : "Approval comments or sign-off notes…"
              }
              className="w-full rounded-lg border border-zinc-300 p-2.5 focus:border-zinc-900 focus:outline-none"
            />
          </div>

          {/* Specific Offer Gate controls */}
          {isOfferGate && decision === "approved" && (
            <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 space-y-3">
              <div>
                <label className="block font-semibold text-zinc-700 mb-1">
                  Candidate Offer Response Mode
                </label>
                <select
                  value={candidateResponse}
                  onChange={(e) => setCandidateResponse(e.target.value as any)}
                  className="w-full rounded-lg border border-zinc-300 bg-white p-2 focus:border-zinc-900 focus:outline-none"
                >
                  <option value="accepted">Accepted (Advances directly to Onboarding)</option>
                  <option value="negotiation">Negotiation (Enters Offer Revision loop)</option>
                  <option value="rejected">Rejected (Closes Application)</option>
                </select>
              </div>

              {candidateResponse === "negotiation" && (
                <div>
                  <label className="block font-semibold text-zinc-700 mb-1">
                    Candidate Counter Salary Proposal (USD)
                  </label>
                  <input
                    type="number"
                    value={counterSalary}
                    onChange={(e) => setCounterSalary(e.target.value ? Number(e.target.value) : "")}
                    placeholder="e.g. 155000"
                    className="w-full rounded-lg border border-zinc-300 bg-white p-2 focus:border-zinc-900 focus:outline-none"
                  />
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-3 border-t border-zinc-100">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-lg border border-zinc-200 px-4 py-2 font-semibold text-zinc-700 hover:bg-zinc-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-zinc-900 px-4 py-2 font-bold text-white hover:bg-zinc-800 disabled:opacity-50 transition-colors"
            >
              {loading ? "Resuming Workflow…" : "Submit Decision"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
