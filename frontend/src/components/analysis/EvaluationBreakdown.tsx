import { CandidateAssessment } from "@/types";

interface EvaluationBreakdownProps {
  assessment: CandidateAssessment;
}

export function EvaluationBreakdown({ assessment }: EvaluationBreakdownProps) {
  const evaluations = assessment?.required_skills_evaluation || [];
  const strengths = assessment?.strengths || [];
  const gaps = assessment?.concerns_or_gaps || [];
  const missing = assessment?.missing_evidence || [];

  const statusBadge: Record<string, { label: string; color: string }> = {
    found: { label: "Evidence Found", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    partial: { label: "Partial Evidence", color: "bg-amber-50 text-amber-700 border-amber-200" },
    missing: { label: "Missing Evidence", color: "bg-red-50 text-red-700 border-red-200" },
  };

  return (
    <div className="space-y-6">
      {/* Required Skills Match Matrix */}
      <div className="rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden">
        <div className="p-5 border-b border-zinc-100">
          <h3 className="text-base font-semibold text-zinc-900">
            Required Skills Alignment & Evidence
          </h3>
          <p className="mt-0.5 text-xs text-zinc-500">
            Skill-by-skill evaluation cross-referenced against projects and work history.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-50 text-xs font-semibold uppercase text-zinc-500 border-b border-zinc-200">
              <tr>
                <th className="px-6 py-3 w-1/4">Required Skill</th>
                <th className="px-6 py-3 w-1/6">Verification</th>
                <th className="px-6 py-3">Substantiated Evidence & Citations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 text-zinc-700">
              {evaluations.map((ev, i) => {
                const badge = statusBadge[ev.status] || statusBadge.missing;
                return (
                  <tr key={i} className="hover:bg-zinc-50/60 transition-colors">
                    <td className="px-6 py-3.5 font-semibold text-zinc-900 text-xs">
                      {ev.skill}
                    </td>
                    <td className="px-6 py-3.5">
                      <span
                        className={`inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap ${badge.color}`}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-xs text-zinc-600">
                      {ev.evidence}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Strengths & Missing Evidence Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Key Strengths */}
        <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-5">
          <h4 className="text-sm font-bold text-emerald-900 mb-3 flex items-center">
            <span className="mr-2">✓</span> Key Verified Strengths
          </h4>
          <ul className="space-y-1.5 text-xs text-emerald-800">
            {strengths.map((str, i) => (
              <li key={i} className="flex items-start">
                <span className="mr-2 text-emerald-500 font-bold">•</span>
                <span>{str}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Missing Evidence / Concerns */}
        <div className="rounded-xl border border-amber-100 bg-amber-50/40 p-5">
          <h4 className="text-sm font-bold text-amber-900 mb-3 flex items-center">
            <span className="mr-2">⚠</span> Missing Evidence & Interview Probing Points
          </h4>
          <ul className="space-y-1.5 text-xs text-amber-800">
            {gaps.concat(missing.map((m) => `No explicit evidence for requirement: ${m}`)).map((gap, i) => (
              <li key={i} className="flex items-start">
                <span className="mr-2 text-amber-500 font-bold">•</span>
                <span>{gap}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
