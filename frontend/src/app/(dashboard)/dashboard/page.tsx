"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import type { Organization } from "@/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loadingOrgs, setLoadingOrgs] = useState(true);

  useEffect(() => {
    api
      .get<Organization[] | { results: Organization[] }>("/api/v1/organizations/")
      .then((data) => {
        setOrgs(Array.isArray(data) ? data : (data?.results ?? []));
      })
      .catch(() => setOrgs([]))
      .finally(() => setLoadingOrgs(false));
  }, []);

  const hasOrg = orgs.length > 0;

  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-900">
        Welcome back, {user?.first_name}
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        Here&apos;s what&apos;s happening in your workspace.
      </p>

      <div className="mt-8">
        {loadingOrgs ? (
          <p className="text-sm text-zinc-400">Loading organisations…</p>
        ) : hasOrg ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {orgs.map((org) => (
              <div
                key={org.id}
                className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm"
              >
                <h3 className="font-semibold text-zinc-900">{org.name}</h3>
                <p className="mt-1 text-sm text-zinc-500">
                  {org.member_count} member{org.member_count !== 1 ? "s" : ""}
                </p>
                <p className="mt-1 text-xs capitalize text-zinc-400">
                  Your role: {org.current_user_role?.replace("_", " ")}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-300 bg-white p-10 text-center">
            <h3 className="font-semibold text-zinc-900">No organisation yet</h3>
            <p className="mt-1 text-sm text-zinc-500">
              Create your first organisation to start hiring.
            </p>
            <Link
              href="/onboarding"
              className="mt-4 inline-block rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 transition-colors"
            >
              Get started
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
