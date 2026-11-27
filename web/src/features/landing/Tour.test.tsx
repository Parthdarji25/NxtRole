import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SAFETY_FACTS, TOUR_STEPS } from "@/content/landing";

import { STEP_MILLISECONDS, Tour } from "./Tour";

function fakeMotionSetting(reduced: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: reduced, addEventListener() {}, removeEventListener() {} })),
  );
}

const heading = () => screen.getByRole("heading", { level: 3 }).textContent;
const wait = () => act(() => vi.advanceTimersByTime(STEP_MILLISECONDS));

describe("how it works tour", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("plays on its own and can be paused", () => {
    fakeMotionSetting(false);
    render(<Tour />);
    expect(heading()).toBe(TOUR_STEPS[0]!.title);
    wait();
    expect(heading()).toBe(TOUR_STEPS[1]!.title);

    fireEvent.click(screen.getByRole("button", { name: /Pause/ }));
    wait();
    expect(heading()).toBe(TOUR_STEPS[1]!.title);
  });

  it("does not move by itself for people who prefer reduced motion", () => {
    fakeMotionSetting(true);
    render(<Tour />);
    wait();
    expect(heading()).toBe(TOUR_STEPS[0]!.title);
    expect(screen.getByRole("button", { name: /Play/ })).toBeInTheDocument();
  });

  it("stops playing once the visitor picks a step, and wraps at both ends", () => {
    fakeMotionSetting(false);
    render(<Tour />);
    fireEvent.click(screen.getByRole("button", { name: "Previous step" }));
    expect(heading()).toBe(TOUR_STEPS.at(-1)!.title);
    wait();
    expect(heading()).toBe(TOUR_STEPS.at(-1)!.title);
    fireEvent.click(screen.getByRole("button", { name: "Start again" }));
    expect(heading()).toBe(TOUR_STEPS[0]!.title);
  });
});

describe("landing wording (D-046)", () => {
  const text = JSON.stringify([TOUR_STEPS, SAFETY_FACTS]);

  it("makes no claim that a decision ruled out", () => {
    for (const forbidden of [
      /Telegram/i,
      /OpenRouter/i,
      /Mock data/i,
      /Edge Function/i,
      /Supabase Cron/i,
      /15.{0,3}30 minutes/i,
      /LinkedIn and Naukri searches/i,
      /Indeed/i,
      /1,240|\b163\b|\b41 companies/,
      /read-only/i,
    ]) {
      expect(text).not.toMatch(forbidden);
    }
  });

  it("states the true schedule", () => {
    expect(text).toContain("every hour from 7 AM to 9 PM");
  });
});
