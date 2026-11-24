"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type {
  JobRequisition,
  PaginatedResponse,
  WorkflowDashboardMetrics,
  WorkflowExecutionDetail,
} from "@/types";
import WorkflowMetrics from "@/components/workflows/WorkflowMetrics";
import ExecutionTable from "@/components/workflows/ExecutionTable";
import ApprovalModal from "@/components/workflows/ApprovalModal";
import OnboardingList from "@/components/workflows/OnboardingList";

export default function WorkflowsPage() {
  const [metrics, setMetrics] = useState<WorkflowDashboardMetrics | null>(null);
  const [executions, setExecutions] = useState<WorkflowExecutionDetail[]>([]);
  const [jobs, setJobs] = useState<JobRequisition[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"workflows" | "onboarding">("workflows");

  // Approval Modal state
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecutionDetail | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);

  // Trigger New Workflow Modal state
  const [showStartModal, setShowStartModal] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [minApplicants, setMinApplicants] = useState(1);
  const [startLoading, setStartLoading] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchDashboardData = useCallback(async (q: string, st: string, p: number) => {
    setLoading(true);
    try {
      const [mRes, eRes] = await Promise.all([
        api.get<WorkflowDashboardMetrics>("/api/v1/workflows/dashboard/"),
        api.get<PaginatedResponse<WorkflowExecutionDetail>>(
          `/api/v1/workflows/?${new URLSearchParams({
            search: q,
            status: st,
            page: String(p),
          }).toString()}`
        ),
      ]);
      setMetrics(mRes);
      setExecutions(eRes.results);
    } catch {
      // Error handling
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(
      () => fetchDashboardData(search, statusFilter, page),
      300
    );
    return () => clearTimeout(debounceRef.current);
  }, [search, statusFilter, page, fetchDashboardData]);

  useEffect(() => {
    // Load jobs for starter modal
    api
      .get<PaginatedResponse<JobRequisition>>("/api/v1/jobs/?page_size=50")
      .then((res) => {
        setJobs(res.results);
        if (res.results.length > 0) setSelectedJobId(res.results[0].id);
      })
      .catch(() => setJobs([]));
  }, []);

  const handleStartWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedJobId) return;
    setStartLoading(true);
    try {
      await api.post("/api/v1/workflows/recruitment/start/", {
        job_id: selectedJobId,
        minimum_applicants: minApplicants,
      });
      setShowStartModal(false);
      fetchDashboardData(search, statusFilter, page);
    } catch {
      alert("Failed to start recruitment workflow.");
    } finally {
      setStartLoading(false);
    }
  };

  const handleRetry = async (exec: WorkflowExecutionDetail) => {
    try {
      await api.post(`/api/v1/workflows/${exec.id}/retry/`, {});
      fetchDashboardData(search, statusFilter, page);
    } catch {
      alert("Failed to retry execution.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">Workflow Automation</h1>
          <p className="text-xs text-zinc-500 mt-1">
            Durable LangGraph state machines, human decision gates, scheduled monitoring, and automated onboarding.
          </p>
        </div>

        <button
          onClick={() => setShowStartModal(true)}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors shadow-sm"
        >
          + Start Recruitment Workflow
        </button>
      </div>

      {/* Metrics Row */}
      <WorkflowMetrics metrics={metrics} loading={loading} />

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-zinc-200 pb-2">
        <button
          onClick={() => setActiveTab("workflows")}
          className={`rounded-lg px-4 py-2 text-xs font-bold transition-colors ${
            activeTab === "workflows"
              ? "bg-zinc-900 text-white"
              : "text-zinc-600 hover:bg-zinc-100"
          }`}
        >
          Active Workflows & Executions
        </button>
        <button
          onClick={() => setActiveTab("onboarding")}
          className={`rounded-lg px-4 py-2 text-xs font-bold transition-colors ${
            activeTab === "onboarding"
              ? "bg-zinc-900 text-white"
              : "text-zinc-600 hover:bg-zinc-100"
          }`}
        >
          Candidate Onboarding Checklists
        </button>
      </div>

      {activeTab === "workflows" ? (
        <div className="space-y-4">
          {/* Filter and Search Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white p-3 shadow-sm">
            <div className="flex flex-wrap items-center gap-2">
              {[
                { label: "All", value: "" },
                { label: "Running", value: "running" },
                { label: "Awaiting Approval", value: "interrupted" },
                { label: "Failed", value: "failed" },
                { label: "Completed", value: "completed" },
              ].map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => {
                    setStatusFilter(tab.value);
                    setPage(1);
                  }}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    statusFilter === tab.value
                      ? "bg-zinc-900 text-white"
                      : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="w-full sm:w-64">
              <input
                type="text"
                placeholder="Search thread or job…"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs focus:border-zinc-900 focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          {/* Execution Table */}
          <div className="rounded-2xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
            <ExecutionTable
              executions={executions}
              loading={loading}
              onResumeClick={(exec) => {
                setSelectedExecution(exec);
                setShowApprovalModal(true);
              }}
              onRetryClick={handleRetry}
            />
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="border-b border-zinc-100 pb-3 mb-4">
            <h2 className="text-base font-bold text-zinc-900">Pre-Boarding & Onboarding Operations</h2>
            <p className="text-xs text-zinc-500">
              Checklists spawned automatically following candidate offer acceptance.
            </p>
          </div>
          <OnboardingList />
        </div>
      )}

      {/* Human Approval Gate Modal */}
      <ApprovalModal
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        onSuccess={() => fetchDashboardData(search, statusFilter, page)}
        execution={selectedExecution}
      />

      {/* Start Recruitment Workflow Modal */}
      {showStartModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <h2 className="text-base font-bold text-zinc-900">Start Recruitment Pipeline</h2>
              <button
                onClick={() => setShowStartModal(false)}
                className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-100"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleStartWorkflow} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-zinc-700 mb-1">
                  Target Job Requisition *
                </label>
                <select
                  required
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="w-full rounded-lg border border-zinc-300 p-2.5 focus:border-zinc-900 focus:outline-none"
                >
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} — {job.department} ({job.status})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-zinc-700 mb-1">
                  Applicant Volume Threshold (Minimum applicants before screening)
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={minApplicants}
                  onChange={(e) => setMinApplicants(Number(e.target.value))}
                  className="w-full rounded-lg border border-zinc-300 p-2.5 focus:border-zinc-900 focus:outline-none"
                />
                <p className="text-[10px] text-zinc-400 mt-1">
                  If volume is below this count, monitoring will alert recruiter and trigger JD revision.
                </p>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={() => setShowStartModal(false)}
                  className="rounded-lg border border-zinc-200 px-4 py-2 font-semibold text-zinc-700 hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={startLoading}
                  className="rounded-lg bg-zinc-900 px-4 py-2 font-bold text-white hover:bg-zinc-800 disabled:opacity-50"
                >
                  {startLoading ? "Starting…" : "Start Pipeline"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
