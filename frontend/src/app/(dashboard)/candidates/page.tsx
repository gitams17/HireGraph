"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { api, extractApiErrors } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Candidate, Organization, PaginatedResponse } from "@/types";
import { CandidateTable } from "@/components/candidates/CandidateTable";

export default function CandidatesPage() {
  const { user } = useAuth();
  const [candidatesData, setCandidatesData] = useState<PaginatedResponse<Candidate> | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal for new candidate
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [form, setForm] = useState({
    organization: "",
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    location: "",
    current_company: "",
    current_title: "",
    total_experience_years: "",
    skills_input: "",
    notes: "",
  });

  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchCandidates = useCallback(async (q: string, p: number) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("search", q);
      params.set("page", String(p));
      const res = await api.get<PaginatedResponse<Candidate>>(
        `/api/v1/candidates/?${params.toString()}`
      );
      setCandidatesData(res);
    } catch {
      setError("Failed to load candidates. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchCandidates(search, page), 300);
    return () => clearTimeout(debounceRef.current);
  }, [search, page, fetchCandidates]);

  // Load organizations for new candidate dropdown
  useEffect(() => {
    api
      .get<Organization[] | { results: Organization[] }>("/api/v1/organizations/")
      .then((data) => {
        const list = Array.isArray(data) ? data : data?.results ?? [];
        setOrgs(list);
        if (list.length > 0 && !form.organization) {
          setForm((prev) => ({ ...prev, organization: list[0].id }));
        }
      })
      .catch(() => {});
  }, [form.organization]);

  async function handleCreateCandidate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setModalError(null);

    const skillsArray = form.skills_input
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      await api.post<Candidate>("/api/v1/candidates/", {
        organization: form.organization,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        location: form.location.trim(),
        current_company: form.current_company.trim(),
        current_title: form.current_title.trim(),
        total_experience_years: form.total_experience_years
          ? parseInt(form.total_experience_years, 10)
          : null,
        skills: skillsArray,
        notes: form.notes.trim(),
      });

      setIsModalOpen(false);
      setForm({
        organization: orgs.length > 0 ? orgs[0].id : "",
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        location: "",
        current_company: "",
        current_title: "",
        total_experience_years: "",
        skills_input: "",
        notes: "",
      });
      fetchCandidates(search, 1);
    } catch (err) {
      setModalError(extractApiErrors(err));
    } finally {
      setSubmitting(false);
    }
  }

  const totalPages = candidatesData ? Math.ceil(candidatesData.count / 20) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Candidates</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {candidatesData ? `${candidatesData.count} candidates in your database` : "Manage candidate profiles and resumes"}
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 transition-colors self-start sm:self-auto"
        >
          + Add candidate
        </button>
      </div>

      {/* Search Input */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Search by candidate name, email, company, or skills..."
          className="w-full max-w-md rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </div>

      {/* Content */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-sm text-zinc-400">Loading candidates…</div>
      ) : (
        <CandidateTable candidates={candidatesData?.results ?? []} />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-zinc-100 pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-50 disabled:opacity-40"
          >
            ← Previous
          </button>
          <span className="text-xs text-zinc-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-50 disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}

      {/* Add Candidate Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-100">
              <h2 className="text-lg font-bold text-zinc-900">Add New Candidate</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreateCandidate} className="mt-4 space-y-4 text-sm">
              {orgs.length > 1 && (
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Organisation *
                  </label>
                  <select
                    value={form.organization}
                    onChange={(e) => setForm({ ...form, organization: e.target.value })}
                    required
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  >
                    {orgs.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    First Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={form.first_name}
                    onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={form.last_name}
                    onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Current Company
                  </label>
                  <input
                    type="text"
                    value={form.current_company}
                    onChange={(e) => setForm({ ...form, current_company: e.target.value })}
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Current Title
                  </label>
                  <input
                    type="text"
                    value={form.current_title}
                    onChange={(e) => setForm({ ...form, current_title: e.target.value })}
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Experience (Years)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={form.total_experience_years}
                    onChange={(e) =>
                      setForm({ ...form, total_experience_years: e.target.value })
                    }
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">Location</label>
                <input
                  type="text"
                  placeholder="e.g. San Francisco, CA or Remote"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">
                  Skills (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="Python, Django, React, AWS, Docker"
                  value={form.skills_input}
                  onChange={(e) => setForm({ ...form, skills_input: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">
                  Recruiter Notes
                </label>
                <textarea
                  rows={2}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg border border-zinc-300 px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-700 disabled:opacity-50"
                >
                  {submitting ? "Saving…" : "Save candidate"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
