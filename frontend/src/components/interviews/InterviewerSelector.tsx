"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Organization, OrganizationMembership } from "@/types";

interface InterviewerSelectorProps {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
}

export default function InterviewerSelector({
  selectedIds,
  onChange,
  disabled = false,
}: InterviewerSelectorProps) {
  const [members, setMembers] = useState<OrganizationMembership[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMembers() {
      try {
        const orgs = await api.get<Organization[]>("/api/v1/organizations/");
        if (orgs.length > 0) {
          const mList = await api.get<OrganizationMembership[]>(
            `/api/v1/organizations/${orgs[0].id}/members/`
          );
          setMembers(mList.filter((m) => m.is_active));
        }
      } catch {
        setMembers([]);
      } finally {
        setLoading(false);
      }
    }
    loadMembers();
  }, []);

  const toggleUser = (userId: string) => {
    if (disabled) return;
    if (selectedIds.includes(userId)) {
      onChange(selectedIds.filter((id) => id !== userId));
    } else {
      onChange([...selectedIds, userId]);
    }
  };

  if (loading) {
    return <div className="text-xs text-zinc-400">Loading interviewers…</div>;
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold text-zinc-700">
        Assigned Interview Panel ({selectedIds.length} selected)
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-2 border border-zinc-200 rounded-lg bg-zinc-50">
        {members.map((member) => {
          const isSelected = selectedIds.includes(member.user.id);
          const displayName = member.user.full_name || `${member.user.first_name} ${member.user.last_name}`.trim() || member.user.email;
          return (
            <button
              key={member.id}
              type="button"
              disabled={disabled}
              onClick={() => toggleUser(member.user.id)}
              className={`flex items-center justify-between p-2 rounded-md border text-left text-xs transition-colors ${
                isSelected
                  ? "bg-zinc-900 border-zinc-900 text-white"
                  : "bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-100"
              }`}
            >
              <div className="truncate">
                <div className="font-semibold truncate">{displayName}</div>
                <div className={`text-[10px] truncate ${isSelected ? "text-zinc-300" : "text-zinc-500"}`}>
                  {member.user.email} • {member.role}
                </div>
              </div>
              <div className="ml-2 shrink-0">
                {isSelected ? (
                  <span className="text-xs font-bold text-white">✓</span>
                ) : (
                  <span className="text-xs text-zinc-400">+</span>
                )}
              </div>
            </button>
          );
        })}
        {members.length === 0 && (
          <div className="text-xs text-zinc-500 p-2 col-span-2">No team members found.</div>
        )}
      </div>
    </div>
  );
}
