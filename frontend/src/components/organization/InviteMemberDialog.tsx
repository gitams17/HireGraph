"use client";

import { useState } from "react";
import { api, extractApiErrors } from "@/lib/api";
import type { OrganizationInvitation, OrganizationRole } from "@/types";
import RoleSelector from "@/components/settings/RoleSelector";

interface Props {
  orgId: string;
  onClose: () => void;
  onSuccess: (invitation: OrganizationInvitation) => void;
}

export default function InviteMemberDialog({ orgId, onClose, onSuccess }: Props) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<OrganizationRole>("recruiter");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const invitation = await api.post<OrganizationInvitation>(
        `/api/v1/organizations/${orgId}/invitations/`,
        { email, role }
      );
      onSuccess(invitation);
    } catch (err) {
      setError(extractApiErrors(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      {/* Dialog */}
      <div
        className="relative z-50 w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-zinc-900">Invite team member</h2>
        <p className="mt-1 text-sm text-zinc-500">
          They will receive an invitation link valid for 7 days.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              Email address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError("");
              }}
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-400"
              placeholder="colleague@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              Role
            </label>
            <RoleSelector
              value={role}
              onChange={setRole}
              excludeOwner
              className="w-full"
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 transition-colors"
            >
              {submitting ? "Sending…" : "Send invitation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
