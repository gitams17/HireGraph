import Link from "next/link";
import { JobRequisition, EMPLOYMENT_TYPE_LABELS } from "@/types";
import { JobStatusBadge } from "./JobStatusBadge";

interface JobCardProps {
  job: JobRequisition;
}

export function JobCard({ job }: JobCardProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <Link
            href={`/jobs/${job.id}`}
            className="text-base font-semibold text-zinc-900 hover:text-blue-600 transition-colors line-clamp-1"
          >
            {job.title}
          </Link>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-500">
            {job.department && <span>{job.department}</span>}
            {job.location && <span>{job.location}</span>}
            <span>{EMPLOYMENT_TYPE_LABELS[job.employment_type]}</span>
          </div>
        </div>
        <JobStatusBadge status={job.status} />
      </div>

      {job.required_skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.required_skills.slice(0, 5).map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs text-zinc-600"
            >
              {skill}
            </span>
          ))}
          {job.required_skills.length > 5 && (
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs text-zinc-500">
              +{job.required_skills.length - 5} more
            </span>
          )}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-xs text-zinc-400">
        <span>Posted {new Date(job.created_at).toLocaleDateString()}</span>
        <Link
          href={`/jobs/${job.id}/edit`}
          className="text-zinc-500 hover:text-zinc-800 font-medium transition-colors"
        >
          Edit →
        </Link>
      </div>
    </div>
  );
}
