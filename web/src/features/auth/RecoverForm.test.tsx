import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/http";

import { LoginForm } from "./LoginForm";
import { RecoverForm } from "./RecoverForm";

const type = (label: string, value: string) =>
  userEvent.type(screen.getByLabelText(label, { exact: true }), value);

async function fill() {
  await type("Email", "you@example.com");
  await userEvent.type(screen.getByLabelText(/Recovery code/), "abcd efgh");
  await type("New password", "a new long password");
  await type("New password again", "a new long password");
}

const submit = () => userEvent.click(screen.getByRole("button", { name: "Set new password" }));

describe("recovery form", () => {
  it("sends the details and shows the next code once", async () => {
    const onRecover = vi.fn(async () => "NEXT-CODE");
    render(<RecoverForm onRecover={onRecover} />);

    await fill();
    await submit();

    expect(onRecover).toHaveBeenCalledWith({
      email: "you@example.com",
      recovery_code: "abcd efgh",
      new_password: "a new long password",
    });
    expect(await screen.findByText("NEXT-CODE")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /sign in/i })).toHaveAttribute("href", "/login");
  });

  it("checks that the two passwords match before sending", async () => {
    const onRecover = vi.fn(async () => "NEXT-CODE");
    render(<RecoverForm onRecover={onRecover} />);

    await type("Email", "you@example.com");
    await userEvent.type(screen.getByLabelText(/Recovery code/), "abcd");
    await type("New password", "a new long password");
    await type("New password again", "another long password");
    await submit();

    expect(await screen.findByText("The two passwords are not the same.")).toBeInTheDocument();
    expect(onRecover).not.toHaveBeenCalled();
  });
});

describe("@E-34 sign-in button", () => {
  it("ignores a second click while signing in", async () => {
    let finish: () => void = () => {};
    const onSignIn = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)));
    render(<LoginForm onSignIn={onSignIn} />);
    await type("Email", "you@example.com");
    await type("Password", "any password");
    const button = screen.getByRole("button", { name: /Sign in/ });

    await userEvent.dblClick(button);
    await userEvent.type(screen.getByLabelText("Password", { exact: true }), "{Enter}");

    expect(onSignIn).toHaveBeenCalledTimes(1);
    finish();
  });

  it.each([
    ["invalid_credentials", "That email or password is not right."],
    ["account_locked", "Too many wrong attempts. Try again in 15 minutes."],
    ["rate_limited", "Too many attempts. Try again in 40 seconds."],
    ["unreachable", "NxtRole cannot be reached. Check your connection and try again."],
  ])("shows the reason for %s", async (code, message) => {
    render(
      <LoginForm
        onSignIn={async () => {
          throw new ApiError(401, { code, message });
        }}
      />,
    );
    await type("Email", "you@example.com");
    await type("Password", "any password");

    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
  });
});
