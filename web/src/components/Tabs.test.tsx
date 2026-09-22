import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { TabPanel, Tabs, type TabDef } from "./Tabs";

const TABS: TabDef[] = [
  { id: "a", label: "Tab A" },
  { id: "b", label: "Tab B" },
  { id: "c", label: "Tab C" },
];

function Harness() {
  const [active, setActive] = useState("a");
  return (
    <div>
      <Tabs tabs={TABS} active={active} onChange={setActive} />
      <TabPanel id="a" active={active}>
        Panel A
      </TabPanel>
      <TabPanel id="b" active={active}>
        Panel B
      </TabPanel>
      <TabPanel id="c" active={active}>
        Panel C
      </TabPanel>
    </div>
  );
}

describe("Tabs", () => {
  it("shows only the active panel and marks the matching tab selected", () => {
    render(<Harness />);
    expect(screen.getByText("Panel A")).toBeInTheDocument();
    expect(screen.queryByText("Panel B")).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Tab A" })).toHaveAttribute("aria-selected", "true");
  });

  it("switches panels on click", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByRole("tab", { name: "Tab B" }));
    expect(screen.getByText("Panel B")).toBeInTheDocument();
    expect(screen.queryByText("Panel A")).not.toBeInTheDocument();
  });

  it("moves focus and selection with the arrow keys, wrapping at the ends", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    screen.getByRole("tab", { name: "Tab A" }).focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByText("Panel B")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Tab B" })).toHaveFocus();
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByText("Panel A")).toBeInTheDocument();
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByText("Panel C")).toBeInTheDocument(); // wraps to the last tab
  });

  it("only the active tab is in the tab order (roving tabindex)", () => {
    render(<Harness />);
    expect(screen.getByRole("tab", { name: "Tab A" })).toHaveAttribute("tabIndex", "0");
    expect(screen.getByRole("tab", { name: "Tab B" })).toHaveAttribute("tabIndex", "-1");
  });
});
