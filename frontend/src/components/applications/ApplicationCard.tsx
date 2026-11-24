import Link from "next/link";
import { Application, STAGE_COLORS, STAGE_LABELS } from "@/types";

interface ApplicationCardProps {
  application: Application;
  onAdvanceClick?: () => void;
}

export function ApplicationCard({ application, onAdvanceClick }: ApplicationCardProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/candidates/${application.candidate_id}`}
          className="font-semibold text-zinc-900 hover:underline text-sm leading-snug line-clamp-1"
        >
          {application.candidate_name}
        </Link>
        <span
          className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
            STAGE_COLORS[application.stage] || "bg-zinc-100 text-zinc-600 border-zinc-200"
          }`}
        >
          {STAGE_LABELS[application.stage] || application.stage}
        </span>
      </div>

      <div className="mt-1 text-xs text-zinc-500 truncate">
        {application.job_title}
      </div>

      {application.candidate_company && (
        <div className="mt-0.5 text-[11px] text-zinc-400 truncate">
          {application.candidate_title ? `${application.candidate_title} at ` : ""}
          {application.candidate_company}
        </div>
      )}

      {application.rating && application.rating > 0 ? (
        <div className="mt-2 flex items-center text-xs text-amber-500 font-semibold">
          {"★".repeat(application.rating)}
          <span className="text-[10px] text-zinc-400 font-normal ml-1">
            ({application.rating}/5)
          </span>
        </div>
      ) : null}

      <div className="mt-4 flex items-center justify-between border-t border-zinc-100 pt-3 text-xs">
        <span className="text-[11px] text-zinc-400">
          {new Date(application.created_at).toLocaleDateString()}
        </span>
        <div className="flex items-center space-x-2">
          {onAdvanceClick && (
            <button
              onClick={onAdvanceClick}
              className="font-medium text-zinc-600 hover:text-zinc-900 text-xs"
            >
              Advance →
            </button>
          )}
          <Link
            href={`/applications/${application.id}`}
            className="font-semibold text-zinc-900 hover:underline"
          >
            Review
          </Link>
        </div>
      </div>
    </div>
  );
}
