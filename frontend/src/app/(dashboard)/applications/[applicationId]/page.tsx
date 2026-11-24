"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Application, STAGE_COLORS, STAGE_LABELS } from "@/types";
import { StageSelector } from "@/components/applications/StageSelector";
import { ApplicationTimeline } from "@/components/applications/ApplicationTimeline";

interface ApplicationDetailPageProps {
  params: Promise<{ applicationId: string }>;
}

export default function ApplicationDetailPage({ params }: ApplicationDetailPageProps) {
  const [applicationId, setApplicationId] = useState<string>("");
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { applicationId: aid } = await params;
      setApplicationId(aid);
      try {
        const data = await api.get<Application>(`/api/v1/applications/${aid}/`);
        if (!cancelled) setApplication(data);
      } catch {
        if (!cancelled) setError("Application not found or access denied.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params]);

  function handleStageUpdated(updated: Application) {
    setApplication(updated);
  }

  if (loading) {
    return <div className="py-20 text-center text-sm text-zinc-400">Loading application details…</div>;
  }

  if (error || !application) {
    return (
      <div className="space-y-4">
        <Link href="/applications" className="text-xs text-zinc-500 hover:text-zinc-800">
          ← Back to applications
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error || "Application not found."}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-2 text-xs text-zinc-400">
        <Link href="/applications" className="hover:text-zinc-700">
          Applications
        </Link>
        <span>/</span>
        <span className="text-zinc-600 font-medium">
          {application.candidate?.full_name || application.candidate_name}
        </span>
      </div>

      {/* Header card */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-zinc-900">
                {application.candidate?.full_name || application.candidate_name}
              </h1>
              <span
                className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                  STAGE_COLORS[application.stage] || "bg-zinc-100 text-zinc-600"
                }`}
              >
                {STAGE_LABELS[application.stage] || application.stage}
              </span>
            </div>
            <p className="mt-1 text-sm text-zinc-500">
              Applying for{" "}
              <Link
                href={`/jobs/${application.job?.id || application.job_id}`}
                className="font-semibold text-zinc-900 hover:underline"
              >
                {application.job?.title || application.job_title}
              </Link>
              {application.job?.department ? ` • ${application.job.department}` : ""}
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              href={`/candidates/${application.candidate?.id || application.candidate_id}`}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors"
            >
              View Full Profile →
            </Link>
          </div>
        </div>

        {/* Candidate & Job Summary grid */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 border-t border-zinc-100 pt-5 text-sm">
          <div>
            <span className="block text-xs font-medium text-zinc-400">Email</span>
            <span className="text-zinc-800">{application.candidate?.email || application.candidate_email}</span>
          </div>
          <div>
            <span className="block text-xs font-medium text-zinc-400">Current Role</span>
            <span className="text-zinc-800">
              {application.candidate?.current_title || application.candidate_title || "—"}
            </span>
          </div>
          <div>
            <span className="block text-xs font-medium text-zinc-400">Current Company</span>
            <span className="text-zinc-800">
              {application.candidate?.current_company || application.candidate_company || "—"}
            </span>
          </div>
          <div>
            <span className="block text-xs font-medium text-zinc-400">Rating</span>
            <span className="text-amber-500 font-semibold">
              {application.rating ? `${"★".repeat(application.rating)} (${application.rating}/5)` : "Unrated"}
            </span>
          </div>
        </div>

        {/* Resume attached */}
        {application.resume && (
          <div className="mt-5 border-t border-zinc-100 pt-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-zinc-400">Attached Resume:</span>
              <span className="text-sm font-semibold text-zinc-800">
                {application.resume.file_name}
              </span>
            </div>
            <a
              href={application.resume.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md border border-zinc-300 bg-zinc-50 px-3 py-1 text-xs font-semibold text-zinc-700 hover:bg-zinc-100"
            >
              Download resume
            </a>
          </div>
        )}

        {/* Rejection reason */}
        {application.rejection_reason && (
          <div className="mt-4 rounded-lg bg-red-50 border border-red-200 p-3 text-xs text-red-700">
            <strong>Rejection Reason:</strong> {application.rejection_reason}
          </div>
        )}
      </div>

      {/* Stage Controller */}
      <StageSelector application={application} onStageUpdated={handleStageUpdated} />

      {/* Audit Timeline */}
      <ApplicationTimeline events={application.events || []} />
    </div>
  );
}
