"use client";

import { useState } from "react";
import Link from "next/link";
import { Candidate, STAGE_COLORS, STAGE_LABELS } from "@/types";

interface CandidateProfileProps {
  candidate: Candidate;
  onApplyJobClick: () => void;
}

export function CandidateProfile({ candidate, onApplyJobClick }: CandidateProfileProps) {
  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-zinc-900">
                {candidate.full_name || `${candidate.first_name} ${candidate.last_name}`}
              </h1>
              {candidate.location && (
                <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600">
                  {candidate.location}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-zinc-600">
              {candidate.current_title || "No current title specified"}
              {candidate.current_company ? ` at ${candidate.current_company}` : ""}
            </p>
          </div>

          <button
            onClick={onApplyJobClick}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700 transition-colors shrink-0"
          >
            + Link to Job
          </button>
        </div>

        {/* Contact info grid */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 border-t border-zinc-100 pt-5 text-sm">
          <div>
            <span className="block text-xs font-medium text-zinc-400">Email</span>
            <a
              href={`mailto:${candidate.email}`}
              className="text-zinc-800 hover:underline font-medium"
            >
              {candidate.email}
            </a>
          </div>
          <div>
            <span className="block text-xs font-medium text-zinc-400">Phone</span>
            <span className="text-zinc-800">{candidate.phone || "—"}</span>
          </div>
          <div>
            <span className="block text-xs font-medium text-zinc-400">Experience</span>
            <span className="text-zinc-800">
              {candidate.total_experience_years != null
                ? `${candidate.total_experience_years} years`
                : "—"}
            </span>
          </div>
          {candidate.linkedin_url && (
            <div>
              <span className="block text-xs font-medium text-zinc-400">LinkedIn</span>
              <a
                href={candidate.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:underline text-xs"
              >
                {candidate.linkedin_url}
              </a>
            </div>
          )}
          {candidate.github_url && (
            <div>
              <span className="block text-xs font-medium text-zinc-400">GitHub</span>
              <a
                href={candidate.github_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:underline text-xs"
              >
                {candidate.github_url}
              </a>
            </div>
          )}
          {candidate.portfolio_url && (
            <div>
              <span className="block text-xs font-medium text-zinc-400">Portfolio</span>
              <a
                href={candidate.portfolio_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:underline text-xs"
              >
                {candidate.portfolio_url}
              </a>
            </div>
          )}
        </div>

        {/* Skills */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="mt-5 border-t border-zinc-100 pt-4">
            <span className="block text-xs font-medium text-zinc-400 mb-2">Skills</span>
            <div className="flex flex-wrap gap-1.5">
              {candidate.skills.map((skill, index) => (
                <span
                  key={index}
                  className="rounded-md bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {candidate.notes && (
          <div className="mt-5 border-t border-zinc-100 pt-4">
            <span className="block text-xs font-medium text-zinc-400 mb-1">Recruiter Notes</span>
            <p className="text-sm text-zinc-600 whitespace-pre-wrap">{candidate.notes}</p>
          </div>
        )}
      </div>

      {/* Applications list */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-zinc-900 mb-4">Job Applications</h3>
        {!candidate.applications || candidate.applications.length === 0 ? (
          <p className="text-xs text-zinc-400">
            This candidate has not been submitted for any jobs yet. Click &quot;+ Link to Job&quot; above to submit an application.
          </p>
        ) : (
          <div className="divide-y divide-zinc-100">
            {candidate.applications.map((app) => (
              <div
                key={app.id}
                className="flex items-center justify-between py-3 text-sm hover:bg-zinc-50 px-2 rounded-lg"
              >
                <div>
                  <Link
                    href={`/applications/${app.id}`}
                    className="font-semibold text-zinc-900 hover:underline"
                  >
                    {app.job_title}
                  </Link>
                  <span className="text-xs text-zinc-400 block">
                    Applied on {new Date(app.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize ${
                      STAGE_COLORS[app.stage] || "bg-zinc-100 text-zinc-600 border-zinc-200"
                    }`}
                  >
                    {STAGE_LABELS[app.stage] || app.stage}
                  </span>
                  <Link
                    href={`/applications/${app.id}`}
                    className="text-xs font-semibold text-zinc-700 hover:text-zinc-900 underline"
                  >
                    Manage →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
