"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BrainCircuit, CheckCircle2, Eye, ShieldAlert } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

interface InvestigationDetail {
  case_id: string;
  tx_id: string;
  risk_score: number;
  risk_classification: string;
  status: string;
  observed_evidence: Array<{ category: string; fact: string; metric: string; source: string }>;
  model_inference: {
    xgboost_probability: number;
    isolation_forest_anomaly_score: number;
    combined_risk_score: number;
    risk_classification: string;
    narrative: string;
    provenance_notice: string;
  };
  contributing_features: Array<{
    feature: string;
    value: number;
    shap_value: number;
    impact_pct: number;
    direction: string;
  }>;
  recommended_actions: Array<{ priority: string; action: string; rationale: string }>;
  analyst_notes: string | null;
  transaction: {
    tx_id: string;
    card_last4: string;
    merchant: string;
    merchant_category: string;
    amount: number;
    country: string;
    channel: string;
    device_id: string;
    ip_subnet: string;
    velocity_1h: number;
    timestamp: string | null;
  } | null;
}

function InvestigationContent() {
  const searchParams = useSearchParams();
  const initialTx = searchParams.get("tx") || "";

  const [txIdInput, setTxIdInput] = useState(initialTx);
  const [dossier, setDossier] = useState<InvestigationDetail | null>(null);
  const [status, setStatus] = useState("open");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  const runInvestigation = async (targetTx: string) => {
    if (!targetTx) return;
    setLoading(true);
    setSavedMsg(null);
    try {
      const res = await apiFetch<InvestigationDetail>(
        `/api/investigations/${encodeURIComponent(targetTx)}`,
        { method: "POST" }
      );
      setDossier(res);
      setStatus(res.status);
      setNotes(res.analyst_notes || "");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialTx) {
      runInvestigation(initialTx);
    } else {
      // Load latest existing investigation by default
      apiFetch<{ items: InvestigationDetail[] }>("/api/investigations?page=1&page_size=1").then(
        (res) => {
          if (res.items.length > 0) {
            const first = res.items[0];
            setDossier(first);
            setTxIdInput(first.tx_id);
            setStatus(first.status);
            setNotes(first.analyst_notes || "");
          }
        }
      );
    }
  }, [initialTx]);

  const handleSaveCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dossier) return;
    const updated = await apiFetch<InvestigationDetail>(
      `/api/investigations/${encodeURIComponent(dossier.case_id)}`,
      {
        method: "PATCH",
        body: JSON.stringify({ status, analyst_notes: notes }),
      }
    );
    setDossier(updated);
    setSavedMsg("Case decision saved.");
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
            AI Investigation Workspace
          </h1>
          <p className="text-sm text-on-surface-variant">
            Explainable transaction triage separating observed evidence from model-generated inference.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={txIdInput}
            onChange={(e) => setTxIdInput(e.target.value)}
            placeholder="Enter TX ID (e.g. TX-100001)"
            className="rounded bg-surface-container border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
          />
          <button
            type="button"
            onClick={() => runInvestigation(txIdInput)}
            disabled={loading || !txIdInput}
            className="px-4 py-2 rounded bg-primary text-on-primary text-sm font-semibold disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Investigate"}
          </button>
        </div>
      </header>

      {dossier ? (
        <div className="flex flex-col gap-6">
          {/* Case Banner */}
          <section className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs px-2.5 py-1 rounded bg-surface-container-high border border-outline-variant text-on-surface-variant">
                  {dossier.case_id}
                </span>
                <span className="font-mono text-lg font-semibold text-on-surface">
                  {dossier.tx_id}
                </span>
                <RiskBadge level={dossier.risk_classification} />
              </div>
              {dossier.transaction && (
                <p className="text-sm text-on-surface-variant">
                  {dossier.transaction.merchant} ({dossier.transaction.merchant_category}) • Card{" "}
                  <span className="font-mono">•••• {dossier.transaction.card_last4}</span> •{" "}
                  <span className="font-mono font-semibold text-on-surface">
                    ${dossier.transaction.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>{" "}
                  • {dossier.transaction.country}
                </p>
              )}
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-xs text-on-surface-variant">Composite Risk</div>
                <div className="font-mono text-3xl font-semibold text-primary tabular-nums">
                  {dossier.risk_score.toFixed(1)}
                  <span className="text-sm text-on-surface-variant"> / 100</span>
                </div>
              </div>
            </div>
          </section>

          {/* Observed Evidence vs Model Inference */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Observed Evidence */}
            <div className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-info" />
                  <h2 className="text-base font-semibold text-on-surface">
                    Observed Evidence
                  </h2>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-info-container text-on-info-container">
                  FACTUAL TELEMETRY
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {dossier.observed_evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded bg-surface-container-low border border-outline-variant flex items-start justify-between gap-3"
                  >
                    <div>
                      <div className="text-xs font-semibold text-on-surface">{ev.category}</div>
                      <p className="text-xs text-on-surface-variant mt-0.5">{ev.fact}</p>
                    </div>
                    <span className="font-mono text-xs text-info shrink-0">{ev.metric}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Model Inference */}
            <div className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-primary" />
                  <h2 className="text-base font-semibold text-on-surface">
                    Model Inference
                  </h2>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-primary-container text-on-primary-container">
                  ML PROBABILISTIC
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded bg-surface-container-low border border-outline-variant">
                  <div className="text-xs text-on-surface-variant">XGBoost Fraud Prob</div>
                  <div className="font-mono text-xl font-semibold text-on-surface mt-1">
                    {(dossier.model_inference.xgboost_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-3.5 rounded bg-surface-container-low border border-outline-variant">
                  <div className="text-xs text-on-surface-variant">Isolation Forest Anomaly</div>
                  <div className="font-mono text-xl font-semibold text-on-surface mt-1">
                    {(dossier.model_inference.isolation_forest_anomaly_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <p className="text-sm text-on-surface leading-relaxed">
                {dossier.model_inference.narrative}
              </p>
              <p className="text-xs text-on-surface-variant border-t border-outline-variant pt-3">
                {dossier.model_inference.provenance_notice}
              </p>
            </div>
          </section>

          {/* SHAP Contributions + Recommended Actions */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
              <div>
                <h2 className="text-base font-semibold text-on-surface">
                  SHAP Feature Attributions
                </h2>
                <p className="text-xs text-on-surface-variant">
                  Per-feature log-odds contribution pushing risk up (red) or down (green)
                </p>
              </div>
              <div className="h-[260px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={dossier.contributing_features}
                    layout="vertical"
                    margin={{ left: 30 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#2F3130" horizontal={false} />
                    <XAxis type="number" stroke="#90918F" fontSize={11} />
                    <YAxis
                      type="category"
                      dataKey="feature"
                      stroke="#90918F"
                      fontSize={11}
                      width={130}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1A1C1B",
                        borderColor: "#2F3130",
                        borderRadius: "10px",
                        color: "#F1F1EE",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="shap_value" name="SHAP Value" radius={[0, 4, 4, 0]}>
                      {dossier.contributing_features.map((entry, index) => (
                        <Cell
                          key={index}
                          fill={entry.shap_value >= 0 ? "#FF5A5F" : "#3FB950"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="lg:col-span-5 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col justify-between gap-4">
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-warning" />
                  <h2 className="text-base font-semibold text-on-surface">
                    Recommended Analyst Actions
                  </h2>
                </div>
                {dossier.recommended_actions.map((act, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded bg-surface-container-low border border-outline-variant"
                  >
                    <div className="text-xs font-semibold text-on-surface">{act.action}</div>
                    <div className="text-xs text-on-surface-variant mt-0.5">{act.rationale}</div>
                  </div>
                ))}
              </div>

              <form onSubmit={handleSaveCase} className="pt-4 border-t border-outline-variant flex flex-col gap-3">
                <div className="flex items-center justify-between gap-2">
                  <label className="text-xs font-medium text-on-surface-variant">
                    Case Disposition
                  </label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="rounded bg-surface-container-low border border-outline-variant px-2.5 py-1.5 text-xs text-on-surface"
                  >
                    <option value="open">Open</option>
                    <option value="escalated">Escalated</option>
                    <option value="resolved_fraud">Resolved: Confirmed Fraud</option>
                    <option value="resolved_legit">Resolved: Legitimate</option>
                  </select>
                </div>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Analyst investigation notes..."
                  className="w-full rounded bg-surface-container-low border border-outline-variant p-2.5 text-xs text-on-surface"
                />
                <div className="flex items-center justify-between">
                  {savedMsg ? (
                    <span className="inline-flex items-center gap-1 text-xs text-success">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {savedMsg}
                    </span>
                  ) : (
                    <span />
                  )}
                  <button
                    type="submit"
                    className="px-4 py-2 rounded bg-primary text-on-primary text-xs font-semibold"
                  >
                    Save Disposition
                  </button>
                </div>
              </form>
            </div>
          </section>
        </div>
      ) : (
        <div className="bg-surface-container border border-outline-variant rounded-lg p-12 text-center text-on-surface-variant">
          Enter a Transaction ID above to launch an explainable AI investigation.
        </div>
      )}
    </div>
  );
}

export default function InvestigationsPage() {
  return (
    <Suspense fallback={<div className="text-sm text-on-surface-variant">Loading workspace...</div>}>
      <InvestigationContent />
    </Suspense>
  );
}
