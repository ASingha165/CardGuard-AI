"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, KeyRound, Save } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function SettingsPage() {
  const [contamination, setContamination] = useState("0.035");
  const [highCutoff, setHighCutoff] = useState("75");
  const [criticalCutoff, setCriticalCutoff] = useState("90");
  const [autoFlag, setAutoFlag] = useState(true);
  const [apiKey, setApiKey] = useState("");
  const [envInfo, setEnvInfo] = useState<{ environment: string; max_upload_mb: number; require_auth: boolean } | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setApiKey(localStorage.getItem("cardguard_api_key") || "");
    }
    apiFetch<{
      iforest_contamination: number;
      high_risk_cutoff: number;
      critical_risk_cutoff: number;
      auto_flag_critical: boolean;
      environment: string;
      max_upload_mb: number;
      require_auth: boolean;
    }>("/api/settings").then((s) => {
      setContamination(String(s.iforest_contamination));
      setHighCutoff(String(s.high_risk_cutoff));
      setCriticalCutoff(String(s.critical_risk_cutoff));
      setAutoFlag(s.auto_flag_critical);
      setEnvInfo({
        environment: s.environment,
        max_upload_mb: s.max_upload_mb,
        require_auth: s.require_auth,
      });
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== "undefined") {
      if (apiKey.trim()) {
        localStorage.setItem("cardguard_api_key", apiKey.trim());
      } else {
        localStorage.removeItem("cardguard_api_key");
      }
    }
    await apiFetch("/api/settings", {
      method: "PATCH",
      body: JSON.stringify({
        iforest_contamination: Number(contamination),
        high_risk_cutoff: Number(highCutoff),
        critical_risk_cutoff: Number(criticalCutoff),
        auto_flag_critical: autoFlag,
      }),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <header>
        <h1 className="font-headline text-[28px] lg:text-[40px] leading-tight text-on-surface">
          Settings
        </h1>
        <p className="text-sm text-on-surface-variant">
          Configure risk thresholds, Isolation Forest contamination, and analyst API authentication.
        </p>
      </header>

      <form
        onSubmit={handleSave}
        className="bg-surface-container border border-outline-variant rounded-lg p-6 flex flex-col gap-5"
      >
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-on-surface-variant mb-1">
              Default Contamination
            </label>
            <input
              type="number"
              step="0.005"
              value={contamination}
              onChange={(e) => setContamination(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
            />
          </div>
          <div>
            <label className="block text-xs text-on-surface-variant mb-1">
              High Risk Cutoff
            </label>
            <input
              type="number"
              value={highCutoff}
              onChange={(e) => setHighCutoff(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
            />
          </div>
          <div>
            <label className="block text-xs text-on-surface-variant mb-1">
              Critical Risk Cutoff
            </label>
            <input
              type="number"
              value={criticalCutoff}
              onChange={(e) => setCriticalCutoff(e.target.value)}
              className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
            />
          </div>
        </div>

        <label className="flex items-center gap-3 text-sm text-on-surface cursor-pointer">
          <input
            type="checkbox"
            checked={autoFlag}
            onChange={(e) => setAutoFlag(e.target.checked)}
            className="rounded border-outline-variant bg-surface-container-low text-primary"
          />
          Automatically flag critical-risk transactions for analyst review
        </label>

        <div className="pt-4 border-t border-outline-variant">
          <label className="flex items-center gap-2 text-xs text-on-surface-variant mb-1">
            <KeyRound className="w-3.5 h-3.5" />
            Analyst API Key (stored in browser localStorage for X-API-Key header)
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Optional in local dev; required when REQUIRE_AUTH=true"
            className="w-full rounded bg-surface-container-low border border-outline-variant px-3 py-2 text-sm font-mono text-on-surface"
          />
        </div>

        {envInfo && (
          <div className="rounded bg-surface-container-low border border-outline-variant p-3.5 text-xs font-mono text-on-surface-variant flex flex-wrap gap-4">
            <span>ENV: {envInfo.environment}</span>
            <span>MAX_UPLOAD: {envInfo.max_upload_mb} MB</span>
            <span>AUTH_ENFORCED: {String(envInfo.require_auth)}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          {saved ? (
            <span className="inline-flex items-center gap-1.5 text-xs text-success">
              <CheckCircle2 className="w-4 h-4" />
              Settings saved.
            </span>
          ) : (
            <span />
          )}
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-on-primary text-xs font-semibold"
          >
            <Save className="w-4 h-4" />
            Save Settings
          </button>
        </div>
      </form>
    </div>
  );
}
