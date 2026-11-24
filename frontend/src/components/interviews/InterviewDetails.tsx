"use client";

import Link from "next/link";
import type { InterviewDetail, InterviewStatus } from "@/types";

interface InterviewDetailsProps {
  interview: InterviewDetail;
  onStatusUpdate: (status: InterviewStatus) => void;
  onEditClick: () => void;
}

export default function InterviewDetails({
  interview,
  onStatusUpdate,
  onEditClick,
}: InterviewDetailsProps) {
  const start = new Date(interview.scheduled_start);
  const end = new Date(interview.scheduled_end);

  const statusBadge = {
    scheduled: "bg-blue-50 text-blue-700 border-blue-200",
    completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
    cancelled: "bg-red-50 text-red-700 border-red-200",
    rescheduled: "bg-amber-50 text-amber-700 border-amber-200",
  }[interview.status] || "bg-zinc-100 text-zinc-700";

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-zinc-900">{interview.title}</h1>
            <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold uppercase ${statusBadge}`}>
              {interview.status}
            </span>
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-700 capitalize">
              {interview.interview_type}
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            Scheduled for {start.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "short", day: "numeric" })} at{" "}
            {start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} –{" "}
            {end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} ({interview.location_type})
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {interview.meeting_link && (
            <a
              href={interview.meeting_link}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg border border-zinc-200 bg-zinc-50 px-3.5 py-2 text-xs font-bold text-zinc-800 hover:bg-zinc-100 transition-colors"
            >
              Join Meeting ↗
            </a>
          )}
          <button
            onClick={onEditClick}
            className="rounded-lg border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors"
          >
            Edit Schedule
          </button>
          {interview.status === "scheduled" && (
            <button
              onClick={() => onStatusUpdate("completed")}
              className="rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition-colors"
            >
              ✓ Mark Completed
            </button>
          )}
          {interview.status === "scheduled" && (
            <button
              onClick={() => onStatusUpdate("cancelled")}
              className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Candidate & Job Context Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Candidate Card */}
        <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Candidate Information
            </span>
            <Link
              href={`/applications/${interview.application.id}`}
              className="text-xs font-semibold text-zinc-900 hover:underline"
            >
              View Application →
            </Link>
          </div>
          <div className="text-sm font-bold text-zinc-900">
            {interview.application.candidate.full_name}
          </div>
          <div className="text-xs text-zinc-600">
            {interview.application.candidate.email}
            {interview.application.candidate.phone && ` • ${interview.application.candidate.phone}`}
          </div>
          {interview.application.latest_analysis && (
            <div className="mt-2 rounded-lg border border-blue-200 bg-blue-50/60 p-2 text-xs text-blue-900 flex items-center justify-between">
              <div>
                <span className="font-bold">✨ AI Resume Screening:</span>{" "}
                {interview.application.latest_analysis.summary_headline}
              </div>
              {interview.application.latest_analysis.ats_score != null && (
                <span className="rounded-full bg-blue-600 px-2 py-0.5 text-[10px] font-bold text-white shrink-0">
                  ATS: {interview.application.latest_analysis.ats_score}/100
                </span>
              )}
            </div>
          )}
        </div>

        {/* Job Card */}
        <div className="rounded-xl border border-zinc-200 bg-zinc-50/50 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Target Requisition
            </span>
            <span className="text-xs font-semibold text-zinc-700">
              {interview.application.job.department}
            </span>
          </div>
          <div className="text-sm font-bold text-zinc-900">
            {interview.application.job.title}
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {interview.application.job.required_skills?.map((skill, idx) => (
              <span
                key={idx}
                className="rounded bg-zinc-200/70 px-2 py-0.5 text-[10px] font-semibold text-zinc-700"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Internal Notes if present */}
      {interview.notes && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/40 p-4 text-xs text-amber-900">
          <span className="font-bold">Panel Notes: </span>
          {interview.notes}
        </div>
      )}
    </div>
  );
}
