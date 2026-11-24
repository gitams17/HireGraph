"use client";

import { Application, ApplicationStage, STAGE_LABELS, STAGE_ORDER } from "@/types";
import { ApplicationCard } from "./ApplicationCard";

interface ApplicationPipelineProps {
  applications: Application[];
  onAdvance: (app: Application, nextStage: ApplicationStage) => void;
}

export function ApplicationPipeline({ applications, onAdvance }: ApplicationPipelineProps) {
  function getNextStage(current: ApplicationStage): ApplicationStage | null {
    const idx = STAGE_ORDER.indexOf(current);
    if (idx >= 0 && idx < STAGE_ORDER.length - 2) {
      // Moves along pipeline up to selected
      return STAGE_ORDER[idx + 1];
    }
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 items-start">
      {STAGE_ORDER.map((stage) => {
        const stageApps = applications.filter((app) => app.stage === stage);
        return (
          <div
            key={stage}
            className="rounded-xl border border-zinc-200 bg-zinc-50/70 p-3 flex flex-col min-h-[450px]"
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-200">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-700">
                {STAGE_LABELS[stage]}
              </span>
              <span className="rounded-full bg-white px-2 py-0.5 text-xs font-bold text-zinc-800 border border-zinc-200 shadow-2xs">
                {stageApps.length}
              </span>
            </div>

            {/* Application Cards */}
            <div className="space-y-3 flex-1 overflow-y-auto">
              {stageApps.length === 0 ? (
                <div className="py-8 text-center text-xs text-zinc-400">
                  No applications
                </div>
              ) : (
                stageApps.map((app) => {
                  const next = getNextStage(app.stage);
                  return (
                    <ApplicationCard
                      key={app.id}
                      application={app}
                      onAdvanceClick={next ? () => onAdvance(app, next) : undefined}
                    />
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
