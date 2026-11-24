"use client";

import Link from "next/link";
import type { InterviewListItem } from "@/types";

interface InterviewCalendarProps {
  interviews: InterviewListItem[];
  loading?: boolean;
}

export default function InterviewCalendar({ interviews, loading }: InterviewCalendarProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center text-xs text-zinc-400">
        Loading interview calendar…
      </div>
    );
  }

  if (interviews.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center">
        <span className="text-3xl">📅</span>
        <h3 className="mt-3 text-sm font-semibold text-zinc-900">No interviews scheduled</h3>
        <p className="mt-1 text-xs text-zinc-500">
          Interviews will appear here once scheduled with candidates and interviewers.
        </p>
      </div>
    );
  }

  // Group by date string (e.g. "2026-11-26")
  const groupedByDate: Record<string, InterviewListItem[]> = {};
  interviews.forEach((item) => {
    const dateKey = new Date(item.scheduled_start).toLocaleDateString(undefined, {
      weekday: "long",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
    if (!groupedByDate[dateKey]) groupedByDate[dateKey] = [];
    groupedByDate[dateKey].push(item);
  });

  return (
    <div className="space-y-6">
      {Object.entries(groupedByDate).map(([dateLabel, items]) => (
        <div key={dateLabel} className="space-y-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              {dateLabel}
            </span>
            <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] font-semibold text-zinc-700">
              {items.length} {items.length === 1 ? "session" : "sessions"}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {items.map((interview) => {
              const start = new Date(interview.scheduled_start);
              const end = new Date(interview.scheduled_end);
              const timeString = `${start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} – ${end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;

              const statusColor =
                interview.status === "completed"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : interview.status === "cancelled"
                  ? "bg-red-50 text-red-700 border-red-200"
                  : "bg-blue-50 text-blue-700 border-blue-200";

              return (
                <div
                  key={interview.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between rounded-xl border border-zinc-200 bg-white p-4 shadow-sm hover:border-zinc-300 transition-all gap-4"
                >
                  <div className="flex items-start space-x-4">
                    <div className="rounded-lg bg-zinc-100 p-2 text-center shrink-0 w-24">
                      <div className="text-[11px] font-bold text-zinc-900">{timeString}</div>
                      <div className="text-[10px] text-zinc-500 capitalize">{interview.location_type}</div>
                    </div>

                    <div>
                      <div className="flex items-center space-x-2">
                        <Link
                          href={`/interviews/${interview.id}`}
                          className="text-sm font-bold text-zinc-900 hover:underline"
                        >
                          {interview.title}
                        </Link>
                        <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${statusColor}`}>
                          {interview.status}
                        </span>
                        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-semibold text-zinc-600 capitalize">
                          {interview.interview_type}
                        </span>
                      </div>

                      <div className="mt-1 text-xs text-zinc-600">
                        Candidate: <span className="font-semibold text-zinc-900">{interview.candidate_name}</span> for{" "}
                        <span className="font-semibold text-zinc-900">{interview.job_title}</span>
                      </div>

                      <div className="mt-2 flex items-center space-x-2 text-[11px] text-zinc-500">
                        <span>Panel:</span>
                        {interview.participants.length > 0 ? (
                          interview.participants.map((p) => (
                            <span
                              key={p.id}
                              className="rounded bg-zinc-100 px-1.5 py-0.5 text-zinc-700 font-medium"
                            >
                              {p.user.full_name || p.user.email}
                            </span>
                          ))
                        ) : (
                          <span className="italic text-zinc-400">No panel assigned</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    {interview.meeting_link && (
                      <a
                        href={interview.meeting_link}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-100 transition-colors"
                      >
                        Join Call ↗
                      </a>
                    )}
                    <Link
                      href={`/interviews/${interview.id}`}
                      className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors"
                    >
                      Open Cockpit →
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
