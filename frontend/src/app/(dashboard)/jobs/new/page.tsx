"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Organization } from "@/types";
import { JobForm } from "@/components/jobs/JobForm";

export default function NewJobPage() {
  const { user } = useAuth();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .get<{ results: Organization[] }>("/api/v1/organizations/")
      .then((data) => {
        const list = data.results ?? [];
        setOrgs(list);
        if (list.length > 0) setSelectedOrgId(list[0].id);
      })
      .catch(() => setError("Failed to load organisations."))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) {
    return <div className="py-16 text-center text-sm text-zinc-400">Loading…</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (orgs.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white py-16 text-center">
        <p className="text-sm text-zinc-500">
          You must belong to an organisation before creating jobs.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-900">New job requisition</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Fill in the details below to create a new hiring requisition.
        </p>
      </div>

      {/* Organisation selector (shown only when user belongs to multiple orgs) */}
      {orgs.length > 1 && (
        <div className="mb-6">
          <label className="mb-1.5 block text-sm font-medium text-zinc-700">
            Organisation
          </label>
          <select
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          >
            {orgs.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <JobForm organizationId={selectedOrgId} />
      </div>
    </div>
  );
}
