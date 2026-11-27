import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { Badge, CountBadge, TrustBadge } from "./badge";
import { Button } from "./button";
import { Chip } from "./chip";
import { Field, Input } from "./field";
import { PageHeader, ProgressBar } from "./layout";
import { Segmented } from "./segmented";
import { Sheet, SheetContent, SheetTrigger } from "./sheet";
import { Switch } from "./switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";

describe("Button", () => {
  it("does not submit a form by accident and reports its variant", () => {
    render(<Button variant="primary">Apply</Button>);
    const button = screen.getByRole("button", { name: "Apply" });
    expect(button).toHaveAttribute("type", "button");
    expect(button).toHaveAttribute("data-variant", "primary");
  });

  it("blocks clicks and says it is busy while loading", async () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Save
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Save" });
    await userEvent.click(button);
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(onClick).not.toHaveBeenCalled();
  });

  it("can give a link the button look", () => {
    render(
      <Button asChild variant="outline">
        <a href="/jobs">Browse jobs</a>
      </Button>,
    );
    expect(screen.getByRole("link", { name: "Browse jobs" })).toHaveAttribute("href", "/jobs");
  });
});

describe("Field", () => {
  it("ties the label, hint and error to the input", () => {
    render(
      <Field label="Email" hint="Used to sign in." error="Enter a valid email address.">
        {(control) => <Input {...control} />}
      </Field>,
    );
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Enter a valid email address. Used to sign in.");
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a valid email address.");
  });

  it("is not marked invalid without an error", () => {
    render(<Field label="Email">{(control) => <Input {...control} />}</Field>);
    expect(screen.getByLabelText("Email")).not.toHaveAttribute("aria-invalid");
  });
});

describe("toggles", () => {
  it("switch changes state with the keyboard", async () => {
    function Example() {
      const [on, setOn] = useState(false);
      return <Switch aria-label="Quiet hours" checked={on} onCheckedChange={setOn} />;
    }
    render(<Example />);
    const control = screen.getByRole("switch", { name: "Quiet hours" });
    control.focus();
    await userEvent.keyboard(" ");
    expect(control).toBeChecked();
  });

  it("chip reports whether it is pressed", async () => {
    function Example() {
      const [pressed, setPressed] = useState(false);
      return (
        <Chip pressed={pressed} onPressedChange={setPressed}>
          City
        </Chip>
      );
    }
    render(<Example />);
    const chip = screen.getByRole("button", { name: "City" });
    expect(chip).toHaveAttribute("aria-pressed", "false");
    await userEvent.click(chip);
    expect(chip).toHaveAttribute("aria-pressed", "true");
  });

  it("segmented control marks one option and reports the choice", async () => {
    const onChange = vi.fn();
    render(
      <Segmented
        label="Theme"
        value="light"
        onChange={onChange}
        options={[
          { value: "light", label: "Light" },
          { value: "dark", label: "Dark" },
        ]}
      />,
    );
    expect(screen.getByRole("button", { name: "Light" })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: "Dark" }));
    expect(onChange).toHaveBeenCalledWith("dark");
  });
});

describe("Tabs", () => {
  it("moves between tabs with the arrow keys", async () => {
    render(
      <Tabs defaultValue="one">
        <TabsList aria-label="Example">
          <TabsTrigger value="one">One</TabsTrigger>
          <TabsTrigger value="two">Two</TabsTrigger>
        </TabsList>
        <TabsContent value="one">First panel</TabsContent>
        <TabsContent value="two">Second panel</TabsContent>
      </Tabs>,
    );
    screen.getByRole("tab", { name: "One" }).focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "Two" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Second panel");
  });
});

describe("Sheet", () => {
  it("opens as a named dialog, closes with Escape and returns the focus", async () => {
    render(
      <Sheet>
        <SheetTrigger asChild>
          <Button>Open</Button>
        </SheetTrigger>
        <SheetContent title="Add a job">
          <Input aria-label="Job link" />
        </SheetContent>
      </Sheet>,
    );
    const opener = screen.getByRole("button", { name: "Open" });
    await userEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: "Add a job" });
    expect(dialog).toContainElement(document.activeElement as HTMLElement);

    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });
});

describe("badges and headers", () => {
  it("states the trust level in words", () => {
    render(
      <>
        <TrustBadge level="high" />
        <TrustBadge level="check" />
        <TrustBadge level="risky" />
        <Badge>Closed</Badge>
      </>,
    );
    for (const label of ["High trust", "Check first", "Risky", "Closed"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("hides a zero count and caps a large one", () => {
    const { container } = render(<CountBadge count={0} />);
    expect(container).toBeEmptyDOMElement();
    render(<CountBadge count={250} />);
    expect(screen.getByText("99+")).toBeInTheDocument();
  });

  it("renders one main heading per page header", () => {
    render(<PageHeader kicker="Kicker" title="Screen title" lead="A sentence." />);
    expect(screen.getByRole("heading", { level: 1, name: "Screen title" })).toBeInTheDocument();
  });

  it("keeps progress inside its limits", () => {
    render(<ProgressBar value={9} max={5} label="Prep done" />);
    expect(screen.getByRole("progressbar", { name: "Prep done" })).toHaveAttribute(
      "aria-valuenow",
      "5",
    );
  });
});
