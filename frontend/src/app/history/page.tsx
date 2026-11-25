"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

interface HistoryItem {
  case_id: string;
  tx_id: string;
  risk_score: number;
  risk_classification: string;
  status: string;
  analyst_notes: string | null;
  created_at: string | null;
  transaction: {
    merchant: string;
    amount: number;
    card_last4: string;
  } | null;
}

export default function InvestigationHistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    apiFetch<{ items: HistoryItem[] }>(
      `/api/investigations?status=${statusFilter}&page=1&page_size=50`
    ).then((res) => setItems(res.items));
  }, [statusFilter]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
            Investigation History
          </h1>
          <p className="text-sm text-on-surface-variant">
            Audit trail of AI-assisted fraud cases, analyst dispositions, and escalated alerts.
          </p>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded bg-surface-container border border-outline-variant px-3 py-2 text-xs text-on-surface"
        >
          <option value="all">All Case Statuses</option>
          <option value="open">Open</option>
          <option value="escalated">Escalated</option>
          <option value="resolved_fraud">Resolved Fraud</option>
          <option value="resolved_legit">Resolved Legit</option>
        </select>
      </header>

      <div className="bg-surface-container border border-outline-variant rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low text-[11px] uppercase tracking-wider text-on-surface-variant">
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-4">TX ID</th>
                <th className="py-3 px-4">Merchant</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4 text-right">Risk</th>
                <th className="py-3 px-4">Classification</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Open</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant text-[13px]">
              {items.map((item) => (
                <tr key={item.case_id} className="hover:bg-surface-container-high/50">
                  <td className="py-3 px-4 font-mono text-primary">{item.case_id}</td>
                  <td className="py-3 px-4 font-mono">{item.tx_id}</td>
                  <td className="py-3 px-4">{item.transaction?.merchant ?? "—"}</td>
                  <td className="py-3 px-4 font-mono text-right">
                    {item.transaction ? `$${item.transaction.amount.toFixed(2)}` : "—"}
                  </td>
                  <td className="py-3 px-4 font-mono text-right font-semibold">
                    {item.risk_score.toFixed(1)}
                  </td>
                  <td className="py-3 px-4">
                    <RiskBadge level={item.risk_classification} />
                  </td>
                  <td className="py-3 px-4 font-mono text-xs uppercase text-on-surface-variant">
                    {item.status}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      href={`/investigations?tx=${encodeURIComponent(item.tx_id)}`}
                      className="px-2.5 py-1 rounded bg-surface-container-high border border-outline-variant text-xs text-primary"
                    >
                      Review
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
