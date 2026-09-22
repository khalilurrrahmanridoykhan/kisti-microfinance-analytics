import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HorizontalBars } from "./HorizontalBars";

describe("HorizontalBars", () => {
  it("keeps a short label as-is in the visible chart", () => {
    render(<HorizontalBars rows={[{ label: "Short", value: 10 }]} domainMax={20} />);
    // one in the SVG, one in the sr-only fallback table
    expect(screen.getAllByText("Short").length).toBeGreaterThanOrEqual(1);
  });

  it("shortens a label that would be clipped, but keeps the full text for screen readers", () => {
    const long = "Average loan below 5,000 or above 250,000 taka";
    render(<HorizontalBars rows={[{ label: long, value: 9, fullLabel: long }]} domainMax={20} />);
    // the accessible fallback table always carries the full text
    const table = screen.getByText("Bar chart values").closest("table")!;
    expect(within(table).getByText(long)).toBeInTheDocument();
    // the visible chart's own text must not silently render the un-truncated long string,
    // since that is exactly what gets clipped past the SVG's left edge
    expect(screen.queryByText(long, { selector: "svg text" })).not.toBeInTheDocument();
  });

  it("renders a reference line label when given one", () => {
    render(<HorizontalBars rows={[{ label: "A", value: 5 }]} domainMax={10} reference={{ value: 5, label: "Midpoint" }} />);
    expect(screen.getByText("Midpoint")).toBeInTheDocument();
  });

  it("uses the custom endLabel over the formatted value when provided", () => {
    render(<HorizontalBars rows={[{ label: "A", value: 5, endLabel: "5 of 10" }]} domainMax={10} />);
    expect(screen.getByText("5 of 10")).toBeInTheDocument();
  });
});
