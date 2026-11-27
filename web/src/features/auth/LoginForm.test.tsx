import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "./LoginForm";
import { loginSchema } from "./loginSchema";

const submit = () => userEvent.click(screen.getByRole("button", { name: "Sign in" }));

describe("sign-in form", () => {
  it("offers email and password only: no Google, no emailed code (D-010)", () => {
    render(<LoginForm />);
    expect(screen.getByLabelText("Email")).toHaveAttribute("autocomplete", "username");
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.queryByText(/google|code/i)).not.toBeInTheDocument();
  });

  it("explains what is missing", async () => {
    render(<LoginForm />);
    await submit();
    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-invalid", "true");
  });

  it("shows and hides the password", async () => {
    render(<LoginForm />);
    await userEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "text");
  });

  it("sends nothing and says so, because sign-in arrives in Phase 4", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText("Email"), "person@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "any text");
    await submit();
    expect(await screen.findByText(/Nothing was sent/)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("never puts the password in the address if the script has not loaded", () => {
    const { container } = render(<LoginForm />);
    expect(container.querySelector("form")).toHaveAttribute("method", "post");
  });

  it("trims spaces around the email and rejects very long input", () => {
    const parsed = loginSchema.parse({ email: "  person@example.com ", password: "x" });
    expect(parsed.email).toBe("person@example.com");
    expect(
      loginSchema.safeParse({ email: "person@example.com", password: "x".repeat(201) }).success,
    ).toBe(false);
  });
});
