"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Search, SlidersHorizontal, Zap } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

interface TransactionRow {
  tx_id: string;
  timestamp: string | null;
  card_last4: string;
  merchant: string;
  merchant_category: string;
  amount: number;
  country: string;
  channel: string;
  device_id: string;
  ip_subnet: string;
  velocity_1h: number;
  xgb_probability: number | null;
  iforest_score: number | null;
  risk_score: number;
  risk_level: string;
  analyst_status: string;
}

export default function TransactionsPage() {
  const [items, setItems] = useState<TransactionRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [q, setQ] = useState("");
  const [riskLevel, setRiskLevel] = useState("all");
  const [analystStatus, setAnalystStatus] = useState("all");
  const [loading, setLoading] = useState(true);

  // Live Scorer Modal
  const [scorerOpen, setScorerOpen] = useState(false);
  const [scoreAmount, setScoreAmount] = useState("2850");
  const [scoreMerchant, setScoreMerchant] = useState("BitVault Exchange");
  const [scoreVelocity, setScoreVelocity] = useState("5");
  const [scoreDistance, setScoreDistance] = useState("2400");
  const [scoreIntl, setScoreIntl] = useState("1");
  const [scoreResult, setScoreResult] = useState<{
    tx_id: string;
    risk_score: number;
    risk_level: string;
    xgb_probability: number;
    iforest_score: number;
  } | null>(null);

  const loadTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "15",
        risk_level: riskLevel,
        analyst_status: analystStatus,
        sort_by: "risk_score",
        sort_dir: "desc",
      });
      if (q.trim()) params.set("q", q.trim());
      const res = await apiFetch<{
        items: TransactionRow[];
        total: number;
        total_pages: number;
      }>(`/api/transactions?${params.toString()}`);
      setItems(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } finally {
      setLoading(false);
    }
  }, [page, riskLevel, analystStatus, q]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  const handleStatusChange = async (txId: string, status: string) => {
    await apiFetch(`/api/transactions/${txId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ analyst_status: status }),
    });
    loadTransactions();
  };

  const handleScoreSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch<{
      tx_id: string;
      risk_score: number;
      risk_level: string;
      xgb_probability: number;
      iforest_score: number;
    }>("/api/transactions/score", {
      method: "POST",
      body: JSON.stringify({
        amount: Number(scoreAmount),
        merchant: scoreMerchant,
        merchant_category: "crypto_exchange",
        country: scoreIntl === "1" ? "NG" : "US",
        velocity_1h: Number(scoreVelocity),
        distance_from_home_km: Number(scoreDistance),
        amount_zscore: Number(scoreAmount) > 1000 ? 3.4 : 0.3,
        is_international: Number(scoreIntl),
        hour_of_day: 2,
        merchant_risk_index: 0.62,
        persist: true,
      }),
    });
    setScoreResult(res);
    loadTransactions();
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
            Transaction Intelligence
          </h1>
          <p className="text-sm text-on-surface-variant">
            Search, filter, score, and triage monitored credit-card transactions.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setScorerOpen((v) => !v)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-on-primary text-[13px] font-semibold hover:opacity-90 transition-opacity"
        >
          <Zap className="w-4 h-4" />
          Score Live Transaction
        </button>
      </header>

      {scorerOpen && (
        <form
          onSubmit={handleScoreSubmit}
          className="bg-surface-container border border-primary/30 rounded-lg p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 items-end"
        >
          <div>
            <label className="block text-xs text-on-surface-variant mb-1">Amount (USD)</label>
            <input
              type="number"
              step="0.01"
              value={scoreAmount}
              onChange={(e) => setScoreAmount(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
              required
            />
          </div>
          <div className="lg:col-span-2">
            <label className="block text-xs text-on-surface-variant mb-1">Merchant</label>
            <input
              type="text"
              value={scoreMerchant}
              onChange={(e) => setScoreMerchant(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm text-on-surface"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-on-surface-variant mb-1">1h Velocity</label>
            <input
              type="number"
              value={scoreVelocity}
              onChange={(e) => setScoreVelocity(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
            />
          </div>
          <div>
            <label className="block text-xs text-on-surface-variant mb-1">Distance (km)</label>
            <input
              type="number"
              value={scoreDistance}
              onChange={(e) => setScoreDistance(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={scoreIntl}
              onChange={(e) => setScoreIntl(e.target.value)}
              className="rounded bg-surface-container-low border border-outline-variant px-2 py-2 text-sm text-on-surface"
            >
              <option value="1">Intl</option>
              <option value="0">Domestic</option>
            </select>
            <button
              type="submit"
              className="flex-1 px-4 py-2 rounded bg-primary text-on-primary text-sm font-semibold"
            >
              Score
            </button>
          </div>
          {scoreResult && (
            <div className="sm:col-span-2 lg:col-span-6 pt-3 border-t border-outline-variant flex flex-wrap items-center gap-4 text-xs">
              <span className="font-mono text-primary font-semibold">{scoreResult.tx_id}</span>
              <span>
                Composite Risk: <strong className="font-mono">{scoreResult.risk_score}/100</strong>
              </span>
              <RiskBadge level={scoreResult.risk_level} />
              <span className="font-mono text-on-surface-variant">
                XGBoost: {(scoreResult.xgb_probability * 100).toFixed(1)}% • IsoForest:{" "}
                {(scoreResult.iforest_score * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </form>
      )}

      {/* Search & Filters */}
      <div className="bg-surface-container border border-outline-variant rounded-lg p-4 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search TX ID, merchant, last 4 digits, device, or IP subnet..."
            value={q}
            onChange={(e) => {
              setPage(1);
              setQ(e.target.value);
            }}
            className="w-full pl-9 pr-3 py-2 rounded bg-surface-container-low border border-outline-variant text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:outline-none"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-on-surface-variant hidden sm:block" />
          <select
            aria-label="Filter by risk level"
            value={riskLevel}
            onChange={(e) => {
              setPage(1);
              setRiskLevel(e.target.value);
            }}
            className="rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-xs text-on-surface"
          >
            <option value="all">All Risk Levels</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            aria-label="Filter by analyst status"
            value={analystStatus}
            onChange={(e) => {
              setPage(1);
              setAnalystStatus(e.target.value);
            }}
            className="rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-xs text-on-surface"
          >
            <option value="all">All Statuses</option>
            <option value="unreviewed">Unreviewed</option>
            <option value="flagged">Flagged</option>
            <option value="cleared">Cleared</option>
            <option value="confirmed_fraud">Confirmed Fraud</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-surface-container border border-outline-variant rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low text-[11px] uppercase tracking-wider text-on-surface-variant">
                <th className="py-3 px-4 font-medium">TX ID</th>
                <th className="py-3 px-4 font-medium">Card</th>
                <th className="py-3 px-4 font-medium">Merchant</th>
                <th className="py-3 px-4 font-medium">Device / IP</th>
                <th className="py-3 px-4 font-medium text-right">Amount</th>
                <th className="py-3 px-4 font-medium text-right">Risk</th>
                <th className="py-3 px-4 font-medium">Level</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium text-right">Workspace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant text-[13px]">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-on-surface-variant">
                    Loading transactions...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-on-surface-variant">
                    No matching transactions found.
                  </td>
                </tr>
              ) : (
                items.map((tx) => (
                  <tr key={tx.tx_id} className="hover:bg-surface-container-high/50">
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
                    <td className="py-3 px-4 font-mono text-xs text-on-surface-variant">
                      <div>{tx.device_id}</div>
                      <div>{tx.ip_subnet}</div>
                    </td>
                    <td className="py-3 px-4 font-mono tabular-nums text-right">
                      ${tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-mono tabular-nums text-right font-semibold">
                      {tx.risk_score.toFixed(1)}
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge level={tx.risk_level} />
                    </td>
                    <td className="py-3 px-4">
                      <select
                        value={tx.analyst_status}
                        onChange={(e) => handleStatusChange(tx.tx_id, e.target.value)}
                        className="rounded bg-surface-container-low border border-outline-variant px-2 py-1 text-xs text-on-surface"
                      >
                        <option value="unreviewed">Unreviewed</option>
                        <option value="flagged">Flagged</option>
                        <option value="cleared">Cleared</option>
                        <option value="confirmed_fraud">Confirmed Fraud</option>
                      </select>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                      <Link
                        href={`/investigations?tx=${encodeURIComponent(tx.tx_id)}`}
                        className="px-2.5 py-1 rounded bg-primary-container text-primary text-xs font-medium border border-primary/25"
                      >
                        Investigate
                      </Link>
                      <Link
                        href={`/network?tx=${encodeURIComponent(tx.tx_id)}`}
                        className="px-2.5 py-1 rounded bg-surface-container-high text-on-surface text-xs border border-outline-variant"
                      >
                        Graph
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t border-outline-variant flex items-center justify-between text-xs text-on-surface-variant">
          <span className="font-mono">
            Showing page {page} of {totalPages} ({total.toLocaleString()} transactions)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded bg-surface-container-high border border-outline-variant disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-1.5 rounded bg-surface-container-high border border-outline-variant disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
