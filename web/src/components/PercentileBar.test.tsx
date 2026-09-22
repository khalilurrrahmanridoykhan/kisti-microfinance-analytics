import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PercentileBar } from "./PercentileBar";

describe("PercentileBar", () => {
  it("renders an em dash for a null value instead of a misleading zero-length bar", () => {
    render(<PercentileBar value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders the rounded percentile as text, never colour alone", () => {
    render(<PercentileBar value={78.4} />);
    expect(screen.getByText("78")).toBeInTheDocument();
  });
});
