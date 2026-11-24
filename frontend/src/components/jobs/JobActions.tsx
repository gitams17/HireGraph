"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { JobRequisition, OrganizationRole } from "@/types";

const CAN_MANAGE: OrganizationRole[] = ["owner", "admin", "recruiter"];

interface JobActionsProps {
  job: JobRequisition;
  currentUserRole: OrganizationRole | null;
}

export function JobActions({ job, currentUserRole }: JobActionsProps) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const canManage = currentUserRole !== null && CAN_MANAGE.includes(currentUserRole);

  if (!canManage) return null;

  async function handleDelete() {
    if (!confirm(`Delete "${job.title}"? This action cannot be undone.`)) return;
    setDeleting(true);
    try {
      await api.delete(`/api/v1/jobs/${job.id}/`);
      router.push("/jobs");
      router.refresh();
    } catch {
      alert("Failed to delete job. Please try again.");
      setDeleting(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <Link
        href={`/jobs/${job.id}/edit`}
        className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 transition-colors"
      >
        Edit
      </Link>
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-100 disabled:opacity-50 transition-colors"
      >
        {deleting ? "Deleting…" : "Delete"}
      </button>
    </div>
  );
}
