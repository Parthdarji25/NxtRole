import type { Metadata } from "next";

import { LegalPage } from "@/components/layout/legal-page";
import { PRIVACY } from "@/content/legal";

export const metadata: Metadata = { title: "Privacy notice" };

export default function PrivacyPage() {
  return <LegalPage content={PRIVACY} />;
}
