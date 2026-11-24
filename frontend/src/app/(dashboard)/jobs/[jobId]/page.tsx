"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import {
  ApprovalRequest,
  JobDescriptionVersion,
  JobRequisition,
  Organization,
  WorkflowExecution,
} from "@/types";
import { JobDetails } from "@/components/jobs/JobDetails";
import { JobActions } from "@/components/jobs/JobActions";
import { JobDescriptionView } from "@/components/jobs/JobDescriptionView";
import { JobDescriptionEditor } from "@/components/jobs/JobDescriptionEditor";
import { ApprovalModal } from "@/components/jobs/ApprovalModal";
import { WorkflowTimeline } from "@/components/jobs/WorkflowTimeline";

interface JobDetailPageProps {
  params: Promise<{ jobId: string }>;
}

export default function JobDetailPage({ params }: JobDetailPageProps) {
  const { user } = useAuth();
  const [jobId, setJobId] = useState<string>("");
  const [job, setJob] = useState<JobRequisition | null>(null);
  const [currentUserRole, setCurrentUserRole] = useState<Organization["current_user_role"]>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Phase 4 states
  const [activeTab, setActiveTab] = useState<"requirements" | "jd" | "workflow">("requirements");
  const [versions, setVersions] = useState<JobDescriptionVersion[]>([]);
  const [activeVersion, setActiveVersion] = useState<JobDescriptionVersion | null>(null);
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowExecution | null>(null);

  const [generating, setGenerating] = useState(false);
  const [editing, setEditing] = useState(false);
  const [isSubmittingApproval, setIsSubmittingApproval] = useState(false);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);

  const canManage = currentUserRole === "owner" || currentUserRole === "admin" || currentUserRole === "recruiter";
  const canApprove = currentUserRole === "owner" || currentUserRole === "admin" || currentUserRole === "hiring_manager";

  const fetchVersionsAndApprovals = useCallback(async (jid: string) => {
    try {
      // 1. Versions
      const vList = await api.get<JobDescriptionVersion[]>(`/api/v1/jobs/${jid}/versions/`);
      setVersions(vList);
      if (vList.length > 0) {
        setActiveVersion((curr) => curr ? vList.find((v) => v.id === curr.id) || vList[0] : vList[0]);
      }

      // 2. Pending Approvals
      const appData = await api.get<{ results?: ApprovalRequest[] } | ApprovalRequest[]>(
        `/api/v1/approvals/?job=${jid}&status=pending`
      );
      const appList = Array.isArray(appData) ? appData : (appData.results ?? []);
      setPendingApproval(appList.length > 0 ? appList[0] : null);

      // 3. Workflow Execution
      try {
        const wf = await api.get<WorkflowExecution>(`/api/v1/workflows/job-${jid}-jd/status/`);
        setWorkflow(wf);
      } catch {
        // No workflow execution yet
      }
    } catch {
      // Non-fatal
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { jobId: resolvedId } = await params;
      setJobId(resolvedId);
      try {
        const jobData = await api.get<JobRequisition>(`/api/v1/jobs/${resolvedId}/`);
        if (cancelled) return;
        setJob(jobData);

        const orgData = await api.get<Organization>(
          `/api/v1/organizations/${jobData.organization}/`
        );
        if (!cancelled) {
          setCurrentUserRole(orgData.current_user_role);
        }

        await fetchVersionsAndApprovals(resolvedId);
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
  }, [user, params, fetchVersionsAndApprovals]);

  const handleGenerateJD = async () => {
    if (!jobId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post(`/api/v1/jobs/${jobId}/generate-jd/`, {});
      await fetchVersionsAndApprovals(jobId);
      setActiveTab("jd");
    } catch (err: any) {
      setError(err?.data?.detail || "Failed to trigger AI generation.");
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveDraft = async (updated: Partial<JobDescriptionVersion>) => {
    if (!activeVersion || !jobId) return;
    try {
      const saved = await api.patch<JobDescriptionVersion>(
        `/api/v1/jobs/${jobId}/versions/${activeVersion.id}/`,
        updated
      );
      setActiveVersion(saved);
      setVersions((prev) => prev.map((v) => (v.id === saved.id ? saved : v)));
      setEditing(false);
    } catch {
      alert("Failed to save changes.");
    }
  };

  const handleSubmitApproval = async () => {
    if (!activeVersion || !jobId) return;
    setIsSubmittingApproval(true);
    try {
      await api.post(`/api/v1/jobs/${jobId}/versions/${activeVersion.id}/submit-approval/`, {});
      await fetchVersionsAndApprovals(jobId);
    } catch {
      alert("Failed to submit version for approval.");
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  const handleDecision = async (action: "approve" | "reject", feedback: string) => {
    if (!pendingApproval) return;
    await api.post(`/api/v1/approvals/${pendingApproval.id}/decide/`, {
      action,
      feedback,
    });
    // Refresh job status and versions
    const updatedJob = await api.get<JobRequisition>(`/api/v1/jobs/${jobId}/`);
    setJob(updatedJob);
    await fetchVersionsAndApprovals(jobId);
  };

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
    <div className="max-w-4xl space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-zinc-500">
        <Link href="/jobs" className="hover:text-zinc-800 transition-colors">
          Jobs
        </Link>
        <span className="mx-2">›</span>
        <span className="text-zinc-700 font-medium">{job.title}</span>
      </nav>

      {/* Top Banner for Pending Approvals */}
      {pendingApproval && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
          <div>
            <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-amber-900">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
              Approval Required: Version {pendingApproval.version_number}
            </span>
            <p className="mt-0.5 text-xs text-amber-700">
              Submitted by {pendingApproval.requested_by.full_name || pendingApproval.requested_by.email} on{" "}
              {new Date(pendingApproval.created_at).toLocaleDateString()}.
            </p>
          </div>
          {canApprove && (
            <button
              onClick={() => setIsApprovalModalOpen(true)}
              className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-700 shadow-sm transition-colors"
            >
              Review & Decide
            </button>
          )}
        </div>
      )}

      {/* Main Container */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        {/* Header Actions */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-zinc-100 pb-4">
          {/* Tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("requirements")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                activeTab === "requirements"
                  ? "bg-zinc-900 text-white shadow-sm"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              Job Requirements
            </button>
            <button
              onClick={() => setActiveTab("jd")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                activeTab === "jd"
                  ? "bg-zinc-900 text-white shadow-sm"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              AI Job Description ({versions.length})
            </button>
            <button
              onClick={() => setActiveTab("workflow")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                activeTab === "workflow"
                  ? "bg-zinc-900 text-white shadow-sm"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              Workflow History
            </button>
          </div>

          <div className="flex items-center gap-3">
            {canManage && (
              <button
                onClick={handleGenerateJD}
                disabled={generating}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
              >
                {generating ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Generating…
                  </>
                ) : (
                  <>
                    <span>✨</span>
                    <span>{versions.length > 0 ? "Regenerate JD" : "Generate with AI"}</span>
                  </>
                )}
              </button>
            )}
            <JobActions job={job} currentUserRole={currentUserRole} />
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "requirements" && <JobDetails job={job} />}

        {activeTab === "jd" && (
          <div>
            {editing && activeVersion ? (
              <JobDescriptionEditor
                version={activeVersion}
                onSave={handleSaveDraft}
                onCancel={() => setEditing(false)}
              />
            ) : (
              <JobDescriptionView
                versions={versions}
                activeVersion={activeVersion}
                onSelectVersion={(v) => setActiveVersion(v)}
                onEdit={() => setEditing(true)}
                canEdit={canManage}
                onSubmitApproval={handleSubmitApproval}
                isSubmittingApproval={isSubmittingApproval}
              />
            )}
          </div>
        )}

        {activeTab === "workflow" && (
          <div className="space-y-6">
            <div className="rounded-lg bg-zinc-50 p-4 border border-zinc-200 text-xs">
              <span className="font-semibold text-zinc-700">Thread ID: </span>
              <span className="font-mono text-zinc-900">job-{job.id}-jd</span>
              <span className="ml-4 font-semibold text-zinc-700">Status: </span>
              <span className="font-semibold text-zinc-900 capitalize">
                {workflow?.status || "Ready"}
              </span>
            </div>
            <WorkflowTimeline events={workflow?.events || []} />
          </div>
        )}
      </div>

      {/* Approval Modal */}
      {pendingApproval && (
        <ApprovalModal
          request={pendingApproval}
          isOpen={isApprovalModalOpen}
          onClose={() => setIsApprovalModalOpen(false)}
          onDecide={handleDecision}
        />
      )}
    </div>
  );
}
