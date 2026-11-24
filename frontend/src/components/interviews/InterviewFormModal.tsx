"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Application, InterviewDetail, InterviewType, PaginatedResponse } from "@/types";
import InterviewerSelector from "./InterviewerSelector";

interface InterviewFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialApplicationId?: string;
  interviewToEdit?: InterviewDetail | null;
}

export default function InterviewFormModal({
  isOpen,
  onClose,
  onSuccess,
  initialApplicationId,
  interviewToEdit,
}: InterviewFormModalProps) {
  const [applications, setApplications] = useState<Application[]>([]);
  const [applicationId, setApplicationId] = useState(initialApplicationId || "");
  const [title, setTitle] = useState(interviewToEdit?.title || "Technical Round 1");
  const [interviewType, setInterviewType] = useState<InterviewType>(
    interviewToEdit?.interview_type || "technical"
  );
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("10:00");
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [locationType, setLocationType] = useState(interviewToEdit?.location_type || "remote");
  const [meetingLink, setMeetingLink] = useState(interviewToEdit?.meeting_link || "");
  const [locationDetails, setLocationDetails] = useState(interviewToEdit?.location_details || "");
  const [notes, setNotes] = useState(interviewToEdit?.notes || "");
  const [selectedInterviewerIds, setSelectedInterviewerIds] = useState<string[]>(
    interviewToEdit?.participants.map((p) => p.user.id) || []
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    if (interviewToEdit) {
      setTitle(interviewToEdit.title);
      setInterviewType(interviewToEdit.interview_type);
      setLocationType(interviewToEdit.location_type);
      setMeetingLink(interviewToEdit.meeting_link || "");
      setLocationDetails(interviewToEdit.location_details || "");
      setNotes(interviewToEdit.notes || "");
      setSelectedInterviewerIds(interviewToEdit.participants.map((p) => p.user.id));
      if (interviewToEdit.scheduled_start) {
        const d = new Date(interviewToEdit.scheduled_start);
        setDate(d.toISOString().split("T")[0]);
        setStartTime(d.toTimeString().substring(0, 5));
      }
    } else {
      // Default tomorrow at 10:00
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setDate(tomorrow.toISOString().split("T")[0]);
      setStartTime("10:00");
      setTitle("Technical Round 1");
      setInterviewType("technical");
      setLocationType("remote");
      setMeetingLink("");
      setLocationDetails("");
      setNotes("");
      setSelectedInterviewerIds([]);
    }

    // Load active applications
    api
      .get<PaginatedResponse<Application>>("/api/v1/applications/?page_size=100")
      .then((res) => {
        setApplications(res.results);
        if (!applicationId && res.results.length > 0) {
          setApplicationId(res.results[0].id);
        }
      })
      .catch(() => setApplications([]));
  }, [isOpen, interviewToEdit]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const [year, month, day] = date.split("-").map(Number);
      const [hours, minutes] = startTime.split(":").map(Number);
      const start = new Date(year, month - 1, day, hours, minutes);
      const end = new Date(start.getTime() + durationMinutes * 60000);

      const payload = {
        application_id: applicationId,
        title,
        interview_type: interviewType,
        scheduled_start: start.toISOString(),
        scheduled_end: end.toISOString(),
        location_type: locationType,
        meeting_link: meetingLink,
        location_details: locationDetails,
        interviewer_ids: selectedInterviewerIds,
        notes,
      };

      if (interviewToEdit) {
        await api.patch(`/api/v1/interviews/${interviewToEdit.id}/`, payload);
      } else {
        await api.post("/api/v1/interviews/", payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err?.data?.detail || err?.data?.scheduled_end || "Failed to schedule interview.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl my-8">
        <div className="flex items-center justify-between border-b border-zinc-200 pb-4">
          <div>
            <h2 className="text-lg font-bold text-zinc-900">
              {interviewToEdit ? "Edit Interview Session" : "Schedule Interview"}
            </h2>
            <p className="text-xs text-zinc-500">
              Assign interviewers, configure schedule, and prepare candidate evaluation.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-colors"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-red-50 p-3 text-xs font-medium text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {!interviewToEdit && (
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Candidate Application *
              </label>
              <select
                required
                value={applicationId}
                onChange={(e) => setApplicationId(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              >
                <option value="">Select Candidate Application…</option>
                {applications.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.candidate?.full_name || "Candidate"} — {app.job?.title || "Position"} ({app.stage})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1">
              Interview Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Technical Round 1: Architecture Deep Dive"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Interview Type *
              </label>
              <select
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value as InterviewType)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              >
                <option value="technical">Technical</option>
                <option value="hr">HR</option>
                <option value="managerial">Managerial</option>
                <option value="screening">Screening</option>
                <option value="culture_fit">Culture Fit</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Location Type
              </label>
              <select
                value={locationType}
                onChange={(e) => setLocationType(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              >
                <option value="remote">Remote (Video Call)</option>
                <option value="in_person">In-Person (Office)</option>
                <option value="phone">Phone Screen</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Date *
              </label>
              <input
                type="date"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Start Time *
              </label>
              <input
                type="time"
                required
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Duration
              </label>
              <select
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              >
                <option value={30}>30 mins</option>
                <option value={45}>45 mins</option>
                <option value={60}>60 mins (1 hr)</option>
                <option value={90}>90 mins</option>
                <option value={120}>120 mins (2 hrs)</option>
              </select>
            </div>
          </div>

          {locationType === "remote" ? (
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Meeting Link (Google Meet / Zoom / Teams)
              </label>
              <input
                type="url"
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
                placeholder="https://meet.google.com/xyz-abc-def"
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Location Details (Room / Address / Phone)
              </label>
              <input
                type="text"
                value={locationDetails}
                onChange={(e) => setLocationDetails(e.target.value)}
                placeholder="e.g. Conference Room 4B or +1-555-0199"
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
              />
            </div>
          )}

          {/* Assigned Panel */}
          <InterviewerSelector
            selectedIds={selectedInterviewerIds}
            onChange={setSelectedInterviewerIds}
          />

          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1">
              Internal Panel Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Instructions or focus areas for the interview panel…"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-3 border-t border-zinc-200">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-lg border border-zinc-300 px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 disabled:opacity-50"
            >
              {loading ? "Scheduling…" : interviewToEdit ? "Update Interview" : "Schedule Interview"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
