import type { Metadata } from "next";

import { LegalPage } from "@/components/layout/legal-page";
import { TERMS } from "@/content/legal";

export const metadata: Metadata = { title: "Terms of use" };

export default function TermsPage() {
  return <LegalPage content={TERMS} />;
}
