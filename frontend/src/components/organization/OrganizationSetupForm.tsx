"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, extractApiErrors } from "@/lib/api";
import type { Organization } from "@/types";

interface Props {
  /** Called with the newly created org when the form succeeds. */
  onSuccess?: (org: Organization) => void;
}

export default function OrganizationSetupForm({ onSuccess }: Props) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const org = await api.post<Organization>("/api/v1/organizations/", {
        name,
      });
      if (onSuccess) {
        onSuccess(org);
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(extractApiErrors(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">
          Organisation name
        </label>
        <input
          type="text"
          required
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setError("");
          }}
          className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-400"
          placeholder="Acme Corp"
        />
        <p className="mt-1 text-xs text-zinc-400">
          A URL-friendly slug will be generated automatically.
        </p>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 transition-colors"
      >
        {submitting ? "Creating…" : "Create organisation"}
      </button>
    </form>
  );
}
