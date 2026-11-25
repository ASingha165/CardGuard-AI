---
name: "CardGuard AI — Precision Dark Intelligence"
description: "Apple-inspired dark charcoal and lime-green design system for an institutional credit-card fraud detection and AI investigation platform."
---

## Overview

CardGuard AI embodies the quiet authority of an institutional financial intelligence instrument. Inspired by Apple's pro-grade hardware and software interfaces, it pairs a deep charcoal canvas with surgical lime-green highlights, crisp typographic hierarchy, and generous negative space. The interface is minimalist yet information-dense: analysts and researchers can scan macro risk posture in seconds, drill into individual transaction evidence, inspect graph topologies, and calibrate machine-learning models without visual noise or generic neon-dashboard clutter.

## Colors

The palette is anchored by a deep charcoal ground (`#101211`) that eliminates eye strain during long investigation sessions, paired with a high-visibility lime-green primary accent (`#C8F169`) reserved strictly for primary actions, active states, and key model thresholds. Semantic status hues—success, warning, danger, and info—are used exclusively to communicate risk classifications, model states, and data integrity.

```yaml
colors:
  primary: "#C8F169"
  on-primary: "#151F00"
  primary-container: "#263500"
  on-primary-container: "#D8FF7E"
  surface: "#101211"
  surface-container-lowest: "#0A0C0B"
  surface-container-low: "#151816"
  surface-container: "#1A1C1B"
  surface-container-high: "#222523"
  surface-container-highest: "#2F3130"
  on-surface: "#F1F1EE"
  on-surface-variant: "#90918F"
  outline: "#454746"
  outline-variant: "#2F3130"
  success: "#3FB950"
  on-success: "#002105"
  success-container: "#00390D"
  on-success-container: "#83FC89"
  warning: "#F5B041"
  on-warning: "#291800"
  warning-container: "#442B00"
  on-warning-container: "#FFDDB2"
  danger: "#FF5A5F"
  on-danger: "#410007"
  danger-container: "#680010"
  on-danger-container: "#FFDAD8"
  info: "#58A6FF"
  on-info: "#001C38"
  info-container: "#00315C"
  on-info-container: "#D3E4FF"
  error: "#FF5A5F"
  on-error: "#410007"
```

## Typography

A three-role typographic hierarchy separates narrative headings, dense analytical UI, and tabular financial data. **Alatsi** brings geometric precision to page titles and hero KPIs; **Instrument Sans** delivers crisp legibility across tables, filters, and investigation prose; and **Red Hat Mono** guarantees strict vertical alignment for transaction IDs, currency amounts, timestamps, and model metrics (`tabular-nums`).

```yaml
typography:
  display-lg:
    fontFamily: "Alatsi"
    fontSize: 40px
    fontWeight: 400
    lineHeight: 44px
    letterSpacing: -0.75px
  display-lg-mobile:
    fontFamily: "Alatsi"
    fontSize: 28px
    fontWeight: 400
    lineHeight: 34px
    letterSpacing: -0.5px
  headline-lg:
    fontFamily: "Alatsi"
    fontSize: 28px
    fontWeight: 400
    lineHeight: 34px
    letterSpacing: -0.25px
  headline-md:
    fontFamily: "Instrument Sans"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 26px
    letterSpacing: -0.2px
  title-md:
    fontFamily: "Instrument Sans"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 22px
    letterSpacing: 0px
  body-md:
    fontFamily: "Instrument Sans"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: 0px
  body-sm:
    fontFamily: "Instrument Sans"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 18px
    letterSpacing: 0px
  label-lg:
    fontFamily: "Instrument Sans"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 18px
    letterSpacing: 0.1px
  label-sm:
    fontFamily: "Instrument Sans"
    fontSize: 11px
    fontWeight: 500
    lineHeight: 14px
    letterSpacing: 0.4px
  mono-lg:
    fontFamily: "Red Hat Mono"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 30px
    letterSpacing: -0.5px
  mono-md:
    fontFamily: "Red Hat Mono"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 18px
    letterSpacing: 0px
  mono-sm:
    fontFamily: "Red Hat Mono"
    fontSize: 11px
    fontWeight: 500
    lineHeight: 14px
    letterSpacing: 0.2px
```

