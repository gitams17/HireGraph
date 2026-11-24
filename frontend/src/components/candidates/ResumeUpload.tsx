"use client";

import { useState, useRef } from "react";
import { api, extractApiErrors } from "@/lib/api";
import { Resume } from "@/types";

interface ResumeUploadProps {
  candidateId: string;
  resumes: Resume[];
  onUploadSuccess: (newResume: Resume) => void;
}

export function ResumeUpload({ candidateId, resumes, onUploadSuccess }: ResumeUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function formatBytes(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check size client-side (10 MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError("File exceeds maximum allowed size of 10 MB.");
      return;
    }

    // Check extension
    const name = file.name.toLowerCase();
    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      setError("Only PDF and DOCX files are allowed.");
      return;
    }

    setError(null);
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("is_primary", "true");

      const created = await api.upload<Resume>(
        `/api/v1/candidates/${candidateId}/resumes/`,
        formData
      );
      onUploadSuccess(created);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setError(extractApiErrors(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-zinc-900">Resumes & Documents</h3>
        <label className="cursor-pointer rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-700 transition-colors">
          {uploading ? "Uploading…" : "+ Upload resume"}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
          />
        </label>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {resumes.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-200 p-6 text-center text-xs text-zinc-400">
          No resumes uploaded yet. Upload a PDF or DOCX file (max 10 MB).
        </div>
      ) : (
        <div className="divide-y divide-zinc-100 rounded-lg border border-zinc-200 bg-white">
          {resumes.map((resume) => (
            <div
              key={resume.id}
              className="flex items-center justify-between p-3.5 text-sm hover:bg-zinc-50 transition-colors"
            >
              <div className="flex items-center space-x-3 min-w-0">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-zinc-600 font-bold text-xs uppercase">
                  {resume.file_name.endsWith(".pdf") ? "PDF" : "DOC"}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-zinc-900 truncate">
                      {resume.file_name}
                    </span>
                    {resume.is_primary && (
                      <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                        Primary
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-zinc-400 mt-0.5">
                    {formatBytes(resume.file_size)} • Uploaded{" "}
                    {new Date(resume.created_at).toLocaleDateString()}
                    {resume.uploaded_by_name ? ` by ${resume.uploaded_by_name}` : ""}
                  </div>
                </div>
              </div>

              <a
                href={resume.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 rounded-md border border-zinc-200 px-3 py-1 text-xs font-semibold text-zinc-700 hover:bg-zinc-100 transition-colors"
              >
                Download
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
