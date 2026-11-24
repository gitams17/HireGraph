"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { WorkflowExecutionDetail } from "@/types";
import WorkflowGraphViewer from "@/components/workflows/WorkflowGraphViewer";
import ApprovalModal from "@/components/workflows/ApprovalModal";

interface PageProps {
  params: Promise<{
    executionId: string;
  }>;
}

export default function WorkflowExecutionDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const executionId = resolvedParams.executionId;

  const [execution, setExecution] = useState<WorkflowExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const fetchExecution = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<WorkflowExecutionDetail>(`/api/v1/workflows/${executionId}/`);
      setExecution(data);
    } catch {
      setError("Failed to load workflow execution details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecution();
  }, [executionId]);

  const handleRetry = async () => {
    if (!execution) return;
    setRetrying(true);
    try {
      await api.post(`/api/v1/workflows/${execution.id}/retry/`, {});
      fetchExecution();
    } catch {
      alert("Failed to retry execution.");
    } finally {
      setRetrying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-zinc-900 border-r-transparent"></div>
          <p className="mt-3 text-xs text-zinc-500 font-medium">Loading workflow cockpit…</p>
        </div>
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center space-y-3">
        <div className="text-2xl">⚠️</div>
        <h2 className="text-base font-bold text-red-900">{error || "Execution not found"}</h2>
        <p className="text-xs text-red-700">
          The requested execution could not be found or you do not have permission in this organisation.
        </p>
        <Link
          href="/workflows"
          className="inline-block rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800"
        >
          ← Return to Workflows
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "interrupted":
        return "bg-amber-50 text-amber-800 border-amber-300 animate-pulse";
      case "completed":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "failed":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-zinc-100 text-zinc-700 border-zinc-200";
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center space-x-2 text-xs text-zinc-500">
        <Link href="/workflows" className="hover:text-zinc-900">
          Workflows
        </Link>
        <span>/</span>
        <span className="font-semibold text-zinc-900 truncate">{execution.thread_id}</span>
      </div>

      {/* Header Bar */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-zinc-900">
                {execution.workflow_type.replace("_", " ")} Execution
              </h1>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold uppercase ${getStatusBadge(execution.status)}`}>
                {execution.status === "interrupted" ? "Awaiting Decision" : execution.status}
              </span>
            </div>
            <p className="text-xs text-zinc-500 mt-1 font-mono">
              Thread ID: {execution.thread_id} • Job: {execution.job_title}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {execution.status === "interrupted" && (
              <button
                onClick={() => setShowApprovalModal(true)}
                className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-bold text-white hover:bg-amber-700 transition-colors shadow-sm"
              >
                ⚡ Review & Decide
              </button>
            )}
            {execution.status === "failed" && (
              <button
                onClick={handleRetry}
                disabled={retrying}
                className="rounded-lg bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-700 transition-colors shadow-sm disabled:opacity-50"
              >
                {retrying ? "Retrying…" : "↻ Retry from Checkpoint"}
              </button>
            )}
            <Link
              href="/workflows"
              className="rounded-lg border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
            >
              All Workflows
            </Link>
          </div>
        </div>

        {/* Error message if failed */}
        {execution.error_message && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">
            <span className="font-bold">Execution Error: </span>
            {execution.error_message}
          </div>
        )}
      </div>

      {/* Visual LangGraph Pipeline Viewer */}
      <WorkflowGraphViewer execution={execution} />

      {/* State Snapshot Inspector */}
      {execution.state_snapshot && Object.keys(execution.state_snapshot).length > 0 && (
        <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-zinc-900">Checkpoint State Variables</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {Object.entries(execution.state_snapshot).map(([key, val]) => (
              <div key={key} className="rounded-xl border border-zinc-100 bg-zinc-50/60 p-3">
                <div className="text-[10px] uppercase font-bold text-zinc-400">{key}</div>
                <div className="font-semibold text-zinc-800 truncate mt-1">
                  {typeof val === "object" ? JSON.stringify(val) : String(val)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Event Timeline */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-zinc-900">Execution Audit Timeline</h2>
        <div className="space-y-3">
          {(execution.events || []).map((ev, idx) => {
            const time = new Date(ev.created_at);
            return (
              <div
                key={ev.id || idx}
                className="flex items-start space-x-3 rounded-xl border border-zinc-100 bg-zinc-50/40 p-3 text-xs"
              >
                <div className="mt-1 h-2 w-2 rounded-full bg-zinc-900 shrink-0" />
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-zinc-900 capitalize">
                      {ev.event_type.replace("_", " ")}
                    </span>
                    <span className="text-[10px] text-zinc-400">
                      {time.toLocaleDateString()} {time.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                    </span>
                  </div>
                  {ev.payload && Object.keys(ev.payload).length > 0 && (
                    <pre className="text-[10px] text-zinc-600 bg-white p-2 rounded border border-zinc-200 overflow-x-auto font-mono">
                      {JSON.stringify(ev.payload, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Approval Modal */}
      <ApprovalModal
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        onSuccess={fetchExecution}
        execution={execution}
      />
    </div>
  );
}
