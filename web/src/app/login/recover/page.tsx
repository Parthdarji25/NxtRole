import type { Metadata } from "next";

import { RecoverScreen } from "@/features/auth/RecoverScreen";

// Not linked from any screen (D-027), and kept out of search engines.
export const metadata: Metadata = {
  title: "Get back in",
  robots: { index: false, follow: false },
};

export default function RecoverPage() {
  return <RecoverScreen />;
}
