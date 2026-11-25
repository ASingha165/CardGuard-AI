"use client";

import React, { useEffect, useState } from "react";
import { Download, FileText, Plus } from "lucide-react";
import { apiFetch, getApiUrl } from "@/lib/api";

interface ReportItem {
  report_id: string;
  title: string;
  report_type: string;
  format: string;
  content?: string;
  created_at: string | null;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [reportType, setReportType] = useState("executive_summary");
  const [format, setFormat] = useState("markdown");
  const [preview, setPreview] = useState<ReportItem | null>(null);
  const [creating, setCreating] = useState(false);

  const loadReports = async () => {
    const res = await apiFetch<{ items: ReportItem[] }>("/api/reports");
    setReports(res.items);
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const created = await apiFetch<ReportItem>("/api/reports", {
        method: "POST",
        body: JSON.stringify({ report_type: reportType, format }),
      });
      setPreview(created);
      await loadReports();
    } finally {
      setCreating(false);
    }
  };

  const openReport = async (id: string) => {
    const rpt = await apiFetch<ReportItem>(`/api/reports/${id}`);
    setPreview(rpt);
  };

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
          Reports & Exports
        </h1>
        <p className="text-sm text-on-surface-variant">
          Generate audit-ready fraud summaries, case dossiers, and model evaluation exports in Markdown, CSV, or JSON.
        </p>
      </header>

      <form
        onSubmit={handleGenerate}
        className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-wrap items-end gap-4"
      >
        <div>
          <label className="block text-xs text-on-surface-variant mb-1">Report Type</label>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm text-on-surface"
          >
            <option value="executive_summary">Executive Fraud Summary</option>
            <option value="case_dossier">Investigation Case Dossier</option>
            <option value="model_audit">ML Model Evaluation Audit</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-on-surface-variant mb-1">Export Format</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm text-on-surface"
          >
            <option value="markdown">Markdown (.md)</option>
            <option value="csv">CSV (.csv)</option>
            <option value="json">JSON (.json)</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-on-primary text-xs font-semibold"
        >
          <Plus className="w-4 h-4" />
          {creating ? "Generating..." : "Generate Report"}
        </button>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-surface-container border border-outline-variant rounded-lg divide-y divide-outline-variant">
          {reports.length === 0 ? (
            <div className="p-6 text-sm text-on-surface-variant">
              No reports generated yet. Create one above.
            </div>
          ) : (
            reports.map((r) => (
              <div
                key={r.report_id}
                onClick={() => openReport(r.report_id)}
                className="p-4 flex items-center justify-between gap-3 cursor-pointer hover:bg-surface-container-high/50"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-primary shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-on-surface">{r.title}</div>
                    <div className="font-mono text-xs text-on-surface-variant">{r.report_id}</div>
                  </div>
                </div>
                <a
                  href={getApiUrl(`/api/reports/${r.report_id}/download`)}
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-surface-container-high border border-outline-variant text-xs text-primary"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </a>
              </div>
            ))
          )}
        </div>

        <div className="lg:col-span-7 bg-surface-container border border-outline-variant rounded-lg p-6">
          <h2 className="text-base font-semibold text-on-surface mb-3">Report Preview</h2>
          {preview ? (
            <pre className="bg-surface-container-lowest border border-outline-variant rounded p-4 text-xs font-mono text-on-surface overflow-x-auto max-h-[460px] whitespace-pre-wrap">
              {preview.content}
            </pre>
          ) : (
            <p className="text-sm text-on-surface-variant">
              Select or generate a report to inspect its contents.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
