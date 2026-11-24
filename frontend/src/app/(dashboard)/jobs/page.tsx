"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { JobRequisition, PaginatedResponse } from "@/types";
import { JobTable } from "@/components/jobs/JobTable";
import { JobFilters } from "@/components/jobs/JobFilters";

type Filters = {
  search: string;
  status: string;
  department: string;
  location: string;
  employment_type: string;
};

const DEFAULT_FILTERS: Filters = {
  search: "",
  status: "",
  department: "",
  location: "",
  employment_type: "",
};

export default function JobsPage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [data, setData] = useState<PaginatedResponse<JobRequisition> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchJobs = useCallback(async (f: Filters, p: number) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (f.search) params.set("search", f.search);
      if (f.status) params.set("status", f.status);
      if (f.department) params.set("department", f.department);
      if (f.location) params.set("location", f.location);
      if (f.employment_type) params.set("employment_type", f.employment_type);
      params.set("page", String(p));
      const qs = params.toString();
      const result = await api.get<PaginatedResponse<JobRequisition>>(
        `/api/v1/jobs/${qs ? `?${qs}` : ""}`
      );
      setData(result);
    } catch {
      setError("Failed to load jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounce filter changes (300ms) but fetch immediately on page change.
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchJobs(filters, page), 300);
    return () => clearTimeout(debounceRef.current);
  }, [filters, page, fetchJobs]);

  function handleFilterChange(key: string, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  }

  const totalPages = data ? Math.ceil(data.count / 10) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Jobs</h1>
          {data && (
            <p className="mt-1 text-sm text-zinc-500">
              {data.count} {data.count === 1 ? "requisition" : "requisitions"}
            </p>
          )}
        </div>
        <Link
          href="/jobs/new"
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 transition-colors"
        >
          + New job
        </Link>
      </div>

      {/* Filters */}
      <JobFilters {...filters} onChange={handleFilterChange} />

      {/* Content */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-sm text-zinc-400">Loading…</div>
      ) : (
        <JobTable jobs={data?.results ?? []} />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-40 transition-colors"
          >
            ← Previous
          </button>
          <span className="text-sm text-zinc-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-40 transition-colors"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
