"use client";

import { useQuery } from "@tanstack/react-query";

import { RULES } from "@/features/preferences/api";
import { api } from "@/lib/api";
import { reasonFor } from "@/lib/useAction";

import { RulesList, type Rule, type RuleList } from "./RulesList";

/** "Your rules", connected to the API. */
export function RulesContainer() {
  const rules = useQuery({
    queryKey: RULES,
    queryFn: () => api<{ items: Rule[] }>("/api/rules"),
  });
  const shown: RuleList = rules.data
    ? { status: "ready", items: rules.data.items }
    : rules.isError
      ? { status: "error", message: reasonFor(rules.error), retry: () => void rules.refetch() }
      : { status: "loading" };
  return <RulesList rules={shown} />;
}
