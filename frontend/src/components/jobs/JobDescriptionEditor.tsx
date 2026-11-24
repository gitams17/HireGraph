"use client";

import { useState } from "react";
import { JobDescriptionVersion } from "@/types";

interface JobDescriptionEditorProps {
  version: JobDescriptionVersion;
  onSave: (updated: Partial<JobDescriptionVersion>) => Promise<void>;
  onCancel: () => void;
}

export function JobDescriptionEditor({
  version,
  onSave,
  onCancel,
}: JobDescriptionEditorProps) {
  const [title, setTitle] = useState(version.title);
  const [overview, setOverview] = useState(version.overview);
  const [responsibilities, setResponsibilities] = useState(version.responsibilities.join("\n"));
  const [requiredQuals, setRequiredQuals] = useState(version.required_qualifications.join("\n"));
  const [preferredQuals, setPreferredQuals] = useState(version.preferred_qualifications.join("\n"));
  const [benefits, setBenefits] = useState(version.benefits.join("\n"));
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        title,
        overview,
        responsibilities: responsibilities.split("\n").map((s) => s.trim()).filter(Boolean),
        required_qualifications: requiredQuals.split("\n").map((s) => s.trim()).filter(Boolean),
        preferred_qualifications: preferredQuals.split("\n").map((s) => s.trim()).filter(Boolean),
        benefits: benefits.split("\n").map((s) => s.trim()).filter(Boolean),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-xl border border-zinc-200 bg-white p-6">
      <div className="border-b border-zinc-200 pb-3">
        <h3 className="text-lg font-bold text-zinc-900">Edit Version {version.version_number}</h3>
        <p className="text-xs text-zinc-500">Make changes to the draft before sending for approval.</p>
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">
          Job Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">
          Overview
        </label>
        <textarea
          rows={4}
          value={overview}
          onChange={(e) => setOverview(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">
          Responsibilities (one per line)
        </label>
        <textarea
          rows={4}
          value={responsibilities}
          onChange={(e) => setResponsibilities(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">
          Required Qualifications (one per line)
        </label>
        <textarea
          rows={4}
          value={requiredQuals}
          onChange={(e) => setRequiredQuals(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">
          Preferred Qualifications (one per line)
        </label>
        <textarea
          rows={3}
          value={preferredQuals}
          onChange={(e) => setPreferredQuals(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600 mb-1">
          Benefits & Perks (one per line)
        </label>
        <textarea
          rows={3}
          value={benefits}
          onChange={(e) => setBenefits(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      <div className="flex items-center gap-3 pt-2">
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving…" : "Save Changes"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
