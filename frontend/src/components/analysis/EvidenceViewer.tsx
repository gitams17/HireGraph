import { ParsedResume } from "@/types";

interface EvidenceViewerProps {
  extractedData: ParsedResume;
}

export function EvidenceViewer({ extractedData }: EvidenceViewerProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h3 className="text-sm font-semibold text-zinc-900 mb-2">
        Parsed Profile Summary
      </h3>
      <p className="text-xs text-zinc-600 whitespace-pre-wrap leading-relaxed">
        {extractedData?.summary || "No professional summary detected in document."}
      </p>

      <div className="mt-4 pt-4 border-t border-zinc-100 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-zinc-500">
        <div>
          <span className="font-medium text-zinc-700">Parsed Name:</span>{" "}
          {extractedData?.candidate_name || "—"}
        </div>
        <div>
          <span className="font-medium text-zinc-700">Parsed Email:</span>{" "}
          {extractedData?.email || "—"}
        </div>
        <div>
          <span className="font-medium text-zinc-700">Parsed Phone:</span>{" "}
          {extractedData?.phone || "—"}
        </div>
        <div>
          <span className="font-medium text-zinc-700">Location:</span>{" "}
          {extractedData?.location || "—"}
        </div>
      </div>
    </div>
  );
}
