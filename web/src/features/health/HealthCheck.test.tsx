import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthCheck } from "./HealthCheck";

// The responses below are the API's own documented shapes (api/app/health/router.py).
function reply(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status });
}

const healthy = () => reply(200, { database: "ok", redis: "ok" });
const redisDown = () =>
  reply(503, {
    detail: { code: "not_ready", message: "…", checks: { database: "ok", redis: "error" } },
  });

describe("HealthCheck", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a loading message first, then both services as ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(healthy()));

    render(<HealthCheck />);

    expect(screen.getByRole("status")).toHaveTextContent("Checking services");
    expect(await screen.findByText("database ok, redis ok")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("names the failed service and recovers after Retry", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(redisDown()).mockResolvedValueOnce(healthy()),
    );

    render(<HealthCheck />);
    expect(await screen.findByText("database ok, redis error")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("database ok, redis ok")).toBeInTheDocument();
  });

  it("explains when the API cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network down")));

    render(<HealthCheck />);

    expect(await screen.findByText("The API cannot be reached.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("treats an unexpected answer as unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 502 })));

    render(<HealthCheck />);

    expect(await screen.findByText("The API cannot be reached.")).toBeInTheDocument();
  });
});
