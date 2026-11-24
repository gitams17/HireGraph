"use client";

import { JobStatus, EmploymentType, JOB_STATUS_LABELS, EMPLOYMENT_TYPE_LABELS } from "@/types";

interface JobFiltersProps {
  search: string;
  status: string;
  department: string;
  location: string;
  employment_type: string;
  onChange: (key: string, value: string) => void;
}

export function JobFilters({
  search,
  status,
  department,
  location,
  employment_type,
  onChange,
}: JobFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
      {/* Search */}
      <input
        type="text"
        placeholder="Search jobs…"
        value={search}
        onChange={(e) => onChange("search", e.target.value)}
        className="flex-1 min-w-48 rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400"
      />

      {/* Status */}
      <select
        value={status}
        onChange={(e) => onChange("status", e.target.value)}
        className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-zinc-400"
      >
        <option value="">All statuses</option>
        {(Object.entries(JOB_STATUS_LABELS) as [JobStatus, string][]).map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>

      {/* Employment type */}
      <select
        value={employment_type}
        onChange={(e) => onChange("employment_type", e.target.value)}
        className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-zinc-400"
      >
        <option value="">All types</option>
        {(Object.entries(EMPLOYMENT_TYPE_LABELS) as [EmploymentType, string][]).map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>

      {/* Department */}
      <input
        type="text"
        placeholder="Department"
        value={department}
        onChange={(e) => onChange("department", e.target.value)}
        className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400"
      />

      {/* Location */}
      <input
        type="text"
        placeholder="Location"
        value={location}
        onChange={(e) => onChange("location", e.target.value)}
        className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400"
      />
    </div>
  );
}
