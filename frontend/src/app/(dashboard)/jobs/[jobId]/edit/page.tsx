"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { JobRequisition } from "@/types";
import { JobForm } from "@/components/jobs/JobForm";

interface EditJobPageProps {
  params: Promise<{ jobId: string }>;
}

export default function EditJobPage({ params }: EditJobPageProps) {
  const { user } = useAuth();
  const [job, setJob] = useState<JobRequisition | null>(null);
  const [jobId, setJobId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { jobId: id } = await params;
      setJobId(id);
      try {
        const data = await api.get<JobRequisition>(`/api/v1/jobs/${id}/`);
        if (!cancelled) setJob(data);
      } catch {
        if (!cancelled) setError("Job not found or access denied.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (user) load();
    return () => {
      cancelled = true;
    };
  }, [user, params]);

  if (loading) {
    return <div className="py-16 text-center text-sm text-zinc-400">Loading…</div>;
  }

  if (error || !job) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error ?? "Job not found."}
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-zinc-500">
        <Link href="/jobs" className="hover:text-zinc-800 transition-colors">
          Jobs
        </Link>
        <span className="mx-2">›</span>
        <Link href={`/jobs/${jobId}`} className="hover:text-zinc-800 transition-colors">
          {job.title}
        </Link>
        <span className="mx-2">›</span>
        <span className="text-zinc-700">Edit</span>
      </nav>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-900">Edit job requisition</h1>
        <p className="mt-1 text-sm text-zinc-500">Update the details below and save your changes.</p>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <JobForm
          organizationId={job.organization}
          initialData={job}
          jobId={jobId}
        />
      </div>
    </div>
  );
}
