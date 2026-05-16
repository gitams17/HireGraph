/**
 * Typed API client for HireGraph.
 *
 * All requests go to relative paths (/api/v1/…) which Next.js rewrites to
 * the Django backend at port 8000.  This keeps cookies on the same origin
 * and avoids every cross-origin SameSite / CORS complication.
 *
 * CSRF handling:
 *   – Django sets a non-HttpOnly `csrftoken` cookie on the first GET.
 *   – Every mutation (POST/PATCH/PUT/DELETE) reads that cookie and sends it
 *     as the `X-CSRFToken` header, which Django validates.
 */

import type { ApiError } from "@/types";

// ---------------------------------------------------------------------------
// CSRF helpers
// ---------------------------------------------------------------------------

function getCsrfToken(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

const MUTATION_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };

  if (MUTATION_METHODS.has(method)) {
    const token = getCsrfToken();
    if (token) headers["X-CSRFToken"] = token;
  }

  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "include",
  });

  // 204 No Content
  if (response.status === 204) return undefined as unknown as T;

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    const err: ApiError = { status: response.status, data: body };
    throw err;
  }

  return body as T;
}

// ---------------------------------------------------------------------------
// Public API surface
// ---------------------------------------------------------------------------

export const api = {
  get: <T>(path: string): Promise<T> => request<T>(path, { method: "GET" }),

  post: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),

  patch: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),

  put: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),

  delete: <T>(path: string): Promise<T> =>
    request<T>(path, { method: "DELETE" }),
};

// ---------------------------------------------------------------------------
// Error formatting helper
// ---------------------------------------------------------------------------

export function extractApiErrors(err: unknown): string {
  if (!err || typeof err !== "object") return "An unexpected error occurred.";
  const apiErr = err as ApiError;
  if (!apiErr.data) return "An unexpected error occurred.";
  const { detail, non_field_errors, ...fieldErrors } = apiErr.data;
  if (detail) return detail;
  if (non_field_errors?.length) return non_field_errors[0];
  const fieldMessages = Object.entries(fieldErrors)
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
    .join(" ");
  return fieldMessages || "An unexpected error occurred.";
}
