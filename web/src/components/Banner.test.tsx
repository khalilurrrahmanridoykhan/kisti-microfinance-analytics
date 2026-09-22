import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Banner } from "./Banner";

describe("Banner", () => {
  it("uses role=alert for an error so assistive tech announces it immediately", () => {
    render(<Banner kind="error">Something failed</Banner>);
    expect(screen.getByRole("alert")).toHaveTextContent("Something failed");
  });

  it("uses role=status for an info banner (polite, not interrupting)", () => {
    render(<Banner kind="info">Loading…</Banner>);
    expect(screen.getByRole("status")).toHaveTextContent("Loading…");
  });
});
