"use client";

import type { WorkflowExecutionDetail } from "@/types";

interface WorkflowGraphViewerProps {
  execution: WorkflowExecutionDetail;
}

export default function WorkflowGraphViewer({ execution }: WorkflowGraphViewerProps) {
  const steps = [
    { key: "load_requirements", label: "Requirements", phase: "jd" },
    { key: "generate_jd", label: "JD Generation", phase: "jd" },
    { key: "approval_interrupt", label: "JD Approval (Gate)", phase: "jd", isGate: true },
    { key: "publish_job", label: "Job Publication", phase: "intake" },
    { key: "monitor_applicants", label: "Applicant Monitoring", phase: "intake" },
    { key: "screen_candidates", label: "Resume Screening", phase: "eval" },
    { key: "evaluate_interview_decision", label: "Interview Decision", phase: "eval" },
    { key: "prepare_offer", label: "Offer Prep", phase: "offer" },
    { key: "offer_approval_interrupt", label: "Offer Approval (Gate)", phase: "offer", isGate: true },
    { key: "send_offer", label: "Send & Negotiation", phase: "offer" },
    { key: "initiate_onboarding", label: "Onboarding Checklist", phase: "onboarding" },
  ];

  const currentStep = execution.current_step;
  const isCompleted = execution.status === "completed";
  const isFailed = execution.status === "failed";
  const isInterrupted = execution.status === "interrupted";

  const currentIndex = steps.findIndex((s) => s.key === currentStep);

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
        <div>
          <h2 className="text-base font-bold text-zinc-900">LangGraph Execution Flow</h2>
          <p className="text-xs text-zinc-500">
            Real-time durable workflow checkpoints and branching pipeline.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {isInterrupted && (
            <span className="rounded-full bg-amber-100 border border-amber-300 px-2.5 py-0.5 text-xs font-bold text-amber-900 animate-pulse">
              ⚡ Paused at Human Approval Gate
            </span>
          )}
          {isCompleted && (
            <span className="rounded-full bg-emerald-100 border border-emerald-300 px-2.5 py-0.5 text-xs font-bold text-emerald-900">
              ✓ Pipeline Completed
            </span>
          )}
          {isFailed && (
            <span className="rounded-full bg-red-100 border border-red-300 px-2.5 py-0.5 text-xs font-bold text-red-900">
              ✕ Failed at Step
            </span>
          )}
        </div>
      </div>

      <div className="overflow-x-auto py-4">
        <div className="flex items-center space-x-2 min-w-max">
          {steps.map((step, idx) => {
            const isCurrent = step.key === currentStep;
            const isPast = isCompleted || (currentIndex > -1 && idx < currentIndex);

            let style = "bg-zinc-100 border-zinc-200 text-zinc-500";
            if (isPast) {
              style = "bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold";
            } else if (isCurrent) {
              if (isFailed) {
                style = "bg-red-500 border-red-600 text-white font-bold shadow-md";
              } else if (isInterrupted) {
                style = "bg-amber-500 border-amber-600 text-white font-bold shadow-md animate-pulse";
              } else {
                style = "bg-zinc-900 border-zinc-900 text-white font-bold shadow-md";
              }
            }

            return (
              <div key={step.key} className="flex items-center">
                <div
                  className={`flex flex-col items-center justify-center rounded-xl border px-3 py-2 text-center text-xs transition-all ${style}`}
                >
                  <div className="text-[10px] uppercase font-bold tracking-wider opacity-80">
                    {step.isGate ? "Human Gate" : `Step ${idx + 1}`}
                  </div>
                  <div className="text-xs font-semibold whitespace-nowrap mt-0.5">
                    {step.label}
                  </div>
                </div>
                {idx < steps.length - 1 && (
                  <div
                    className={`h-0.5 w-4 mx-1 ${
                      isPast ? "bg-emerald-400" : "bg-zinc-200"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
