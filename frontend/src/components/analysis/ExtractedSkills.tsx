import { ParsedResume } from "@/types";

interface ExtractedSkillsProps {
  extractedData: ParsedResume;
}

export function ExtractedSkills({ extractedData }: ExtractedSkillsProps) {
  const techSkills = extractedData?.technical_skills || [];
  const softSkills = extractedData?.soft_skills || [];

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm space-y-5">
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <h3 className="text-sm font-semibold text-zinc-900">
            Technical & Hard Skills ({techSkills.length})
          </h3>
        </div>
        {techSkills.length === 0 ? (
          <p className="text-xs text-zinc-400">No technical skills detected in text.</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {techSkills.map((skill, i) => (
              <span
                key={i}
                className="rounded-lg bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-800 border border-zinc-200"
              >
                {skill}
              </span>
            ))}
          </div>
        )}
      </div>

      {softSkills.length > 0 && (
        <div className="border-t border-zinc-100 pt-4">
          <h3 className="text-sm font-semibold text-zinc-900 mb-2.5">
            Soft Skills & Attributes ({softSkills.length})
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {softSkills.map((skill, i) => (
              <span
                key={i}
                className="rounded-lg bg-blue-50/70 px-2.5 py-1 text-xs font-medium text-blue-800 border border-blue-200"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
