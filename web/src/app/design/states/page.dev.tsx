import type { Metadata } from "next";

import { StatesSheet } from "./StatesSheet";

export const metadata: Metadata = { title: "Screen states (development)" };

export default function StatesPage() {
  return <StatesSheet />;
}
