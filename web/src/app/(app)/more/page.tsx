import type { Metadata } from "next";

import { SignOutButton } from "@/features/auth/SignOutButton";
import { MoreScreen } from "@/features/more/MoreScreen";

export const metadata: Metadata = { title: "More" };

export default function MorePage() {
  return <MoreScreen footer={<SignOutButton />} />;
}
