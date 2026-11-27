import type { Metadata } from "next";

import { LegalPage } from "@/components/layout/legal-page";
import { ABOUT } from "@/content/legal";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return <LegalPage content={ABOUT} />;
}
