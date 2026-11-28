"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { restore, signIn } from "@/lib/session";
import { useSession } from "@/lib/useSession";

import { AuthLayout } from "./AuthLayout";
import { LoginForm } from "./LoginForm";

/** The Sign-in screen. Whoever is signed in goes straight to `next`. */
export function LoginScreen({ next }: { next: string }) {
  const { status } = useSession();
  const router = useRouter();

  useEffect(() => {
    // A visit with a live sign-in does not need the password again.
    if (status === "unknown") void restore();
    if (status === "signedIn") router.replace(next);
  }, [status, next, router]);

  return (
    <AuthLayout
      title="Sign in"
      phoneTitle="Wake up to the jobs worth your time."
      phoneLead="Sign in to see your brief."
    >
      <LoginForm onSignIn={({ email, password }) => signIn(email, password)} />
    </AuthLayout>
  );
}
