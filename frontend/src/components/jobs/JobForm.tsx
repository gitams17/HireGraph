"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
  JobRequisition,
  JobStatus,
  EmploymentType,
  JOB_STATUS_LABELS,
  EMPLOYMENT_TYPE_LABELS,
  ApiError,
} from "@/types";

interface JobFormProps {
  organizationId: string;
  /** Pre-filled for edit mode */
  initialData?: Partial<JobRequisition>;
  jobId?: string;
}

type FormData = {
  title: string;
  department: string;
  location: string;
  employment_type: EmploymentType;
  experience_min: string;
  experience_max: string;
  required_skills: string; // comma-separated in the form
  responsibilities: string; // newline-separated in the form
  status: JobStatus;
};

const DEFAULTS: FormData = {
  title: "",
  department: "",
  location: "",
  employment_type: "full_time",
  experience_min: "",
  experience_max: "",
  required_skills: "",
  responsibilities: "",
  status: "draft",
};

export function JobForm({ organizationId, initialData, jobId }: JobFormProps) {
  const router = useRouter();
  const isEdit = Boolean(jobId);

  const [form, setForm] = useState<FormData>(() => {
    if (!initialData) return DEFAULTS;
    return {
      title: initialData.title ?? "",
      department: initialData.department ?? "",
      location: initialData.location ?? "",
      employment_type: initialData.employment_type ?? "full_time",
      experience_min: initialData.experience_min?.toString() ?? "",
      experience_max: initialData.experience_max?.toString() ?? "",
      required_skills: (initialData.required_skills ?? []).join(", "),
      responsibilities: (initialData.responsibilities ?? []).join("\n"),
      status: initialData.status ?? "draft",
    };
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  function set(field: keyof FormData, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});

    const payload = {
      organization: organizationId,
      title: form.title,
      department: form.department,
      location: form.location,
      employment_type: form.employment_type,
      experience_min: form.experience_min ? parseInt(form.experience_min, 10) : null,
      experience_max: form.experience_max ? parseInt(form.experience_max, 10) : null,
      required_skills: form.required_skills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      responsibilities: form.responsibilities
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      status: form.status,
    };

    try {
      if (isEdit) {
        await api.patch(`/api/v1/jobs/${jobId}/`, payload);
      } else {
        await api.post("/api/v1/jobs/", payload);
      }
      router.push("/jobs");
      router.refresh();
    } catch (err) {
      const apiErr = err as ApiError;
      const fieldErrors: Record<string, string> = {};
      for (const [key, val] of Object.entries(apiErr.data ?? {})) {
        fieldErrors[key] = Array.isArray(val) ? val.join(" ") : String(val);
      }
      setErrors(fieldErrors);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Global error */}
      {errors.detail && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {errors.detail}
        </div>
      )}

      {/* Title */}
      <Field label="Job title *" error={errors.title}>
        <input
          type="text"
          value={form.title}
          onChange={(e) => set("title", e.target.value)}
          required
          placeholder="e.g. Senior Backend Engineer"
          className={inputCls(errors.title)}
        />
      </Field>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {/* Department */}
        <Field label="Department" error={errors.department}>
          <input
            type="text"
            value={form.department}
            onChange={(e) => set("department", e.target.value)}
            placeholder="e.g. Engineering"
            className={inputCls(errors.department)}
          />
        </Field>

        {/* Location */}
        <Field label="Location" error={errors.location}>
          <input
            type="text"
            value={form.location}
            onChange={(e) => set("location", e.target.value)}
            placeholder="e.g. Remote, London"
            className={inputCls(errors.location)}
          />
        </Field>

        {/* Employment type */}
        <Field label="Employment type" error={errors.employment_type}>
          <select
            value={form.employment_type}
            onChange={(e) => set("employment_type", e.target.value as EmploymentType)}
            className={inputCls(errors.employment_type)}
          >
            {(Object.entries(EMPLOYMENT_TYPE_LABELS) as [EmploymentType, string][]).map(
              ([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              )
            )}
          </select>
        </Field>

        {/* Status */}
        <Field label="Status" error={errors.status}>
          <select
            value={form.status}
            onChange={(e) => set("status", e.target.value as JobStatus)}
            className={inputCls(errors.status)}
          >
            {(Object.entries(JOB_STATUS_LABELS) as [JobStatus, string][]).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </Field>

        {/* Experience min */}
        <Field label="Min. experience (years)" error={errors.experience_min}>
          <input
            type="number"
            min={0}
            value={form.experience_min}
            onChange={(e) => set("experience_min", e.target.value)}
            placeholder="e.g. 3"
            className={inputCls(errors.experience_min)}
          />
        </Field>

        {/* Experience max */}
        <Field label="Max. experience (years)" error={errors.experience_max ?? errors.experience_max}>
          <input
            type="number"
            min={0}
            value={form.experience_max}
            onChange={(e) => set("experience_max", e.target.value)}
            placeholder="e.g. 7"
            className={inputCls(errors.experience_max)}
          />
        </Field>
      </div>

      {/* Required skills */}
      <Field
        label="Required skills"
        error={errors.required_skills}
        hint="Comma-separated list, e.g. Python, Django, PostgreSQL"
      >
        <input
          type="text"
          value={form.required_skills}
          onChange={(e) => set("required_skills", e.target.value)}
          placeholder="Python, Django, PostgreSQL"
          className={inputCls(errors.required_skills)}
        />
      </Field>

      {/* Responsibilities */}
      <Field
        label="Responsibilities"
        error={errors.responsibilities}
        hint="One per line"
      >
        <textarea
          rows={5}
          value={form.responsibilities}
          onChange={(e) => set("responsibilities", e.target.value)}
          placeholder="Design and implement REST APIs&#10;Conduct code reviews&#10;Collaborate with product team"
          className={inputCls(errors.responsibilities) + " resize-y"}
        />
      </Field>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-zinc-700 disabled:opacity-50 transition-colors"
        >
          {submitting ? "Saving…" : isEdit ? "Save changes" : "Create job"}
        </button>
        <button
          type="button"
          onClick={() => router.back()}
          className="rounded-lg px-5 py-2.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function inputCls(error?: string) {
  return [
    "w-full rounded-lg border px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400",
    "focus:outline-none focus:ring-2 focus:ring-zinc-400",
    error ? "border-red-400 bg-red-50" : "border-zinc-300 bg-white",
  ].join(" ");
}

function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-zinc-700">{label}</label>
      {children}
      {hint && !error && <p className="mt-1 text-xs text-zinc-500">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
