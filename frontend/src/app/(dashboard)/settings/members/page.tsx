"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Organization, OrganizationMembership } from "@/types";
import InviteMemberDialog from "@/components/organization/InviteMemberDialog";
import RoleSelector from "@/components/settings/RoleSelector";
import { extractApiErrors } from "@/lib/api";
import type { OrganizationRole } from "@/types";

export default function MembersSettingsPage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [members, setMembers] = useState<OrganizationMembership[]>([]);
  const [loading, setLoading] = useState(true);
  const [membersLoading, setMembersLoading] = useState(false);
  const [error, setError] = useState("");
  const [showInvite, setShowInvite] = useState(false);

  useEffect(() => {
    api
      .get<Organization[]>("/api/v1/organizations/")
      .then((data) => {
        setOrgs(data);
        if (data.length > 0) setSelectedOrgId(data[0].id);
      })
      .catch(() => setOrgs([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedOrgId) return;
    setMembersLoading(true);
    api
      .get<OrganizationMembership[]>(`/api/v1/organizations/${selectedOrgId}/members/`)
      .then(setMembers)
      .catch(() => setMembers([]))
      .finally(() => setMembersLoading(false));
  }, [selectedOrgId]);

  const handleRoleChange = async (memberId: string, role: OrganizationRole) => {
    if (!selectedOrgId) return;
    try {
      const updated = await api.patch<OrganizationMembership>(
        `/api/v1/organizations/${selectedOrgId}/members/${memberId}/`,
        { role }
      );
      setMembers((prev) =>
        prev.map((m) => (m.id === memberId ? updated : m))
      );
    } catch (err) {
      setError(extractApiErrors(err));
    }
  };

  const selectedOrg = orgs.find((o) => o.id === selectedOrgId);
  const canManage =
    selectedOrg?.current_user_role === "owner" ||
    selectedOrg?.current_user_role === "admin";

  if (loading) return <p className="text-sm text-zinc-400">Loading…</p>;
  if (orgs.length === 0)
    return (
      <p className="text-sm text-zinc-500">
        You must create an organisation before managing members.
      </p>
    );

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Members</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Manage your organisation&apos;s team.
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => setShowInvite(true)}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 transition-colors"
          >
            Invite member
          </button>
        )}
      </div>

      {/* Org selector — shown if user belongs to multiple orgs */}
      {orgs.length > 1 && (
        <select
          className="mt-4 rounded-lg border border-zinc-200 px-3 py-2 text-sm"
          value={selectedOrgId ?? ""}
          onChange={(e) => setSelectedOrgId(e.target.value)}
        >
          {orgs.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
      )}

      {error && (
        <p className="mt-2 rounded bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </p>
      )}

      <div className="mt-4 rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
        {membersLoading ? (
          <p className="p-6 text-sm text-zinc-400">Loading members…</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Name</th>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Email</th>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {members.map((m) => (
                <tr key={m.id}>
                  <td className="px-4 py-3 font-medium text-zinc-900">
                    {m.user.full_name}
                  </td>
                  <td className="px-4 py-3 text-zinc-500">{m.user.email}</td>
                  <td className="px-4 py-3">
                    {canManage && m.role !== "owner" ? (
                      <RoleSelector
                        value={m.role}
                        onChange={(role) => handleRoleChange(m.id, role)}
                        excludeOwner
                      />
                    ) : (
                      <span className="capitalize text-zinc-600">
                        {m.role.replace("_", " ")}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showInvite && selectedOrgId && (
        <InviteMemberDialog
          orgId={selectedOrgId}
          onClose={() => setShowInvite(false)}
          onSuccess={() => {
            setShowInvite(false);
          }}
        />
      )}
    </div>
  );
}
