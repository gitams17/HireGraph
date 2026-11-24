import {
  JobRequisition,
  EMPLOYMENT_TYPE_LABELS,
  JOB_STATUS_LABELS,
} from "@/types";
import { JobStatusBadge } from "./JobStatusBadge";

interface JobDetailsProps {
  job: JobRequisition;
}

export function JobDetails({ job }: JobDetailsProps) {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold text-zinc-900">{job.title}</h1>
          <JobStatusBadge status={job.status} />
        </div>
        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-zinc-500">
          {job.department && (
            <span>
              <span className="font-medium text-zinc-700">Department: </span>
              {job.department}
            </span>
          )}
          {job.location && (
            <span>
              <span className="font-medium text-zinc-700">Location: </span>
              {job.location}
            </span>
          )}
          <span>
            <span className="font-medium text-zinc-700">Type: </span>
            {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
          </span>
        </div>
      </div>

      {/* Experience */}
      {(job.experience_min !== null || job.experience_max !== null) && (
        <Section title="Experience">
          <p className="text-sm text-zinc-700">
            {job.experience_min !== null && job.experience_max !== null
              ? `${job.experience_min}–${job.experience_max} years`
              : job.experience_min !== null
              ? `${job.experience_min}+ years`
              : `Up to ${job.experience_max} years`}
          </p>
        </Section>
      )}

      {/* Required skills */}
      {job.required_skills.length > 0 && (
        <Section title="Required skills">
          <div className="flex flex-wrap gap-2">
            {job.required_skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full bg-zinc-100 px-3 py-1 text-sm text-zinc-700"
              >
                {skill}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* Responsibilities */}
      {job.responsibilities.length > 0 && (
        <Section title="Responsibilities">
          <ul className="ml-4 list-disc space-y-1 text-sm text-zinc-700">
            {job.responsibilities.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Meta */}
      <Section title="Details">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <dt className="text-zinc-500">Created by</dt>
          <dd className="text-zinc-900">{job.created_by.full_name || job.created_by.email}</dd>
          <dt className="text-zinc-500">Created</dt>
          <dd className="text-zinc-900">{new Date(job.created_at).toLocaleString()}</dd>
          <dt className="text-zinc-500">Last updated</dt>
          <dd className="text-zinc-900">{new Date(job.updated_at).toLocaleString()}</dd>
        </dl>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        {title}
      </h2>
      {children}
    </div>
  );
}
