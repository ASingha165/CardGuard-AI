"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, Database, Sparkles, Upload } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface DatasetItem {
  id: number;
  name: string;
  source_type: string;
  row_count: number;
  fraud_count: number;
  fraud_rate: number;
  is_active: boolean;
  validation_summary: Record<string, unknown>;
  created_at: string | null;
}

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [sampleRows, setSampleRows] = useState<Array<Record<string, unknown>>>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDatasets = async () => {
    const res = await apiFetch<{ items: DatasetItem[] }>("/api/datasets");
    setDatasets(res.items);
    const active = res.items.find((d) => d.is_active) || res.items[0];
    if (active) {
      inspectDataset(active.id);
    }
  };

  const inspectDataset = async (id: number) => {
    setSelectedId(id);
    const res = await apiFetch<{ sample_rows: Array<Record<string, unknown>> }>(
      `/api/datasets/${id}/inspect?limit=10`
    );
    setSampleRows(res.sample_rows);
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiFetch<{ name: string; row_count: number }>("/api/datasets/upload", {
        method: "POST",
        body: formData,
      });
      setMessage(`Uploaded and scored ${res.name} (${res.row_count} rows). Raw PANs stripped/tokenized.`);
      await loadDatasets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateSynthetic = async () => {
    setUploading(true);
    setError(null);
    try {
      await apiFetch("/api/datasets/synthetic", {
        method: "POST",
        body: JSON.stringify({ n_rows: 1200, seed: Math.floor(Math.random() * 1000) + 1 }),
      });
      setMessage("Generated fresh synthetic dataset and retrained models.");
      await loadDatasets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (id: number) => {
    await apiFetch(`/api/datasets/${id}/activate`, { method: "POST" });
    await loadDatasets();
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
            Dataset Laboratory
          </h1>
          <p className="text-sm text-on-surface-variant">
            Upload CSV transaction batches (max 10 MB, auto-tokenized PAN protection) or generate synthetic telemetry.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-on-primary text-xs font-semibold">
            <Upload className="w-4 h-4" />
            {uploading ? "Processing..." : "Upload CSV"}
            <input type="file" accept=".csv" onChange={handleUpload} className="hidden" />
          </label>
          <button
            type="button"
            onClick={handleGenerateSynthetic}
            disabled={uploading}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-surface-container-high border border-outline-variant text-xs font-medium text-on-surface"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            Generate Synthetic
          </button>
        </div>
      </header>

      {message && (
        <div className="rounded-lg bg-success-container border border-success/30 p-3.5 text-xs text-on-success-container flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          {message}
        </div>
      )}
      {error && (
        <div className="rounded-lg bg-danger-container border border-danger/30 p-3.5 text-xs text-on-danger-container">
          {error}
        </div>
      )}

      {/* Dataset List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {datasets.map((ds) => (
          <div
            key={ds.id}
            onClick={() => inspectDataset(ds.id)}
            className={`cursor-pointer rounded-lg p-5 border transition-colors ${
              selectedId === ds.id
                ? "bg-surface-container-high border-primary/50"
                : "bg-surface-container border-outline-variant hover:border-outline"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-primary" />
                <span className="font-medium text-sm text-on-surface">{ds.name}</span>
              </div>
              {ds.is_active ? (
                <span className="px-2 py-0.5 rounded-full bg-primary-container text-primary text-[10px] font-mono">
                  ACTIVE
                </span>
              ) : (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleActivate(ds.id);
                  }}
                  className="px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant text-[10px] text-on-surface-variant hover:text-on-surface"
                >
                  Activate
                </button>
              )}
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 font-mono text-xs">
              <div>
                <span className="text-on-surface-variant block text-[10px]">Rows</span>
                {ds.row_count.toLocaleString()}
              </div>
              <div>
                <span className="text-on-surface-variant block text-[10px]">Fraud</span>
                {ds.fraud_count}
              </div>
              <div>
                <span className="text-on-surface-variant block text-[10px]">Source</span>
                {ds.source_type}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sample Inspection Table */}
      <section className="bg-surface-container border border-outline-variant rounded-lg overflow-hidden">
        <div className="p-5 border-b border-outline-variant">
          <h2 className="text-base font-semibold text-on-surface">
            Dataset Sample Inspection (Top 10 by Risk)
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low text-on-surface-variant uppercase">
                <th className="py-2.5 px-4">TX ID</th>
                <th className="py-2.5 px-4">Card</th>
                <th className="py-2.5 px-4">Merchant</th>
                <th className="py-2.5 px-4 text-right">Amount</th>
                <th className="py-2.5 px-4 text-right">Velocity</th>
                <th className="py-2.5 px-4 text-right">Risk Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant font-mono">
              {sampleRows.map((r, i) => (
                <tr key={i} className="hover:bg-surface-container-high/40">
                  <td className="py-2.5 px-4">{String(r.tx_id)}</td>
                  <td className="py-2.5 px-4">•••• {String(r.card_last4)}</td>
                  <td className="py-2.5 px-4 font-sans">{String(r.merchant)}</td>
                  <td className="py-2.5 px-4 text-right">${Number(r.amount).toFixed(2)}</td>
                  <td className="py-2.5 px-4 text-right">{String(r.velocity_1h)}</td>
                  <td className="py-2.5 px-4 text-right text-primary">{Number(r.risk_score).toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
