import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";

import { Toaster } from "@/components/ui/toast";
import { THEME_SCRIPT } from "@/lib/theme";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "NxtRole", template: "%s · NxtRole" },
  description: "A personal AI job-search agent for India.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F4F1EA" },
    { media: "(prefers-color-scheme: dark)", color: "#111214" },
  ],
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  // Reading the request makes every page render per request, which the nonce needs.
  const nonce = (await headers()).get("x-nonce") ?? undefined;

  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
      // The theme script sets data-theme before React starts.
      suppressHydrationWarning
    >
      <head>
        {/* A fixed script of ours (no outside content) that applies the theme before painting. */}
        <script
          nonce={nonce}
          suppressHydrationWarning
          dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }}
        />
      </head>
      <body className="font-sans">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
