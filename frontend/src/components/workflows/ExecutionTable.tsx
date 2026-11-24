"use client";

import Link from "next/link";
import type { WorkflowExecutionDetail } from "@/types";

interface ExecutionTableProps {
  executions: WorkflowExecutionDetail[];
  loading?: boolean;
  onResumeClick: (exec: WorkflowExecutionDetail) => void;
  onRetryClick: (exec: WorkflowExecutionDetail) => void;
}

export default function ExecutionTable({
  executions,
  loading,
  onResumeClick,
  onRetryClick,
}: ExecutionTableProps) {
  if (loading) {
    return <div className="p-12 text-center text-xs text-zinc-400">Loading workflow executions…</div>;
  }

  if (executions.length === 0) {
    return (
      <div className="p-12 text-center">
        <span className="text-3xl">⚙️</span>
        <h3 className="mt-3 text-sm font-semibold text-zinc-900">No workflow executions found</h3>
        <p className="mt-1 text-xs text-zinc-500">
          Start a recruitment workflow on a job requisition to orchestrate the hiring process.
        </p>
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
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead className="border-b border-zinc-200 bg-zinc-50/75 text-[11px] font-bold uppercase tracking-wider text-zinc-500">
          <tr>
            <th className="px-5 py-3">Workflow / Thread</th>
            <th className="px-5 py-3">Job Requisition</th>
            <th className="px-5 py-3">Current Step</th>
            <th className="px-5 py-3">Status</th>
            <th className="px-5 py-3">Started</th>
            <th className="px-5 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200">
          {executions.map((item) => {
            const started = new Date(item.started_at);
            return (
              <tr key={item.id} className="hover:bg-zinc-50/50 transition-colors">
                <td className="px-5 py-4">
                  <Link
                    href={`/workflows/${item.id}`}
                    className="font-bold text-zinc-900 hover:underline block"
                  >
                    {item.workflow_type.replace("_", " ")}
                  </Link>
                  <div className="text-[10px] text-zinc-400 font-mono truncate max-w-xs">
                    {item.thread_id}
                  </div>
                </td>

                <td className="px-5 py-4">
                  <div className="font-semibold text-zinc-900">{item.job_title || "Requisition"}</div>
                  {item.candidate_name && (
                    <div className="text-[10px] text-zinc-500">Candidate: {item.candidate_name}</div>
                  )}
                </td>

                <td className="px-5 py-4">
                  <span className="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-700 font-semibold">
                    {item.current_step || "—"}
                  </span>
                  {item.retry_count > 0 && (
                    <span className="ml-1 text-[10px] text-zinc-400 font-semibold">
                      (retry #{item.retry_count})
                    </span>
                  )}
                </td>

                <td className="px-5 py-4">
                  <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase ${getStatusBadge(item.status)}`}>
                    {item.status === "interrupted" ? "Awaiting Approval" : item.status}
                  </span>
                </td>

                <td className="px-5 py-4 text-zinc-500 text-[11px]">
                  {started.toLocaleDateString(undefined, { month: "short", day: "numeric" })} at{" "}
                  {started.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </td>

                <td className="px-5 py-4 text-right space-x-2">
                  {item.status === "interrupted" && (
                    <button
                      onClick={() => onResumeClick(item)}
                      className="rounded-lg bg-amber-600 px-3 py-1 text-[11px] font-bold text-white hover:bg-amber-700 transition-colors shadow-sm"
                    >
                      ⚡ Review & Decide
                    </button>
                  )}
                  {item.status === "failed" && (
                    <button
                      onClick={() => onRetryClick(item)}
                      className="rounded-lg border border-red-300 bg-red-50 px-2.5 py-1 text-[11px] font-bold text-red-800 hover:bg-red-100 transition-colors"
                    >
                      ↻ Retry Step
                    </button>
                  )}
                  <Link
                    href={`/workflows/${item.id}`}
                    className="rounded-lg border border-zinc-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
