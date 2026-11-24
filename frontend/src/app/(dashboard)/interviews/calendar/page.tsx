"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { InterviewListItem } from "@/types";
import InterviewCalendar from "@/components/interviews/InterviewCalendar";
import InterviewFormModal from "@/components/interviews/InterviewFormModal";

export default function InterviewsCalendarPage() {
  const [interviews, setInterviews] = useState<InterviewListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [myInterviews, setMyInterviews] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  const loadCalendar = async (mine: boolean) => {
    setLoading(true);
    try {
      const url = mine
        ? "/api/v1/interviews/calendar/?my_interviews=true"
        : "/api/v1/interviews/calendar/";
      const data = await api.get<InterviewListItem[]>(url);
      setInterviews(data);
    } catch {
      setInterviews([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCalendar(myInterviews);
  }, [myInterviews]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Link
              href="/interviews"
              className="text-xs font-semibold text-zinc-500 hover:text-zinc-900"
            >
              ← Back to List
            </Link>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 mt-1">
            Interview Schedule & Calendar
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Chronological calendar timeline of scheduled candidate evaluation sessions.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setMyInterviews(!myInterviews)}
            className={`rounded-lg px-3.5 py-2 text-xs font-semibold border transition-colors ${
              myInterviews
                ? "bg-purple-100 border-purple-300 text-purple-900"
                : "bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-50"
            }`}
          >
            {myInterviews ? "✓ My Assigned Sessions" : "My Assigned Sessions"}
          </button>
          <button
            onClick={() => setShowScheduleModal(true)}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors shadow-sm"
          >
            + Schedule Interview
          </button>
        </div>
      </div>

      {/* Calendar Component */}
      <InterviewCalendar interviews={interviews} loading={loading} />

      {/* Schedule Modal */}
      <InterviewFormModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        onSuccess={() => loadCalendar(myInterviews)}
      />
    </div>
  );
}
