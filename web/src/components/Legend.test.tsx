import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Legend } from "./Legend";

describe("Legend", () => {
  it("renders nothing for fewer than two entries (a single series needs no legend)", () => {
    const { container } = render(<Legend entries={[{ label: "Only one", color: "red" }]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders every entry for two or more series", () => {
    render(
      <Legend
        entries={[
          { label: "First", color: "red" },
          { label: "Second", color: "blue" },
        ]}
      />,
    );
    expect(screen.getByText("First")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Legend" })).toBeInTheDocument();
  });
});
