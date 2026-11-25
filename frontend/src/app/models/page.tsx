"use client";

import React, { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Cpu, Play } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface ModelRun {
  id: number;
  model_name: string;
  selected_threshold: number;
  hyperparameters: Record<string, unknown>;
  metrics: {
    precision?: number;
    recall?: number;
    f1?: number;
    f2?: number;
    pr_auc?: number;
    roc_auc?: number;
    confusion_matrix?: { tn: number; fp: number; fn: number; tp: number };
    pr_curve?: Array<{ recall: number; precision: number }>;
    roc_curve?: Array<{ fpr: number; tpr: number }>;
    smote_applied_to_train_only?: boolean;
    train_samples_before_smote?: number;
    train_samples_after_smote?: number;
    val_samples?: number;
    test_samples?: number;
  };
  feature_importance: Array<{ feature: string; importance: number }>;
}

export default function ModelIntelligencePage() {
  const [models, setModels] = useState<{
    isolation_forest: ModelRun | null;
    xgboost: ModelRun | null;
  }>({ isolation_forest: null, xgboost: null });
  const [contamination, setContamination] = useState("0.035");
  const [thresholdOverride, setThresholdOverride] = useState("");
  const [training, setTraining] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadModels = async () => {
    const res = await apiFetch<{
      isolation_forest: ModelRun | null;
      xgboost: ModelRun | null;
    }>("/api/models/active");
    setModels(res);
  };

  useEffect(() => {
    loadModels();
  }, []);

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    setTraining(true);
    setStatusMsg(null);
    try {
      await apiFetch("/api/models/train", {
        method: "POST",
        body: JSON.stringify({
          model_name: "both",
          contamination: Number(contamination),
          threshold_override: thresholdOverride ? Number(thresholdOverride) : null,
        }),
      });
      await loadModels();
      setStatusMsg("Models retrained and evaluated on held-out test split.");
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : "Training failed");
    } finally {
      setTraining(false);
    }
  };

  const xgb = models.xgboost;
  const iso = models.isolation_forest;
  const cm = xgb?.metrics.confusion_matrix;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
            Model Intelligence
          </h1>
          <p className="text-sm text-on-surface-variant">
            Isolation Forest anomaly detection and XGBoost classification (SMOTE train-only, validation threshold tuning).
          </p>
        </div>
      </header>

      {/* Training Controls */}
      <form
        onSubmit={handleTrain}
        className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-wrap items-end gap-4"
      >
        <div>
          <label className="block text-xs text-on-surface-variant mb-1">
            Isolation Forest Contamination
          </label>
          <input
            type="number"
            step="0.005"
            min="0.005"
            max="0.25"
            value={contamination}
            onChange={(e) => setContamination(e.target.value)}
            className="rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface w-44"
          />
        </div>
        <div>
          <label className="block text-xs text-on-surface-variant mb-1">
            XGBoost Threshold Override (optional)
          </label>
          <input
            type="number"
            step="0.05"
            min="0.05"
            max="0.95"
            placeholder="Auto (Val F2)"
            value={thresholdOverride}
            onChange={(e) => setThresholdOverride(e.target.value)}
            className="rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface w-44"
          />
        </div>
        <button
          type="submit"
          disabled={training}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-on-primary text-xs font-semibold disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5" />
          {training ? "Training..." : "Retrain & Evaluate"}
        </button>
        {statusMsg && <span className="text-xs text-primary">{statusMsg}</span>}
      </form>

      {/* Model Comparison Cards */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[
          { title: "XGBoost Classifier (Supervised)", model: xgb, badge: "SMOTE TRAIN-ONLY" },
          { title: "Isolation Forest (Unsupervised)", model: iso, badge: "ANOMALY SCORING" },
        ].map(({ title, model, badge }) => (
          <div
            key={title}
            className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-primary" />
                <h2 className="text-base font-semibold text-on-surface">{title}</h2>
              </div>
              <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-primary-container text-primary">
                {badge}
              </span>
            </div>

            {model ? (
              <>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    ["Precision", model.metrics.precision],
                    ["Recall", model.metrics.recall],
                    ["F1-Score", model.metrics.f1],
                    ["F2-Score", model.metrics.f2],
                    ["PR-AUC", model.metrics.pr_auc],
                    ["ROC-AUC", model.metrics.roc_auc],
                  ].map(([k, v]) => (
                    <div
                      key={String(k)}
                      className="p-3 rounded bg-surface-container-low border border-outline-variant"
                    >
                      <div className="text-[11px] text-on-surface-variant">{k}</div>
                      <div className="font-mono text-lg font-semibold text-on-surface mt-0.5">
                        {v != null ? Number(v).toFixed(3) : "N/A"}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-on-surface-variant font-mono">
                  Selected Threshold: {model.selected_threshold}
                  {model.metrics.smote_applied_to_train_only
                    ? ` • Train: ${model.metrics.train_samples_before_smote}→${model.metrics.train_samples_after_smote} (SMOTE) • Val: ${model.metrics.val_samples} • Test: ${model.metrics.test_samples}`
                    : ""}
                </div>
              </>
            ) : (
              <p className="text-sm text-on-surface-variant">No active model run.</p>
            )}
          </div>
        ))}
      </section>

      {/* Confusion Matrix + Curves */}
      {xgb && (
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
            <h2 className="text-base font-semibold text-on-surface">
              Held-Out Test Confusion Matrix
            </h2>
            {cm && (
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-4 rounded bg-success-container/40 border border-success/30">
                  <div className="text-[11px] text-on-surface-variant">True Negative</div>
                  <div className="font-mono text-2xl font-semibold text-on-surface mt-1">{cm.tn}</div>
                </div>
                <div className="p-4 rounded bg-warning-container/40 border border-warning/30">
                  <div className="text-[11px] text-on-surface-variant">False Positive</div>
                  <div className="font-mono text-2xl font-semibold text-warning mt-1">{cm.fp}</div>
                </div>
                <div className="p-4 rounded bg-danger-container/40 border border-danger/30">
                  <div className="text-[11px] text-on-surface-variant">False Negative</div>
                  <div className="font-mono text-2xl font-semibold text-danger mt-1">{cm.fn}</div>
                </div>
                <div className="p-4 rounded bg-primary-container border border-primary/30">
                  <div className="text-[11px] text-on-surface-variant">True Positive</div>
                  <div className="font-mono text-2xl font-semibold text-primary mt-1">{cm.tp}</div>
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-4 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
            <h2 className="text-base font-semibold text-on-surface">Precision-Recall Curve</h2>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={xgb.metrics.pr_curve || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2F3130" />
                  <XAxis dataKey="recall" stroke="#90918F" fontSize={11} />
                  <YAxis stroke="#90918F" fontSize={11} domain={[0, 1]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1A1C1B",
                      borderColor: "#2F3130",
                      borderRadius: "10px",
                      fontSize: "12px",
                    }}
                  />
                  <Line type="monotone" dataKey="precision" stroke="#C8F169" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="lg:col-span-4 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
            <h2 className="text-base font-semibold text-on-surface">Feature Importance</h2>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={xgb.feature_importance} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2F3130" horizontal={false} />
                  <XAxis type="number" stroke="#90918F" fontSize={11} />
                  <YAxis type="category" dataKey="feature" stroke="#90918F" fontSize={10} width={110} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1A1C1B",
                      borderColor: "#2F3130",
                      borderRadius: "10px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="importance" fill="#58A6FF" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
