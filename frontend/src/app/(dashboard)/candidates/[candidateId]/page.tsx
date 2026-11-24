"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, extractApiErrors } from "@/lib/api";
import { Candidate, JobRequisition, PaginatedResponse, Resume } from "@/types";
import { CandidateProfile } from "@/components/candidates/CandidateProfile";
import { ResumeUpload } from "@/components/candidates/ResumeUpload";

interface CandidateDetailPageProps {
  params: Promise<{ candidateId: string }>;
}

export default function CandidateDetailPage({ params }: CandidateDetailPageProps) {
  const [candidateId, setCandidateId] = useState<string>("");
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Link to Job Modal State
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [availableJobs, setAvailableJobs] = useState<JobRequisition[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [applyNotes, setApplyNotes] = useState("");
  const [submittingApply, setSubmittingApply] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { candidateId: cid } = await params;
      setCandidateId(cid);
      try {
        const data = await api.get<Candidate>(`/api/v1/candidates/${cid}/`);
        if (!cancelled) setCandidate(data);
      } catch {
        if (!cancelled) setError("Candidate not found or access denied.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params]);

  async function openApplyModal() {
    setIsApplyModalOpen(true);
    setApplyError(null);
    setApplySuccess(null);
    try {
      const res = await api.get<PaginatedResponse<JobRequisition>>(
        `/api/v1/jobs/?status=open&page_size=50`
      );
      setAvailableJobs(res.results || []);
      if (res.results && res.results.length > 0) {
        setSelectedJobId(res.results[0].id);
      }
    } catch {
      setApplyError("Failed to fetch open jobs.");
    }
  }

  async function handleCreateApplication(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedJobId) return;

    setSubmittingApply(true);
    setApplyError(null);

    try {
      await api.post("/api/v1/applications/", {
        candidate_id: candidateId,
        job_id: selectedJobId,
        notes: applyNotes.trim(),
      });

      setApplySuccess("Candidate successfully linked to job requisition!");
      // Refresh candidate details
      const refreshed = await api.get<Candidate>(`/api/v1/candidates/${candidateId}/`);
      setCandidate(refreshed);
      setTimeout(() => setIsApplyModalOpen(false), 1200);
    } catch (err) {
      setApplyError(extractApiErrors(err));
    } finally {
      setSubmittingApply(false);
    }
  }

  function handleResumeUploaded(newResume: Resume) {
    if (!candidate) return;
    setCandidate({
      ...candidate,
      resumes: [newResume, ...(candidate.resumes || [])],
      resume_count: (candidate.resume_count || 0) + 1,
    });
  }

  if (loading) {
    return <div className="py-20 text-center text-sm text-zinc-400">Loading candidate profile…</div>;
  }

  if (error || !candidate) {
    return (
      <div className="space-y-4">
        <Link href="/candidates" className="text-xs text-zinc-500 hover:text-zinc-800">
          ← Back to candidates
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error || "Candidate not found."}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2 text-xs text-zinc-400">
        <Link href="/candidates" className="hover:text-zinc-700">
          Candidates
        </Link>
        <span>/</span>
        <span className="text-zinc-600 font-medium">
          {candidate.full_name || `${candidate.first_name} ${candidate.last_name}`}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left: Main candidate details */}
        <div className="lg:col-span-2 space-y-6">
          <CandidateProfile candidate={candidate} onApplyJobClick={openApplyModal} />
        </div>

        {/* Right: Resumes & documents */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <ResumeUpload
            candidateId={candidate.id}
            resumes={candidate.resumes || []}
            onUploadSuccess={handleResumeUploaded}
          />
        </div>
      </div>

      {/* Link to Job Modal */}
      {isApplyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
              <h2 className="text-base font-bold text-zinc-900">Link Candidate to Job</h2>
              <button
                onClick={() => setIsApplyModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {applyError && (
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                {applyError}
              </div>
            )}
            {applySuccess && (
              <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
                {applySuccess}
              </div>
            )}

            <form onSubmit={handleCreateApplication} className="mt-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">
                  Select Open Job Requisition *
                </label>
                {availableJobs.length === 0 ? (
                  <p className="text-xs text-zinc-400">No open jobs found in this organisation.</p>
                ) : (
                  <select
                    value={selectedJobId}
                    onChange={(e) => setSelectedJobId(e.target.value)}
                    required
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  >
                    {availableJobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.title} ({job.department || "General"})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">
                  Initial Notes / Referral Info
                </label>
                <textarea
                  rows={3}
                  value={applyNotes}
                  onChange={(e) => setApplyNotes(e.target.value)}
                  placeholder="e.g. Sourced via LinkedIn; strong alignment with distributed systems."
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={() => setIsApplyModalOpen(false)}
                  className="rounded-lg border border-zinc-300 px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingApply || availableJobs.length === 0}
                  className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-700 disabled:opacity-50"
                >
                  {submittingApply ? "Creating…" : "Submit application"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
