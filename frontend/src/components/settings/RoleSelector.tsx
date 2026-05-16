"use client";

import type { OrganizationRole } from "@/types";
import { ROLE_LABELS } from "@/types";

interface Props {
  value: OrganizationRole;
  onChange: (role: OrganizationRole) => void;
  /** Hide the Owner option (for forms where only admins are assigning roles). */
  excludeOwner?: boolean;
  className?: string;
}

const ALL_ROLES: OrganizationRole[] = [
  "owner",
  "admin",
  "recruiter",
  "hiring_manager",
  "interviewer",
];

export default function RoleSelector({
  value,
  onChange,
  excludeOwner = false,
  className = "",
}: Props) {
  const roles = excludeOwner ? ALL_ROLES.filter((r) => r !== "owner") : ALL_ROLES;

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as OrganizationRole)}
      className={`rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-900 focus:border-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-400 ${className}`}
    >
      {roles.map((role) => (
        <option key={role} value={role}>
          {ROLE_LABELS[role]}
        </option>
      ))}
    </select>
  );
}
