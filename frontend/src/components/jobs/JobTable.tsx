"use client";

import Link from "next/link";
import { JobRequisition, EMPLOYMENT_TYPE_LABELS } from "@/types";
import { JobStatusBadge } from "./JobStatusBadge";

interface JobTableProps {
  jobs: JobRequisition[];
}

export function JobTable({ jobs }: JobTableProps) {
  if (jobs.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white py-16 text-center text-sm text-zinc-500">
        No jobs found. Create your first job requisition.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
      <table className="min-w-full divide-y divide-zinc-200">
        <thead className="bg-zinc-50">
          <tr>
            {["Title", "Department", "Location", "Type", "Status", "Created", ""].map(
              (header) => (
                <th
                  key={header}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                >
                  {header}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {jobs.map((job) => (
            <tr key={job.id} className="hover:bg-zinc-50 transition-colors">
              <td className="px-4 py-3">
                <Link
                  href={`/jobs/${job.id}`}
                  className="text-sm font-medium text-zinc-900 hover:text-blue-600 transition-colors"
                >
                  {job.title}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm text-zinc-600">{job.department || "—"}</td>
              <td className="px-4 py-3 text-sm text-zinc-600">{job.location || "—"}</td>
              <td className="px-4 py-3 text-sm text-zinc-600">
                {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
              </td>
              <td className="px-4 py-3">
                <JobStatusBadge status={job.status} />
              </td>
              <td className="px-4 py-3 text-sm text-zinc-500">
                {new Date(job.created_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={`/jobs/${job.id}/edit`}
                  className="text-xs font-medium text-zinc-500 hover:text-zinc-800 transition-colors"
                >
                  Edit
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
