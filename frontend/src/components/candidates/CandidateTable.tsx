"use client";

import Link from "next/link";
import { Candidate } from "@/types";

interface CandidateTableProps {
  candidates: Candidate[];
}

export function CandidateTable({ candidates }: CandidateTableProps) {
  if (candidates.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white py-16 text-center">
        <p className="text-sm font-medium text-zinc-600">No candidates found</p>
        <p className="mt-1 text-xs text-zinc-400">
          Try refining your search filters or add a new candidate.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-200 bg-zinc-50 text-xs font-semibold uppercase tracking-wider text-zinc-500">
            <tr>
              <th className="px-6 py-3.5">Candidate</th>
              <th className="px-6 py-3.5">Current Role</th>
              <th className="px-6 py-3.5">Skills</th>
              <th className="px-6 py-3.5">Experience</th>
              <th className="px-6 py-3.5">Resumes</th>
              <th className="px-6 py-3.5">Applications</th>
              <th className="px-6 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 text-zinc-700">
            {candidates.map((candidate) => (
              <tr key={candidate.id} className="hover:bg-zinc-50/70 transition-colors">
                <td className="px-6 py-4">
                  <Link
                    href={`/candidates/${candidate.id}`}
                    className="font-semibold text-zinc-900 hover:underline block"
                  >
                    {candidate.full_name || `${candidate.first_name} ${candidate.last_name}`}
                  </Link>
                  <span className="text-xs text-zinc-400 block mt-0.5">{candidate.email}</span>
                </td>
                <td className="px-6 py-4">
                  <div className="font-medium text-zinc-800">
                    {candidate.current_title || "—"}
                  </div>
                  {candidate.current_company && (
                    <div className="text-xs text-zinc-500">{candidate.current_company}</div>
                  )}
                </td>
                <td className="px-6 py-4 max-w-xs">
                  <div className="flex flex-wrap gap-1">
                    {candidate.skills && candidate.skills.length > 0 ? (
                      candidate.skills.slice(0, 3).map((skill, i) => (
                        <span
                          key={i}
                          className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 font-medium"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-zinc-400">—</span>
                    )}
                    {candidate.skills && candidate.skills.length > 3 && (
                      <span className="text-xs text-zinc-400">+{candidate.skills.length - 3}</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-zinc-600">
                  {candidate.total_experience_years != null
                    ? `${candidate.total_experience_years} yrs`
                    : "—"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-700">
                    {candidate.resume_count ?? candidate.resumes?.length ?? 0} file(s)
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                    {candidate.application_count ?? candidate.applications?.length ?? 0} applied
                  </span>
                </td>
                <td className="px-6 py-4 text-right whitespace-nowrap">
                  <Link
                    href={`/candidates/${candidate.id}`}
                    className="text-xs font-semibold text-zinc-900 hover:text-zinc-700 underline"
                  >
                    View profile →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
