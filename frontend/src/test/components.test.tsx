import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { RiskBadge } from "@/components/RiskBadge";
import { AppShell } from "@/components/AppShell";

describe("CardGuard UI Components", () => {
  it("renders RiskBadge levels accurately", () => {
    render(
      <div>
        <RiskBadge level="critical" />
        <RiskBadge level="high" />
        <RiskBadge level="low" />
      </div>
    );
    expect(screen.getByText("critical")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("low")).toBeInTheDocument();
  });

  it("renders AppShell with all 9 navigation routes and provenance badge", () => {
    render(
      <AppShell>
        <div>Workspace Content</div>
      </AppShell>
    );
    expect(screen.getByText("Executive Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Transaction Intel")).toBeInTheDocument();
    expect(screen.getByText("AI Investigation")).toBeInTheDocument();
    expect(screen.getByText("Fraud Network")).toBeInTheDocument();
    expect(screen.getByText("Model Intelligence")).toBeInTheDocument();
    expect(screen.getByText("Dataset Laboratory")).toBeInTheDocument();
    expect(screen.getByText("Investigation History")).toBeInTheDocument();
    expect(screen.getByText("Reports & Exports")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByText("Synthetic Demo Data")).toBeInTheDocument();
    expect(screen.getByText("Workspace Content")).toBeInTheDocument();
  });
});
