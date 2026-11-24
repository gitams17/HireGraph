"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { OnboardingChecklistTask } from "@/types";

export default function OnboardingList() {
  const [tasks, setTasks] = useState<OnboardingChecklistTask[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await api.get<any>("/api/v1/workflows/onboarding/");
      const list = Array.isArray(data) ? data : data.results || [];
      setTasks(list);
    } catch {
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleStatusToggle = async (task: OnboardingChecklistTask, newStatus: string) => {
    try {
      await api.patch(`/api/v1/workflows/onboarding/${task.id}/status/`, { status: newStatus });
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: newStatus as any } : t))
      );
    } catch {
      alert("Failed to update task status.");
    }
  };

  if (loading) {
    return <div className="text-center p-6 text-xs text-zinc-400">Loading onboarding checklist…</div>;
  }

  if (tasks.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-200 p-8 text-center text-xs text-zinc-500">
        No active onboarding tasks. Once candidate offers are accepted, onboarding checklists will populate here.
      </div>
    );
  }

  const categoryBadge = {
    compliance: "bg-purple-50 text-purple-700 border-purple-200",
    it_setup: "bg-blue-50 text-blue-700 border-blue-200",
    hr_paperwork: "bg-amber-50 text-amber-700 border-amber-200",
    team_intro: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };

  return (
    <div className="space-y-3">
      {tasks.map((task) => {
        const isDone = task.status === "completed";
        return (
          <div
            key={task.id}
            className={`flex flex-col sm:flex-row sm:items-center justify-between rounded-xl border p-4 text-xs transition-colors gap-3 ${
              isDone ? "border-emerald-200 bg-emerald-50/20" : "border-zinc-200 bg-white"
            }`}
          >
            <div className="flex items-start space-x-3">
              <button
                onClick={() =>
                  handleStatusToggle(task, isDone ? "pending" : "completed")
                }
                className={`mt-0.5 h-4 w-4 rounded border flex items-center justify-center font-bold text-[10px] transition-colors shrink-0 ${
                  isDone
                    ? "bg-emerald-600 border-emerald-600 text-white"
                    : "border-zinc-300 bg-white hover:border-zinc-500"
                }`}
              >
                {isDone && "✓"}
              </button>
              <div>
                <div className={`font-semibold ${isDone ? "line-through text-zinc-400" : "text-zinc-900"}`}>
                  {task.title}
                </div>
                <div className="flex items-center space-x-2 mt-1 text-[11px] text-zinc-500">
                  <span
                    className={`rounded border px-1.5 py-0.2 text-[9px] font-bold uppercase ${
                      categoryBadge[task.category] || "bg-zinc-100 text-zinc-700"
                    }`}
                  >
                    {task.category.replace("_", " ")}
                  </span>
                  {task.candidate_name && (
                    <span>Candidate: <strong className="text-zinc-700">{task.candidate_name}</strong></span>
                  )}
                  {task.due_date && <span>Due: {task.due_date}</span>}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              <select
                value={task.status}
                onChange={(e) => handleStatusToggle(task, e.target.value)}
                className="rounded-lg border border-zinc-200 bg-zinc-50 px-2 py-1 text-[11px] font-semibold text-zinc-700 focus:outline-none"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="skipped">Skipped</option>
              </select>
            </div>
          </div>
        );
      })}
    </div>
  );
}
