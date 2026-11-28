import type { Metadata } from "next";

import { LoginScreen } from "@/features/auth/LoginScreen";
import { safeNext } from "@/lib/safeNext";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>;
}) {
  const { next } = await searchParams;
  return <LoginScreen next={safeNext(next)} />;
}
