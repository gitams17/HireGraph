import { JobStatus, JOB_STATUS_LABELS } from "@/types";

interface JobStatusBadgeProps {
  status: JobStatus;
}

const STATUS_STYLES: Record<JobStatus, string> = {
  draft: "bg-zinc-100 text-zinc-700 ring-zinc-300",
  open: "bg-green-50 text-green-700 ring-green-300",
  paused: "bg-yellow-50 text-yellow-700 ring-yellow-300",
  closed: "bg-red-50 text-red-600 ring-red-300",
};

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {JOB_STATUS_LABELS[status]}
    </span>
  );
}
