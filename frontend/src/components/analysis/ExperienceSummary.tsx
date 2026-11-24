import { ParsedResume } from "@/types";

interface ExperienceSummaryProps {
  extractedData: ParsedResume;
}

export function ExperienceSummary({ extractedData }: ExperienceSummaryProps) {
  const experiences = extractedData?.experience || [];
  const projects = extractedData?.projects || [];
  const education = extractedData?.education || [];
  const certifications = extractedData?.certifications || [];

  return (
    <div className="space-y-6">
      {/* Work History */}
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-zinc-900 mb-4">
          Parsed Work Experience ({experiences.length})
        </h3>
        {experiences.length === 0 ? (
          <p className="text-xs text-zinc-400">No work experience extracted.</p>
        ) : (
          <div className="relative border-l border-zinc-200 pl-6 ml-3 space-y-6">
            {experiences.map((exp, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full bg-zinc-900 ring-4 ring-white" />
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                  <div className="font-semibold text-zinc-900 text-sm">
                    {exp.title}
                    <span className="font-normal text-zinc-500"> at </span>
                    {exp.company}
                  </div>
                  <span className="text-xs text-zinc-400">
                    {exp.start_date || "—"} - {exp.is_current ? "Present" : exp.end_date || "—"}
                  </span>
                </div>

                {exp.description && (
                  <p className="mt-1 text-xs text-zinc-600 whitespace-pre-wrap">
                    {exp.description}
                  </p>
                )}

                {exp.technologies_used && exp.technologies_used.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {exp.technologies_used.map((tech, idx) => (
                      <span
                        key={idx}
                        className="rounded bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-700"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Projects */}
      {projects.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-base font-semibold text-zinc-900 mb-4">
            Highlighted Projects ({projects.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((proj, idx) => (
              <div key={idx} className="rounded-lg border border-zinc-200 p-4 bg-zinc-50/50">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-zinc-900 text-sm">{proj.name}</h4>
                  {proj.url && (
                    <a
                      href={proj.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Link ↗
                    </a>
                  )}
                </div>
                {proj.description && (
                  <p className="mt-1 text-xs text-zinc-600 line-clamp-3">{proj.description}</p>
                )}
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1">
                    {proj.technologies.map((t, i) => (
                      <span
                        key={i}
                        className="rounded bg-white px-2 py-0.5 text-[10px] font-medium text-zinc-700 border border-zinc-200"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education & Certifications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Education */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-zinc-900 mb-3">Education</h3>
          {education.length === 0 ? (
            <p className="text-xs text-zinc-400">No education extracted.</p>
          ) : (
            <div className="space-y-3">
              {education.map((edu, i) => (
                <div key={i} className="text-xs">
                  <div className="font-semibold text-zinc-800">
                    {edu.degree} {edu.field_of_study ? `in ${edu.field_of_study}` : ""}
                  </div>
                  <div className="text-zinc-500">{edu.institution}</div>
                  {(edu.start_year || edu.end_year) && (
                    <div className="text-zinc-400 text-[11px]">
                      {edu.start_year || ""} {edu.end_year ? `- ${edu.end_year}` : ""}
                      {edu.grade_or_gpa ? ` • GPA: ${edu.grade_or_gpa}` : ""}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Certifications */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-zinc-900 mb-3">Certifications</h3>
          {certifications.length === 0 ? (
            <p className="text-xs text-zinc-400">No certifications listed.</p>
          ) : (
            <div className="space-y-3">
              {certifications.map((cert, i) => (
                <div key={i} className="text-xs">
                  <div className="font-semibold text-zinc-800">{cert.name}</div>
                  <div className="text-zinc-500">
                    {cert.issuer} {cert.issue_year ? `(${cert.issue_year})` : ""}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
