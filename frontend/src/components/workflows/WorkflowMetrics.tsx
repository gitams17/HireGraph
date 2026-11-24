"use client";

import type { WorkflowDashboardMetrics } from "@/types";

interface WorkflowMetricsProps {
  metrics: WorkflowDashboardMetrics | null;
  loading?: boolean;
}

export default function WorkflowMetrics({ metrics, loading }: WorkflowMetricsProps) {
  if (loading || !metrics) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-20 rounded-xl border border-zinc-200 bg-white p-4 animate-pulse" />
        ))}
      </div>
    );
  }

  const cards = [
    { label: "Total Workflows", value: metrics.total_executions, color: "text-zinc-900", border: "border-zinc-200" },
    { label: "Active Running", value: metrics.active_count, color: "text-blue-600", border: "border-blue-200 bg-blue-50/30" },
    {
      label: "Awaiting Approval",
      value: metrics.pending_approvals_count,
      color: "text-amber-600",
      border: "border-amber-200 bg-amber-50/40",
      alert: metrics.pending_approvals_count > 0,
    },
    { label: "Failed / Retriable", value: metrics.failed_count, color: "text-red-600", border: "border-red-200 bg-red-50/30" },
    { label: "Completed", value: metrics.completed_count, color: "text-emerald-600", border: "border-emerald-200 bg-emerald-50/30" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.label} className={`rounded-xl border ${c.border} p-4 shadow-sm`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-500">{c.label}</span>
            {c.alert && (
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping" />
            )}
          </div>
          <div className={`mt-2 text-2xl font-bold ${c.color}`}>{c.value}</div>
        </div>
      ))}
    </div>
  );
}
