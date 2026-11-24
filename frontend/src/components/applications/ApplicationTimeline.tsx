import { ApplicationEvent, STAGE_LABELS } from "@/types";

interface ApplicationTimelineProps {
  events: ApplicationEvent[];
}

export function ApplicationTimeline({ events }: ApplicationTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6 text-center text-xs text-zinc-400 shadow-sm">
        No activity history recorded yet.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-zinc-900 mb-6">Activity Timeline</h3>

      <div className="relative border-l border-zinc-200 pl-6 ml-3 space-y-6">
        {events.map((event) => {
          const isStageChange = event.event_type === "stage_changed";
          return (
            <div key={event.id} className="relative group">
              {/* Bullet node */}
              <div
                className={`absolute -left-[31px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full ring-4 ring-white ${
                  isStageChange ? "bg-zinc-900" : "bg-zinc-400"
                }`}
              />

              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                <span className="text-sm font-semibold text-zinc-800">
                  {isStageChange ? (
                    <>
                      Moved from{" "}
                      <span className="text-zinc-500">
                        {STAGE_LABELS[event.from_stage as keyof typeof STAGE_LABELS] || event.from_stage || "None"}
                      </span>{" "}
                      →{" "}
                      <span className="text-zinc-900 font-bold">
                        {STAGE_LABELS[event.to_stage as keyof typeof STAGE_LABELS] || event.to_stage}
                      </span>
                    </>
                  ) : event.event_type === "created" ? (
                    "Application Created"
                  ) : (
                    "Application Updated"
                  )}
                </span>
                <span className="text-xs text-zinc-400">
                  {new Date(event.created_at).toLocaleString()}
                </span>
              </div>

              {event.actor_name && (
                <span className="text-xs text-zinc-500 block mt-0.5">
                  by {event.actor_name}
                </span>
              )}

              {event.notes && (
                <div className="mt-2 rounded-lg bg-zinc-50 p-3 text-xs text-zinc-600 border border-zinc-100 whitespace-pre-wrap">
                  {event.notes}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
