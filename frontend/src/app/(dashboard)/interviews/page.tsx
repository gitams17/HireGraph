"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { InterviewListItem, PaginatedResponse } from "@/types";
import InterviewFormModal from "@/components/interviews/InterviewFormModal";

export default function InterviewsPage() {
  const [interviews, setInterviews] = useState<InterviewListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [myInterviews, setMyInterviews] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchInterviews = useCallback(
    async (q: string, st: string, mine: boolean, p: number) => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (q) params.set("search", q);
        if (st) params.set("status", st);
        if (mine) params.set("my_interviews", "true");
        params.set("page", String(p));

        const res = await api.get<PaginatedResponse<InterviewListItem>>(
          `/api/v1/interviews/?${params.toString()}`
        );
        setInterviews(res.results);
        setTotalCount(res.count);
      } catch {
        setError("Failed to load interviews.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(
      () => fetchInterviews(search, statusFilter, myInterviews, page),
      300
    );
    return () => clearTimeout(debounceRef.current);
  }, [search, statusFilter, myInterviews, page, fetchInterviews]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">Interviews</h1>
          <p className="text-xs text-zinc-500 mt-1">
            Schedule sessions, assign interview panels, generate AI questions, and collect evaluations.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/interviews/calendar"
            className="rounded-lg border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors"
          >
            📅 Calendar View
          </Link>
          <button
            onClick={() => setShowScheduleModal(true)}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors shadow-sm"
          >
            + Schedule Interview
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white p-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          {[
            { label: "All", value: "" },
            { label: "Scheduled", value: "scheduled" },
            { label: "Completed", value: "completed" },
            { label: "Cancelled", value: "cancelled" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => {
                setStatusFilter(tab.value);
                setPage(1);
              }}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                statusFilter === tab.value
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
              }`}
            >
              {tab.label}
            </button>
          ))}

          <button
            onClick={() => {
              setMyInterviews(!myInterviews);
              setPage(1);
            }}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors border ${
              myInterviews
                ? "bg-purple-100 border-purple-300 text-purple-900"
                : "bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-50"
            }`}
          >
            {myInterviews ? "✓ My Interviews" : "Show My Interviews"}
          </button>
        </div>

        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search candidate, job, or title…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs focus:border-zinc-900 focus:bg-white focus:outline-none"
          />
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-xs font-medium text-red-700">
          {error}
        </div>
      )}

      {/* Interviews Table / Cards */}
      <div className="rounded-2xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-zinc-400">Loading interview sessions…</div>
        ) : interviews.length === 0 ? (
          <div className="p-12 text-center">
            <span className="text-3xl">👥</span>
            <h3 className="mt-3 text-sm font-semibold text-zinc-900">No interviews found</h3>
            <p className="mt-1 text-xs text-zinc-500">
              Schedule an interview to start evaluating candidates.
            </p>
            <button
              onClick={() => setShowScheduleModal(true)}
              className="mt-4 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800"
            >
              + Schedule Interview
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-200 bg-zinc-50/75 text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                <tr>
                  <th className="px-5 py-3">Interview Session</th>
                  <th className="px-5 py-3">Candidate</th>
                  <th className="px-5 py-3">Date & Time</th>
                  <th className="px-5 py-3">Panel</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200">
                {interviews.map((item) => {
                  const start = new Date(item.scheduled_start);
                  const end = new Date(item.scheduled_end);

                  const statusBadge = {
                    scheduled: "bg-blue-50 text-blue-700 border-blue-200",
                    completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
                    cancelled: "bg-red-50 text-red-700 border-red-200",
                    rescheduled: "bg-amber-50 text-amber-700 border-amber-200",
                  }[item.status] || "bg-zinc-100 text-zinc-700";

                  return (
                    <tr key={item.id} className="hover:bg-zinc-50/50 transition-colors">
                      <td className="px-5 py-4">
                        <Link
                          href={`/interviews/${item.id}`}
                          className="font-bold text-zinc-900 hover:underline block"
                        >
                          {item.title}
                        </Link>
                        <div className="text-[11px] text-zinc-500 capitalize">
                          {item.interview_type} • {item.location_type}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-semibold text-zinc-900">{item.candidate_name}</div>
                        <div className="text-[11px] text-zinc-500">{item.job_title}</div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-medium text-zinc-900">
                          {start.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                        </div>
                        <div className="text-[11px] text-zinc-500">
                          {start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} –{" "}
                          {end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {item.participants.length > 0 ? (
                            item.participants.map((p) => (
                              <span
                                key={p.id}
                                className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-700"
                              >
                                {p.user.full_name || p.user.email}
                              </span>
                            ))
                          ) : (
                            <span className="text-zinc-400 italic">None</span>
                          )}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase ${statusBadge}`}>
                          {item.status}
                        </span>
                        {item.feedbacks_count > 0 && (
                          <div className="text-[10px] text-zinc-500 mt-1">
                            {item.feedbacks_count} feedback submitted
                          </div>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/interviews/${item.id}`}
                          className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors"
                        >
                          Cockpit →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Schedule Modal */}
      <InterviewFormModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        onSuccess={() => fetchInterviews(search, statusFilter, myInterviews, page)}
      />
    </div>
  );
}
