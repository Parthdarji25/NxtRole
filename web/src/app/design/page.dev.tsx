import type { Metadata } from "next";

import { Showroom } from "./Showroom";

export const metadata: Metadata = { title: "Components (development)" };

export default function DesignPage() {
  return <Showroom />;
}
