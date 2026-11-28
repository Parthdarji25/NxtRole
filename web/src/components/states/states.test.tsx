import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EMPTY_STATES, type EmptyContent } from "@/content/emptyStates";
import { PROFILE_STATES } from "@/content/profileStates";

import { EmptyScreenState } from "./EmptyScreenState";
import { Banner, ErrorState, ListSkeleton, OfflineNotice } from "./states";

const screens: EmptyContent[] = Object.values(EMPTY_STATES);
// Resume has two messages of its own: before and after the profile is approved.
const all: EmptyContent[] = [...screens, ...Object.values(PROFILE_STATES)];

describe("states", () => {
  it("loading tells screen readers what is happening", () => {
    render(<ListSkeleton label="Loading jobs" />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading jobs…");
  });

  it("error is announced and can be retried", async () => {
    const onRetry = vi.fn();
    render(<ErrorState title="Your jobs did not load" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Your jobs did not load");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("banners say what happened in words", () => {
    render(
      <>
        <OfflineNotice />
        <Banner tag="Source paused">A source stopped.</Banner>
      </>,
    );
    expect(screen.getAllByRole("status")).toHaveLength(2);
    expect(screen.getByText(/You are offline/)).toBeInTheDocument();
  });

  it("empty screen shows one blue action at most", () => {
    const { container } = render(<EmptyScreenState content={EMPTY_STATES.today} />);
    expect(screen.getByRole("heading", { name: "No brief yet" })).toBeInTheDocument();
    expect(container.querySelectorAll('[data-variant="primary"]')).toHaveLength(1);
  });
});

describe("@E-01 empty-state wording", () => {
  it("covers each screen once", () => {
    const routes = screens.map((content) => content.route);
    expect(new Set(routes).size).toBe(routes.length);
  });

  it.each(all)("$route says what to do next with working links", (content) => {
    expect(content.title.length).toBeGreaterThan(3);
    expect(content.body.length).toBeGreaterThan(20);
    for (const action of [content.primary, content.secondary]) {
      if (action) expect(action.href).toMatch(/^\//);
    }
    expect(content.primary ?? content.secondary).toBeDefined();
  });

  it("never claims NxtRole sends anything", () => {
    for (const content of all) {
      expect(content.body).not.toMatch(/we(’|')ll send|NxtRole sends|sends it for you/i);
    }
  });
});
