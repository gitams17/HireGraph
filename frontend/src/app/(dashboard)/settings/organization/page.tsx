"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Organization } from "@/types";
import OrganizationSetupForm from "@/components/organization/OrganizationSetupForm";
import Link from "next/link";

export default function OrganizationSettingsPage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Organization[]>("/api/v1/organizations/")
      .then(setOrgs)
      .catch(() => setOrgs([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-zinc-400">Loading…</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Organisation</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Manage your organisation details.
          </p>
        </div>
      </div>

      {orgs.length === 0 ? (
        <div className="mt-8 max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <p className="mb-4 text-sm text-zinc-600">
            You are not part of any organisation yet.
          </p>
          <OrganizationSetupForm
            onSuccess={(org) => setOrgs([org])}
          />
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {orgs.map((org) => (
            <div
              key={org.id}
              className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm"
            >
              <h3 className="font-semibold text-zinc-900">{org.name}</h3>
              <p className="text-sm text-zinc-500">Slug: {org.slug}</p>
              <p className="text-sm text-zinc-500">
                {org.member_count} member{org.member_count !== 1 ? "s" : ""}
              </p>
              <p className="mt-2 text-xs capitalize text-zinc-400">
                Your role: {org.current_user_role?.replace("_", " ")}
              </p>
              <Link
                href="/settings/members"
                className="mt-3 inline-block text-sm font-medium text-zinc-700 underline underline-offset-2"
              >
                Manage members →
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
