"use client";

import { useState } from "react";
import { api, extractApiErrors } from "@/lib/api";
import { Application, ApplicationStage, STAGE_LABELS, STAGE_ORDER } from "@/types";

interface StageSelectorProps {
  application: Application;
  onStageUpdated: (updatedApp: Application) => void;
}

export function StageSelector({ application, onStageUpdated }: StageSelectorProps) {
  const [selectedStage, setSelectedStage] = useState<ApplicationStage>(application.stage);
  const [rating, setRating] = useState<number>(application.rating || 0);
  const [notes, setNotes] = useState<string>("");
  const [rejectionReason, setRejectionReason] = useState<string>(application.rejection_reason || "");
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  async function handleUpdate() {
    setUpdating(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const payload: {
        stage: ApplicationStage;
        notes?: string;
        rating?: number;
        rejection_reason?: string;
      } = {
        stage: selectedStage,
        notes: notes.trim(),
      };

      if (rating > 0) payload.rating = rating;
      if (selectedStage === "rejected") payload.rejection_reason = rejectionReason.trim();

      const updated = await api.patch<Application>(
        `/api/v1/applications/${application.id}/stage/`,
        payload
      );
      setSuccessMsg(`Stage updated to ${STAGE_LABELS[selectedStage]}`);
      setNotes("");
      onStageUpdated(updated);
    } catch (err) {
      setError(extractApiErrors(err));
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-zinc-900 mb-4">Recruitment Stage & Actions</h3>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
          {successMsg}
        </div>
      )}

      {/* Stage Progression Bar */}
      <div className="mb-6">
        <label className="block text-xs font-medium text-zinc-500 mb-2">Stage</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {STAGE_ORDER.map((stage) => {
            const isCurrent = application.stage === stage;
            const isSelected = selectedStage === stage;
            return (
              <button
                key={stage}
                type="button"
                onClick={() => setSelectedStage(stage)}
                className={`rounded-lg border px-2.5 py-2 text-xs font-semibold text-center transition-all ${
                  isSelected
                    ? "border-zinc-900 bg-zinc-900 text-white shadow-sm"
                    : isCurrent
                    ? "border-zinc-400 bg-zinc-100 text-zinc-800"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:bg-zinc-50"
                }`}
              >
                {STAGE_LABELS[stage]}
                {isCurrent && !isSelected && (
                  <span className="block text-[10px] text-zinc-400 font-normal">Current</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Rating (1-5 stars) */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-zinc-500 mb-1.5">Candidate Rating</label>
        <div className="flex items-center space-x-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star === rating ? 0 : star)}
              className={`text-xl ${star <= rating ? "text-amber-400" : "text-zinc-200"} hover:text-amber-300 transition-colors`}
            >
              ★
            </button>
          ))}
          <span className="ml-2 text-xs text-zinc-400">
            {rating > 0 ? `${rating} / 5` : "Unrated"}
          </span>
        </div>
      </div>

      {/* Rejection reason (if rejected) */}
      {selectedStage === "rejected" && (
        <div className="mb-4">
          <label className="block text-xs font-medium text-zinc-500 mb-1">Rejection Reason</label>
          <input
            type="text"
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            placeholder="e.g. Lacks required distributed systems experience"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </div>
      )}

      {/* Transition Notes */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-zinc-500 mb-1">
          Stage Notes / Interview Feedback
        </label>
        <textarea
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add comments on candidate evaluation or reason for stage change..."
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleUpdate}
          disabled={updating || (selectedStage === application.stage && !notes.trim() && rating === (application.rating || 0))}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 disabled:opacity-40 transition-colors"
        >
          {updating ? "Updating…" : "Save stage change"}
        </button>
      </div>
    </div>
  );
}
