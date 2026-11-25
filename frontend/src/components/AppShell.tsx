"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BrainCircuit,
  Cpu,
  FileText,
  FlaskConical,
  History,
  Menu,
  Network,
  ReceiptText,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Executive Dashboard", icon: Activity },
  { href: "/transactions", label: "Transaction Intel", icon: ReceiptText },
  { href: "/investigations", label: "AI Investigation", icon: BrainCircuit },
  { href: "/network", label: "Fraud Network", icon: Network },
  { href: "/models", label: "Model Intelligence", icon: Cpu },
  { href: "/datasets", label: "Dataset Laboratory", icon: FlaskConical },
  { href: "/history", label: "Investigation History", icon: History },
  { href: "/reports", label: "Reports & Exports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-surface text-on-surface">
      {/* Mobile Top Bar */}
      <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 bg-surface-container-low border-b border-outline-variant">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="inline-flex items-center justify-center w-8 h-8 rounded bg-primary-container text-primary border border-primary/25">
            <ShieldCheck className="w-4 h-4" />
          </span>
          <span className="font-title text-base font-semibold text-on-surface">
            CardGuard AI
          </span>
        </Link>
        <button
          type="button"
          aria-label="Open navigation"
          onClick={() => setMobileOpen(true)}
          className="inline-flex items-center justify-center w-9 h-9 rounded bg-surface-container-high border border-outline-variant text-on-surface"
        >
          <Menu className="w-4 h-4" />
        </button>
      </header>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-surface-container-lowest/80 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Persistent 248px Sidebar Rail */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-[248px] shrink-0 bg-surface-container-low border-r border-outline-variant flex flex-col justify-between p-4 transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between px-2 pt-1">
            <Link href="/" className="flex items-center gap-3">
              <span className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-primary-container text-primary border border-primary/25">
                <ShieldCheck className="w-5 h-5" />
              </span>
              <div className="flex flex-col">
                <span className="font-title text-base font-semibold text-on-surface">
                  CardGuard AI
                </span>
                <span className="font-mono text-[11px] text-on-surface-variant">
                  v4.2 • Fraud Intel
                </span>
              </div>
            </Link>
            <button
              type="button"
              aria-label="Close navigation"
              onClick={() => setMobileOpen(false)}
              className="lg:hidden inline-flex items-center justify-center w-8 h-8 rounded text-on-surface-variant hover:text-on-surface"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <nav aria-label="Primary" className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded text-[13px] font-medium transition-colors duration-150 ${
                    isActive
                      ? "bg-primary-container text-on-primary-container border border-primary/25"
                      : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container border border-transparent"
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? "text-primary" : ""
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Provenance Footer */}
        <div className="pt-4 border-t border-outline-variant flex flex-col gap-2 px-2">
          <span
            role="status"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary-container text-on-primary-container border border-primary/25 w-fit"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            <span className="text-[11px] font-medium">Synthetic Demo Data</span>
          </span>
          <p className="text-[12px] text-on-surface-variant">
            Isolation Forest + XGBoost • SHAP
          </p>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 max-w-[1440px] mx-auto w-full">
        {children}
      </main>
    </div>
  );
}
