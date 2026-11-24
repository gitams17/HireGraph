"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api, extractApiErrors } from "@/lib/api";
import { Application, ApplicationStage, JobRequisition, PaginatedResponse } from "@/types";
import { ApplicationPipeline } from "@/components/applications/ApplicationPipeline";

export default function PipelinePage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [jobs, setJobs] = useState<JobRequisition[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApplications = useCallback(async (jobId: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (jobId) params.set("job", jobId);
      params.set("page_size", "100"); // View up to 100 in pipeline
      const res = await api.get<PaginatedResponse<Application>>(
        `/api/v1/applications/?${params.toString()}`
      );
      setApplications(res.results || []);
    } catch {
      setError("Failed to load pipeline.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApplications(selectedJob);
  }, [selectedJob, fetchApplications]);

  useEffect(() => {
    api
      .get<PaginatedResponse<JobRequisition>>("/api/v1/jobs/?page_size=100")
      .then((data) => setJobs(data.results || []))
      .catch(() => {});
  }, []);

  async function handleAdvance(app: Application, nextStage: ApplicationStage) {
    try {
      const updated = await api.patch<Application>(`/api/v1/applications/${app.id}/stage/`, {
        stage: nextStage,
        notes: `Advanced to ${nextStage} via Pipeline Board`,
      });
      setApplications((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert(`Could not advance stage: ${extractApiErrors(err)}`);
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-zinc-400 mb-1">
            <Link href="/applications" className="hover:text-zinc-700">
              Applications
            </Link>
            <span>/</span>
            <span className="text-zinc-600 font-medium">Pipeline Board</span>
          </div>
          <h1 className="text-2xl font-bold text-zinc-900">Recruitment Pipeline</h1>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          >
            <option value="">All Requisitions</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>

          <Link
            href="/applications"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
          >
            List View
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-20 text-center text-sm text-zinc-400">Loading pipeline board…</div>
      ) : (
        <ApplicationPipeline applications={applications} onAdvance={handleAdvance} />
      )}
    </div>
  );
}
