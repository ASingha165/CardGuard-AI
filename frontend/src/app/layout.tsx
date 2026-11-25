import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "CardGuard AI — Precision Fraud Intelligence",
  description:
    "Institutional credit-card fraud detection, ML evaluation, network exploration, and explainable AI investigation platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Alatsi&family=Instrument+Sans:wght@400;500;600;700&family=Red+Hat+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-surface text-on-surface font-body antialiased selection:bg-primary selection:text-on-primary">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
