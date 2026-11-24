"use client";

import { useState } from "react";
import { ApprovalRequest } from "@/types";

interface ApprovalModalProps {
  request: ApprovalRequest;
  isOpen: boolean;
  onClose: () => void;
  onDecide: (action: "approve" | "reject", feedback: string) => Promise<void>;
}

export function ApprovalModal({
  request,
  isOpen,
  onClose,
  onDecide,
}: ApprovalModalProps) {
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAction = async (action: "approve" | "reject") => {
    if (action === "reject" && !feedback.trim()) {
      setError("Please provide feedback explaining why this job description was rejected.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onDecide(action, feedback);
      onClose();
    } catch (err: any) {
      setError(err?.data?.detail || "Failed to submit decision.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl space-y-5">
        <div className="border-b border-zinc-200 pb-3">
          <h3 className="text-lg font-bold text-zinc-900">Review Job Description</h3>
          <p className="text-xs text-zinc-500">
            {request.job_title} — Version {request.version_number}
          </p>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1">
            Manager Feedback
          </label>
          <textarea
            rows={4}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Required for rejection, optional for approval (e.g. Looks good, approved for publishing!)"
            className="w-full rounded-lg border border-zinc-300 p-3 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-zinc-100">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => handleAction("reject")}
            disabled={submitting}
            className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-100 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Processing…" : "Reject & Request Revision"}
          </button>
          <button
            type="button"
            onClick={() => handleAction("approve")}
            disabled={submitting}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Processing…" : "Approve & Publish"}
          </button>
        </div>
      </div>
    </div>
  );
}
