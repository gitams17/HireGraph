"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Application, JobRequisition, PaginatedResponse, STAGE_COLORS, STAGE_LABELS, STAGE_ORDER } from "@/types";

export default function ApplicationsPage() {
  const [applicationsData, setApplicationsData] = useState<PaginatedResponse<Application> | null>(null);
  const [jobs, setJobs] = useState<JobRequisition[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>("");
  const [selectedStage, setSelectedStage] = useState<string>("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchApplications = useCallback(async (q: string, jid: string, stg: string, p: number) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("search", q);
      if (jid) params.set("job", jid);
      if (stg) params.set("stage", stg);
      params.set("page", String(p));

      const res = await api.get<PaginatedResponse<Application>>(
        `/api/v1/applications/?${params.toString()}`
      );
      setApplicationsData(res);
    } catch {
      setError("Failed to load applications.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(
      () => fetchApplications(search, selectedJob, selectedStage, page),
      300
    );
    return () => clearTimeout(debounceRef.current);
  }, [search, selectedJob, selectedStage, page, fetchApplications]);

  // Load jobs for filter
  useEffect(() => {
    api
      .get<PaginatedResponse<JobRequisition>>("/api/v1/jobs/?page_size=100")
      .then((data) => setJobs(data.results || []))
      .catch(() => {});
  }, []);

  const totalPages = applicationsData ? Math.ceil(applicationsData.count / 20) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Applications</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {applicationsData ? `${applicationsData.count} active candidate applications` : "Track candidate progress"}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/applications/pipeline"
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors"
          >
            📊 Pipeline Board
          </Link>
          <Link
            href="/candidates"
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 transition-colors"
          >
            + New application
          </Link>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-xl border border-zinc-200">
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Search candidate name or job title..."
          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-900 w-64 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />

        <select
          value={selectedJob}
          onChange={(e) => {
            setSelectedJob(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          <option value="">All Jobs</option>
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title}
            </option>
          ))}
        </select>

        <select
          value={selectedStage}
          onChange={(e) => {
            setSelectedStage(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          <option value="">All Stages</option>
          {STAGE_ORDER.map((stage) => (
            <option key={stage} value={stage}>
              {STAGE_LABELS[stage]}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-sm text-zinc-400">Loading applications…</div>
      ) : !applicationsData || applicationsData.results.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white py-16 text-center">
          <p className="text-sm font-medium text-zinc-600">No applications match your filter.</p>
          <p className="mt-1 text-xs text-zinc-400">
            Submit applications from the Candidates directory or adjust your filters.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                <tr>
                  <th className="px-6 py-3.5">Candidate</th>
                  <th className="px-6 py-3.5">Job Requisition</th>
                  <th className="px-6 py-3.5">Stage</th>
                  <th className="px-6 py-3.5">Rating</th>
                  <th className="px-6 py-3.5">Applied Date</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 text-zinc-700">
                {applicationsData.results.map((app) => (
                  <tr key={app.id} className="hover:bg-zinc-50/70 transition-colors">
                    <td className="px-6 py-4">
                      <Link
                        href={`/candidates/${app.candidate_id}`}
                        className="font-semibold text-zinc-900 hover:underline block"
                      >
                        {app.candidate_name}
                      </Link>
                      <span className="text-xs text-zinc-400 block mt-0.5">
                        {app.candidate_email}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-zinc-800">{app.job_title}</div>
                      <div className="text-xs text-zinc-500">{app.job_department || "General"}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                          STAGE_COLORS[app.stage] || "bg-zinc-100 text-zinc-600"
                        }`}
                      >
                        {STAGE_LABELS[app.stage] || app.stage}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {app.rating ? (
                        <span className="text-amber-500 text-sm font-semibold">
                          {"★".repeat(app.rating)}
                        </span>
                      ) : (
                        <span className="text-xs text-zinc-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-zinc-500">
                      {new Date(app.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <Link
                        href={`/applications/${app.id}`}
                        className="text-xs font-semibold text-zinc-900 hover:underline"
                      >
                        Review & stage →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-zinc-100 pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-50 disabled:opacity-40"
          >
            ← Previous
          </button>
          <span className="text-xs text-zinc-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-50 disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