## Layout & Spacing

Desktop layouts use a persistent `248px` left navigation rail paired with a fluid main workspace (`max-width: 1440px`) structured on a 12-column CSS Grid with `24px` (`gutter-lg`) gaps. On mobile (`< 1024px`), the sidebar collapses into a slide-over drawer triggered from a compact top bar, multi-column KPI and chart grids stack to single columns, and data tables adapt into scannable cards. All spacing adheres strictly to a `4px` / `8px` base grid.

```yaml
spacing:
  gutter-xs: 4px
  gutter-sm: 8px
  gutter-md: 16px
  gutter-lg: 24px
  gutter-xl: 32px
  section: 40px
  page-margin: 24px
```

## Elevation & Depth

Depth is achieved through **tonal surface layering** and **hairline ghost borders** (`1px solid #2F3130`), rather than heavy drop shadows or frosted-glass blurs. The base canvas sits at `#101211`, primary cards step up to `#1A1C1B` (`surface-container`), and interactive popovers or drawers step up to `#222523` (`surface-container-high`). Subtle ambient shadows (`0 8px 24px rgba(0, 0, 0, 0.32)`) are reserved solely for floating drawers, tooltips, and modal overlays.

## Shapes

Corners are crisp and architectural, balancing precision with approachability. Cards and workspace panels use `16px` (`lg`), inner metric tiles and charts use `12px` (`md`), buttons and inputs use `10px` (`DEFAULT`), and status badges or filter pills use `9999px` (`full`).

```yaml
rounded:
  sm: 6px
  DEFAULT: 10px
  md: 12px
  lg: 16px
  xl: 20px
  full: 9999px
```

## Motion & Micro-interaction

Transitions are immediate, restrained, and strictly functional. Hover and selection feedback resolves in `120ms` (`state-change`), while drawers, expandable transaction rows, and chart updates ease in over `220ms` (`surface-enter`). Only `transform`, `opacity`, and color properties are animated; no decorative looping animations are permitted.

```yaml
motion:
  state-change:
    duration: 120ms
    delay: 0ms
    timingFunction: cubic-bezier(0.2, 0, 0, 1)
  surface-enter:
    duration: 220ms
    delay: 0ms
    timingFunction: cubic-bezier(0.2, 0, 0, 1)
  surface-exit:
    duration: 150ms
    delay: 0ms
    timingFunction: cubic-bezier(0.4, 0, 1, 1)
```

## Voice & Content Strategy

- **Tone of voice:** Clinical, transparent, and analytical. Never sensationalize fraud alerts or exaggerate AI certainty. Explicitly separate observed evidence ("Velocity: 4 transactions in 11 minutes") from model inference ("Isolation Forest anomaly score: 0.91").
- **Data Provenance:** Clearly label demonstration environments as **Synthetic Demo Data** and distinguish them from **Uploaded Dataset** sessions. Never use fake live banking feeds.
- **Capitalisation:** Sentence case for headings, table headers, navigation items, and button labels; uppercase only for compact `11px` metadata tags or risk badges when needed.
- **Button and action labels:** Action-oriented verb phrases (`Run Evaluation`, `Export Report`, `Flag for Review`, `Reset Threshold`).
- **Numbers & Dates:** Always use `tabular-nums` (`font-mono`) for currency (`$14,280.50`), risk scores (`87 / 100`), percentages (`94.2%`), and ISO-style timestamps (`2026-11-25 06:42 UTC`).

## Components

Component implementations live as individual HTML sticker sheet files in
`components/`. Each file contains the canonical, styled HTML components with
`<!-- COMPONENT: name -->` comment markers. Read each file before use.

- **Badge** → `@components/badge.html` — `badge-numeric`, `badge-dot`
- **Button** → `@components/button.html` — `button-primary`, `button-icon`, `button-with-icon`
- **Card** → `@components/card.html` — `card-elevated`, `card-action`, `card-interactive`, `card-interactive-2`
- **Input Field** → `@components/input-field.html` — `input-field-text`, `input-field-icon`
- **Table** → `@components/table.html` — `table-standard`, `table-interactive`, `table-selectable`
