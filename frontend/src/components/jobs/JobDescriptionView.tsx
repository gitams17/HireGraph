"use client";

import { useState } from "react";
import { JobDescriptionVersion, VERSION_STATUS_LABELS } from "@/types";

interface JobDescriptionViewProps {
  versions: JobDescriptionVersion[];
  activeVersion: JobDescriptionVersion | null;
  onSelectVersion: (version: JobDescriptionVersion) => void;
  onEdit: () => void;
  canEdit: boolean;
  onSubmitApproval: () => void;
  isSubmittingApproval: boolean;
}

const BADGE_STYLES: Record<string, string> = {
  draft: "bg-zinc-100 text-zinc-700 ring-zinc-300",
  pending_approval: "bg-amber-50 text-amber-700 ring-amber-300",
  approved: "bg-green-50 text-green-700 ring-green-300",
  rejected: "bg-red-50 text-red-700 ring-red-300",
};

export function JobDescriptionView({
  versions,
  activeVersion,
  onSelectVersion,
  onEdit,
  canEdit,
  onSubmitApproval,
  isSubmittingApproval,
}: JobDescriptionViewProps) {
  const [tab, setTab] = useState<"structured" | "raw">("structured");

  if (!activeVersion) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white py-12 text-center text-sm text-zinc-500">
        No job description generated yet. Click "Generate with AI" above to create the first draft.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Version Header & Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-200 pb-4">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-zinc-700">Version:</label>
          <select
            value={activeVersion.id}
            onChange={(e) => {
              const selected = versions.find((v) => v.id === e.target.value);
              if (selected) onSelectVersion(selected);
            }}
            className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm font-semibold text-zinc-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                v{v.version_number} — {VERSION_STATUS_LABELS[v.status]} (
                {new Date(v.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
              BADGE_STYLES[activeVersion.status] || "bg-zinc-100 text-zinc-700 ring-zinc-300"
            }`}
          >
            {VERSION_STATUS_LABELS[activeVersion.status]}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-0.5 text-xs">
            <button
              onClick={() => setTab("structured")}
              className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                tab === "structured"
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-800"
              }`}
            >
              Structured
            </button>
            <button
              onClick={() => setTab("raw")}
              className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                tab === "raw"
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-800"
              }`}
            >
              Markdown
            </button>
          </div>

          {/* Edit action */}
          {canEdit && activeVersion.status !== "approved" && (
            <button
              onClick={onEdit}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors"
            >
              Edit Draft
            </button>
          )}

          {/* Submit for Approval */}
          {canEdit && (activeVersion.status === "draft" || activeVersion.status === "rejected") && (
            <button
              onClick={onSubmitApproval}
              disabled={isSubmittingApproval}
              className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-700 disabled:opacity-50 transition-colors"
            >
              {isSubmittingApproval ? "Submitting…" : "Submit for Approval"}
            </button>
          )}
        </div>
      </div>

      {/* Content Rendering */}
      {tab === "structured" ? (
        <div className="space-y-6">
          <div>
            <h3 className="text-xl font-bold text-zinc-900">{activeVersion.title}</h3>
            {activeVersion.overview && (
              <p className="mt-2 text-sm leading-relaxed text-zinc-700">{activeVersion.overview}</p>
            )}
          </div>

          {activeVersion.responsibilities.length > 0 && (
            <section>
              <h4 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
                Key Responsibilities
              </h4>
              <ul className="mt-2 ml-5 list-disc space-y-1 text-sm text-zinc-800">
                {activeVersion.responsibilities.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </section>
          )}

          {activeVersion.required_qualifications.length > 0 && (
            <section>
              <h4 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
                Required Qualifications
              </h4>
              <ul className="mt-2 ml-5 list-disc space-y-1 text-sm text-zinc-800">
                {activeVersion.required_qualifications.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </section>
          )}

          {activeVersion.preferred_qualifications.length > 0 && (
            <section>
              <h4 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
                Preferred Qualifications
              </h4>
              <ul className="mt-2 ml-5 list-disc space-y-1 text-sm text-zinc-800">
                {activeVersion.preferred_qualifications.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </section>
          )}

          {activeVersion.benefits.length > 0 && (
            <section>
              <h4 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
                What We Offer
              </h4>
              <ul className="mt-2 ml-5 list-disc space-y-1 text-sm text-zinc-800">
                {activeVersion.benefits.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      ) : (
        <pre className="whitespace-pre-wrap rounded-lg bg-zinc-900 p-4 text-xs font-mono text-zinc-100">
          {activeVersion.raw_content || "No raw markdown content available."}
        </pre>
      )}
    </div>
  );
}
