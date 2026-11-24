"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

/**
 * Dashboard route group layout.
 * — Checks authentication on the client side (middleware is the first line).
 * — Renders a sidebar navigation once the user is confirmed.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-screen bg-zinc-50">
        <span className="text-sm font-medium text-zinc-500">Loading…</span>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 border-r border-zinc-200 bg-white flex flex-col">
        <div className="px-6 py-5 border-b border-zinc-200">
          <span className="text-lg font-bold text-zinc-900">HireGraph</span>
        </div>
        <nav className="flex-1 px-4 py-4 space-y-1">
          <NavLink href="/dashboard">Dashboard</NavLink>
          <NavLink href="/jobs">Jobs</NavLink>
          <NavLink href="/candidates">Candidates</NavLink>
          <NavLink href="/applications">Applications</NavLink>
          <NavLink href="/interviews">Interviews</NavLink>
          <NavLink href="/workflows">Workflows</NavLink>
          <NavLink href="/settings/profile">Profile</NavLink>
          <NavLink href="/settings/organization">Organisation</NavLink>
          <NavLink href="/settings/members">Members</NavLink>
        </nav>
        <div className="px-4 py-4 border-t border-zinc-200">
          <div className="mb-2 text-xs text-zinc-500 truncate">{user.email}</div>
          <button
            onClick={logout}
            className="w-full rounded-lg px-3 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 text-left transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-zinc-50">
        <div className="mx-auto max-w-4xl px-6 py-8">{children}</div>
      </main>
    </div>
  );
}

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="block rounded-lg px-3 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 transition-colors"
    >
      {children}
    </Link>
  );
}
