"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, ArrowUpRight, ShieldAlert, TrendingUp } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

interface DashboardData {
  dataset: {
    id: number;
    name: string;
    source_type: string;
    row_count: number;
    fraud_rate: number;
  } | null;
  kpis: {
    transactions_monitored?: number;
    flagged_high_risk?: number;
    critical_alerts?: number;
    exposure_at_risk_usd?: number;
    total_volume_usd?: number;
    open_investigations?: number;
    xgb_pr_auc?: number | null;
    xgb_f2?: number | null;
  };
  timeseries: Array<{ date: string; total: number; flagged: number; volume_usd: number }>;
  risk_distribution: Array<{ level: string; count: number }>;
  category_breakdown: Array<{ category: string; count: number; flagged: number; avg_risk: number }>;
  top_flagged: Array<{
    tx_id: string;
    timestamp: string | null;
    card_last4: string;
    merchant: string;
    merchant_category: string;
    amount: number;
    country: string;
    risk_score: number;
    risk_level: string;
    analyst_status: string;
  }>;
}

export default function ExecutiveDashboardPage() {
  const [rangeDays, setRangeDays] = useState<number>(30);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async (days: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<DashboardData>(`/api/dashboard?range_days=${days}`);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard(rangeDays);
  }, [rangeDays]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight tracking-tight text-on-surface">
            Executive Dashboard
          </h1>
          <p className="text-sm text-on-surface-variant">
            Institutional fraud posture, model detection velocity, and high-priority anomalies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            role="group"
            aria-label="Timeframe"
            className="inline-flex rounded bg-surface-container border border-outline-variant p-1"
          >
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setRangeDays(d)}
                className={`px-3 py-1.5 rounded-sm text-[13px] font-medium transition-colors ${
                  rangeDays === d
                    ? "bg-primary text-on-primary"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {d}D
              </button>
            ))}
          </div>
        </div>
      </header>

      {error && (
        <div className="rounded-lg bg-danger-container border border-danger/30 p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-danger" />
            <div>
              <p className="text-sm font-semibold text-on-danger-container">
                Telemetry stream interrupted
              </p>
              <p className="text-xs text-on-danger-container/80">{error}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => loadDashboard(rangeDays)}
            className="px-3.5 py-2 rounded bg-danger text-on-danger text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-32 rounded-lg bg-surface-container border border-outline-variant p-6 animate-pulse"
            />
          ))}
        </div>
      ) : data ? (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="flex flex-col gap-6"
        >
          {/* KPI Row */}
          <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <article className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <span className="text-[13px] font-medium text-on-surface-variant">
                  Transactions Monitored
                </span>
                <TrendingUp className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="font-mono text-2xl font-semibold tabular-nums text-on-surface">
                  {(data.kpis.transactions_monitored ?? 0).toLocaleString()}
                </p>
                <p className="text-xs text-on-surface-variant mt-1">
                  Active dataset: {data.dataset?.name ?? "None"}
                </p>
              </div>
            </article>

            <article className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <span className="text-[13px] font-medium text-on-surface-variant">
                  High & Critical Alerts
                </span>
                <ShieldAlert className="w-4 h-4 text-danger" />
              </div>
              <div>
                <p className="font-mono text-2xl font-semibold tabular-nums text-on-surface">
                  {(data.kpis.flagged_high_risk ?? 0).toLocaleString()}
                </p>
                <p className="text-xs text-danger mt-1 font-mono tabular-nums">
                  {data.kpis.critical_alerts ?? 0} critical (≥ 90 risk)
                </p>
              </div>
            </article>

            <article className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <span className="text-[13px] font-medium text-on-surface-variant">
                  Exposure at Risk
                </span>
                <AlertTriangle className="w-4 h-4 text-warning" />
              </div>
              <div>
                <p className="font-mono text-2xl font-semibold tabular-nums text-on-surface">
                  ${(data.kpis.exposure_at_risk_usd ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-on-surface-variant mt-1 font-mono tabular-nums">
                  of ${(data.kpis.total_volume_usd ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} total
                </p>
              </div>
            </article>

            <article className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <span className="text-[13px] font-medium text-on-surface-variant">
                  XGBoost PR-AUC / F2
                </span>
                <span className="px-2 py-0.5 rounded-full bg-primary-container text-primary text-[11px] font-mono">
                  ACTIVE
                </span>
              </div>
              <div>
                <p className="font-mono text-2xl font-semibold tabular-nums text-primary">
                  {data.kpis.xgb_pr_auc != null ? `${(data.kpis.xgb_pr_auc * 100).toFixed(1)}%` : "N/A"}
                </p>
                <p className="text-xs text-on-surface-variant mt-1 font-mono tabular-nums">
                  F2-Score: {data.kpis.xgb_f2 != null ? data.kpis.xgb_f2.toFixed(3) : "N/A"} • {data.kpis.open_investigations ?? 0} open cases
                </p>
              </div>
            </article>
          </section>

          {/* Charts Row */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-on-surface">
                    Detection Velocity Over Time
                  </h2>
                  <p className="text-xs text-on-surface-variant">
                    Daily monitored transactions vs. high-risk flagged anomalies
                  </p>
                </div>
              </div>
              <div className="h-[260px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.timeseries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2F3130" />
                    <XAxis dataKey="date" stroke="#90918F" fontSize={11} tickFormatter={(v) => String(v).slice(5)} />
                    <YAxis stroke="#90918F" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1A1C1B",
                        borderColor: "#2F3130",
                        borderRadius: "10px",
                        color: "#F1F1EE",
                        fontSize: "12px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="total"
                      name="Total TX"
                      stroke="#58A6FF"
                      fill="#00315C"
                      fillOpacity={0.45}
                    />
                    <Area
                      type="monotone"
                      dataKey="flagged"
                      name="Flagged"
                      stroke="#C8F169"
                      fill="#263500"
                      fillOpacity={0.75}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="lg:col-span-4 bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-4">
              <div>
                <h2 className="text-base font-semibold text-on-surface">
                  Category Risk Exposure
                </h2>
                <p className="text-xs text-on-surface-variant">
                  Flagged anomalies by merchant category
                </p>
              </div>
              <div className="h-[260px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.category_breakdown.slice(0, 6)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#2F3130" horizontal={false} />
                    <XAxis type="number" stroke="#90918F" fontSize={11} />
                    <YAxis
                      type="category"
                      dataKey="category"
                      stroke="#90918F"
                      fontSize={11}
                      width={96}
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
                    <Bar dataKey="flagged" name="Flagged TX" fill="#C8F169" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          {/* Top Flagged Transactions */}
          <section className="bg-surface-container border border-outline-variant rounded-lg overflow-hidden">
            <div className="p-6 border-b border-outline-variant flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-on-surface">
                  Priority Flagged Transactions
                </h2>
                <p className="text-xs text-on-surface-variant">
                  Highest composite risk scores requiring analyst triage
                </p>
              </div>
              <Link
                href="/transactions"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
              >
                View all transactions
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-outline-variant bg-surface-container-low text-[11px] uppercase tracking-wider text-on-surface-variant">
                    <th className="py-3 px-4 font-medium">TX ID</th>
                    <th className="py-3 px-4 font-medium">Card</th>
                    <th className="py-3 px-4 font-medium">Merchant</th>
                    <th className="py-3 px-4 font-medium text-right">Amount</th>
                    <th className="py-3 px-4 font-medium text-right">Risk Score</th>
                    <th className="py-3 px-4 font-medium">Level</th>
                    <th className="py-3 px-4 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant text-[13px]">
                  {data.top_flagged.map((tx) => (
                    <tr
                      key={tx.tx_id}
                      className="hover:bg-surface-container-high/60 transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-on-surface">{tx.tx_id}</td>
                      <td className="py-3 px-4 font-mono text-on-surface-variant">
                        •••• {tx.card_last4}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-on-surface">{tx.merchant}</div>
                        <div className="text-xs text-on-surface-variant">
                          {tx.merchant_category} • {tx.country}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono tabular-nums text-right text-on-surface">
                        ${tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 font-mono tabular-nums text-right font-semibold text-on-surface">
                        {tx.risk_score.toFixed(1)}
                      </td>
                      <td className="py-3 px-4">
                        <RiskBadge level={tx.risk_level} />
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/investigations?tx=${encodeURIComponent(tx.tx_id)}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-surface-container-high border border-outline-variant text-xs font-medium text-primary hover:border-primary/40"
                        >
                          Investigate
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </motion.div>
      ) : null}
    </div>
  );
}
