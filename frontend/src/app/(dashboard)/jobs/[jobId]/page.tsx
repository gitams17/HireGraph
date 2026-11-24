"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { JobRequisition, Organization } from "@/types";
import { JobDetails } from "@/components/jobs/JobDetails";
import { JobActions } from "@/components/jobs/JobActions";

interface JobDetailPageProps {
  params: Promise<{ jobId: string }>;
}

export default function JobDetailPage({ params }: JobDetailPageProps) {
  const { user } = useAuth();
  const [job, setJob] = useState<JobRequisition | null>(null);
  const [currentUserRole, setCurrentUserRole] = useState<Organization["current_user_role"]>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { jobId } = await params;
      try {
        const jobData = await api.get<JobRequisition>(`/api/v1/jobs/${jobId}/`);
        if (cancelled) return;
        setJob(jobData);

        // Fetch the org to discover current_user_role
        const orgData = await api.get<Organization>(
          `/api/v1/organizations/${jobData.organization}/`
        );
        if (!cancelled) setCurrentUserRole(orgData.current_user_role);
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
    <div className="max-w-3xl space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-zinc-500">
        <Link href="/jobs" className="hover:text-zinc-800 transition-colors">
          Jobs
        </Link>
        <span className="mx-2">›</span>
        <span className="text-zinc-700">{job.title}</span>
      </nav>

      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div className="flex-1" />
          <JobActions job={job} currentUserRole={currentUserRole} />
        </div>
        <JobDetails job={job} />
      </div>
    </div>
  );
}
