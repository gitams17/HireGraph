"use client";

import { WorkflowEvent } from "@/types";

interface WorkflowTimelineProps {
  events: WorkflowEvent[];
}

const EVENT_LABELS: Record<string, { label: string; color: string }> = {
  generation_started: { label: "Generation Triggered", color: "bg-blue-500" },
  jd_generated: { label: "AI Generated Structured JD", color: "bg-indigo-500" },
  approval_interrupted: { label: "Human Approval Requested", color: "bg-amber-500" },
  resumed: { label: "Workflow Resumed", color: "bg-purple-500" },
  approved_and_completed: { label: "Approved & Ready for Publication", color: "bg-green-500" },
  revision_generated: { label: "Revision Generated", color: "bg-orange-500" },
  failed: { label: "Workflow Failed", color: "bg-red-500" },
};

export function WorkflowTimeline({ events }: WorkflowTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-zinc-400">
        No workflow history recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
        Workflow History & Auditing
      </h4>
      <div className="relative border-l border-zinc-200 ml-3 space-y-4">
        {events.map((ev) => {
          const cfg = EVENT_LABELS[ev.event_type] || {
            label: ev.event_type,
            color: "bg-zinc-400",
          };
          return (
            <div key={ev.id} className="relative pl-6">
              <span
                className={`absolute -left-1.5 top-1.5 h-3 w-3 rounded-full ${cfg.color} ring-4 ring-white`}
              />
              <div className="flex items-baseline justify-between gap-4">
                <span className="text-sm font-medium text-zinc-900">{cfg.label}</span>
                <span className="text-xs text-zinc-400">
                  {new Date(ev.created_at).toLocaleTimeString()}
                </span>
              </div>
              {ev.payload && Object.keys(ev.payload).length > 0 && (
                <div className="mt-1 text-xs text-zinc-500">
                  {ev.payload.feedback && (
                    <p className="italic">"{ev.payload.feedback}"</p>
                  )}
                  {ev.payload.error && (
                    <p className="text-red-600 font-medium">{ev.payload.error}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
