"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api, extractApiErrors } from "@/lib/api";
import { Application, ResumeAnalysis } from "@/types";
import { ResumeAnalysisPanel } from "@/components/analysis/ResumeAnalysisPanel";
import { ExtractedSkills } from "@/components/analysis/ExtractedSkills";
import { ExperienceSummary } from "@/components/analysis/ExperienceSummary";
import { EvaluationBreakdown } from "@/components/analysis/EvaluationBreakdown";
import { EvidenceViewer } from "@/components/analysis/EvidenceViewer";
import { RecruiterReviewPanel } from "@/components/analysis/RecruiterReviewPanel";

interface AnalysisPageProps {
  params: Promise<{ applicationId: string }>;
}

export default function ApplicationAnalysisPage({ params }: AnalysisPageProps) {
  const [applicationId, setApplicationId] = useState<string>("");
  const [application, setApplication] = useState<Application | null>(null);
  const [analyses, setAnalyses] = useState<ResumeAnalysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<ResumeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"evaluation" | "extracted" | "review">("evaluation");

  const loadData = useCallback(async (aid: string) => {
    try {
      const [appData, analysisList] = await Promise.all([
        api.get<Application>(`/api/v1/applications/${aid}/`),
        api.get<ResumeAnalysis[]>(`/api/v1/applications/${aid}/analysis/`),
      ]);
      setApplication(appData);
      setAnalyses(analysisList);
      if (analysisList.length > 0) {
        setSelectedAnalysis(analysisList[0]);
      }
    } catch {
      setError("Failed to load application analysis data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      const { applicationId: aid } = await params;
      setApplicationId(aid);
      if (!cancelled) {
        loadData(aid);
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, [params, loadData]);

  async function handleTriggerScreening() {
    if (!applicationId) return;
    setAnalyzing(true);
    setError(null);

    try {
      await api.post(`/api/v1/applications/${applicationId}/analyze/`, {});
      // Refresh analyses
      await loadData(applicationId);
    } catch (err) {
      setError(extractApiErrors(err));
    } finally {
      setAnalyzing(false);
    }
  }

  function handleAnalysisUpdated(updated: ResumeAnalysis) {
    setSelectedAnalysis(updated);
    setAnalyses((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  if (loading) {
    return <div className="py-20 text-center text-sm text-zinc-400">Loading AI screening data…</div>;
  }

  if (error && !application) {
    return (
      <div className="space-y-4">
        <Link href="/applications" className="text-xs text-zinc-500 hover:text-zinc-800">
          ← Back to applications
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      </div>
    );
  }

  const candidateName = application?.candidate?.full_name || application?.candidate_name || "Candidate";
  const jobTitle = application?.job?.title || application?.job_title || "Job Requisition";

  return (
    <div className="space-y-6">
      {/* Top breadcrumb */}
      <div className="flex items-center space-x-2 text-xs text-zinc-400">
        <Link href="/applications" className="hover:text-zinc-700">
          Applications
        </Link>
        <span>/</span>
        <Link href={`/applications/${applicationId}`} className="hover:text-zinc-700">
          {candidateName}
        </Link>
        <span>/</span>
        <span className="text-zinc-600 font-medium">AI Resume Screening</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">AI Resume Screening</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {candidateName} • Applied for <span className="font-medium text-zinc-800">{jobTitle}</span>
          </p>
        </div>

        <Link
          href={`/applications/${applicationId}`}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 self-start sm:self-auto"
        >
          View Application Overview →
        </Link>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Main Analysis Banner & Dial */}
      <ResumeAnalysisPanel
        analysis={selectedAnalysis}
        loading={analyzing}
        onAnalyzeClick={handleTriggerScreening}
      />

      {/* If analysis exists, display tabs */}
      {selectedAnalysis && (
        <div className="space-y-6">
          {/* Tabs bar */}
          <div className="flex space-x-2 border-b border-zinc-200 pb-px">
            <button
              onClick={() => setActiveTab("evaluation")}
              className={`border-b-2 px-4 py-2.5 text-xs font-bold transition-colors ${
                activeTab === "evaluation"
                  ? "border-zinc-900 text-zinc-900"
                  : "border-transparent text-zinc-500 hover:text-zinc-800"
              }`}
            >
              📊 Evaluation & Evidence Matrix
            </button>
            <button
              onClick={() => setActiveTab("extracted")}
              className={`border-b-2 px-4 py-2.5 text-xs font-bold transition-colors ${
                activeTab === "extracted"
                  ? "border-zinc-900 text-zinc-900"
                  : "border-transparent text-zinc-500 hover:text-zinc-800"
              }`}
            >
              📄 Structured Resume Profile
            </button>
            <button
              onClick={() => setActiveTab("review")}
              className={`border-b-2 px-4 py-2.5 text-xs font-bold transition-colors ${
                activeTab === "review"
                  ? "border-zinc-900 text-zinc-900"
                  : "border-transparent text-zinc-500 hover:text-zinc-800"
              }`}
            >
              ✍️ Recruiter Review & Overrides
            </button>
          </div>

          {/* Tab 1: Evaluation Matrix */}
          {activeTab === "evaluation" && (
            <div className="space-y-6">
              <EvaluationBreakdown assessment={selectedAnalysis.assessment} />
              <EvidenceViewer extractedData={selectedAnalysis.extracted_data} />
            </div>
          )}

          {/* Tab 2: Extracted Profile */}
          {activeTab === "extracted" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
              <div className="lg:col-span-2 space-y-6">
                <ExperienceSummary extractedData={selectedAnalysis.extracted_data} />
              </div>
              <div>
                <ExtractedSkills extractedData={selectedAnalysis.extracted_data} />
              </div>
            </div>
          )}

          {/* Tab 3: Recruiter Review */}
          {activeTab === "review" && (
            <RecruiterReviewPanel
              applicationId={applicationId}
              analysis={selectedAnalysis}
              onAnalysisUpdated={handleAnalysisUpdated}
            />
          )}
        </div>
      )}
    </div>
  );
}
