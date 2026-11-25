"use client";

import React, { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Background,
  Controls,
  Edge,
  MiniMap,
  Node,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { apiFetch } from "@/lib/api";

interface NetworkPayload {
  nodes: Array<{ id: string; type: string; label: string; meta: Record<string, unknown> }>;
  edges: Array<{ id: string; source: string; target: string; relation: string }>;
  summary: {
    transaction_count: number;
    node_count: number;
    edge_count: number;
    shared_devices: number;
    shared_ip_subnets: number;
  };
}

const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  transaction: { bg: "#263500", border: "#C8F169", text: "#D8FF7E" },
  card: { bg: "#00315C", border: "#58A6FF", text: "#D3E4FF" },
  merchant: { bg: "#1A1C1B", border: "#454746", text: "#F1F1EE" },
  device: { bg: "#442B00", border: "#F5B041", text: "#FFDDB2" },
  ip_subnet: { bg: "#680010", border: "#FF5A5F", text: "#FFDAD8" },
};

function NetworkContent() {
  const searchParams = useSearchParams();
  const initialTx = searchParams.get("tx") || "";

  const [focusTx, setFocusTx] = useState(initialTx);
  const [minRisk, setMinRisk] = useState(75);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [summary, setSummary] = useState<NetworkPayload["summary"] | null>(null);

  const loadGraph = useCallback(async () => {
    const params = new URLSearchParams({ min_risk_score: String(minRisk), limit: "24" });
    if (focusTx.trim()) params.set("focus_tx_id", focusTx.trim());
    const data = await apiFetch<NetworkPayload>(`/api/network?${params.toString()}`);
    setSummary(data.summary);

    // Deterministic layered layout by entity type
    const laneX: Record<string, number> = {
      card: 40,
      transaction: 300,
      merchant: 580,
      device: 840,
      ip_subnet: 1100,
    };
    const laneCount: Record<string, number> = {};

    const rfNodes: Node[] = data.nodes.map((n) => {
      const idx = laneCount[n.type] || 0;
      laneCount[n.type] = idx + 1;
      const palette = NODE_COLORS[n.type] || NODE_COLORS.merchant;
      return {
        id: n.id,
        position: { x: laneX[n.type] ?? 300, y: 40 + idx * 90 },
        data: { label: `${n.type.toUpperCase()}: ${n.label}` },
        style: {
          background: palette.bg,
          color: palette.text,
          border: `1px solid ${palette.border}`,
          borderRadius: "10px",
          fontSize: "11px",
          fontFamily: "var(--font-redhat-mono), monospace",
          padding: "8px 12px",
          minWidth: "170px",
        },
      };
    });

    const rfEdges: Edge[] = data.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.relation,
      animated: e.relation === "FROM_DEVICE" || e.relation === "VIA_IP",
      style: { stroke: "#454746" },
      labelStyle: { fill: "#90918F", fontSize: 9 },
    }));

    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [focusTx, minRisk]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
            Fraud Network Explorer
          </h1>
          <p className="text-sm text-on-surface-variant">
            Observed entity relationships linking card tokens, transactions, merchants, devices, and IP subnets.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={focusTx}
            onChange={(e) => setFocusTx(e.target.value)}
            placeholder="Focus TX ID (optional)"
            className="rounded bg-surface-container border border-outline-variant px-3 py-2 text-xs font-mono text-on-surface"
          />
          <select
            value={minRisk}
            onChange={(e) => setMinRisk(Number(e.target.value))}
            className="rounded bg-surface-container border border-outline-variant px-3 py-2 text-xs text-on-surface"
          >
            <option value={50}>Risk ≥ 50</option>
            <option value={75}>Risk ≥ 75</option>
            <option value={90}>Risk ≥ 90</option>
          </select>
        </div>
      </header>

      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            ["Transactions", summary.transaction_count],
            ["Total Nodes", summary.node_count],
            ["Observed Links", summary.edge_count],
            ["Shared Devices", summary.shared_devices],
            ["Shared IP Subnets", summary.shared_ip_subnets],
          ].map(([label, val]) => (
            <div
              key={String(label)}
              className="bg-surface-container border border-outline-variant rounded-lg p-4"
            >
              <div className="text-xs text-on-surface-variant">{label}</div>
              <div className="font-mono text-xl font-semibold text-on-surface mt-1">{val}</div>
            </div>
          ))}
        </div>
      )}

      <div className="h-[580px] bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background color="#2F3130" gap={20} />
          <Controls />
          <MiniMap nodeColor="#C8F169" maskColor="rgba(16, 18, 17, 0.8)" />
        </ReactFlow>
      </div>
    </div>
  );
}

export default function NetworkPage() {
  return (
    <Suspense fallback={<div className="text-sm text-on-surface-variant">Loading graph...</div>}>
      <NetworkContent />
    </Suspense>
  );
}
