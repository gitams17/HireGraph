"use client";

import { useState } from "react";
import { api, extractApiErrors } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { User } from "@/types";

export default function UserProfile() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({
    first_name: user?.first_name ?? "",
    last_name: user?.last_name ?? "",
  });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setSuccess(false);
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess(false);
    try {
      await api.patch<User>("/api/v1/auth/me/", form);
      await refresh();
      setSuccess(true);
    } catch (err) {
      setError(extractApiErrors(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <p className="text-sm text-zinc-500 mb-4">
          <strong className="text-zinc-900">Email:</strong> {user?.email}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">
            First name
          </label>
          <input
            type="text"
            name="first_name"
            required
            value={form.first_name}
            onChange={handleChange}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">
            Last name
          </label>
          <input
            type="text"
            name="last_name"
            required
            value={form.last_name}
            onChange={handleChange}
            className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">
          Profile updated successfully.
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 transition-colors"
      >
        {submitting ? "Saving…" : "Save changes"}
      </button>
    </form>
  );
}
