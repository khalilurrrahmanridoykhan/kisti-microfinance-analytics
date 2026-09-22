import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DataTable, type Column } from "./DataTable";

interface Row {
  id: number;
  name: string;
  value: number;
}

const ROWS: Row[] = [
  { id: 1, name: "Alpha", value: 30 },
  { id: 2, name: "Beta", value: 10 },
  { id: 3, name: "Gamma", value: 20 },
];

const COLUMNS: Column<Row>[] = [
  { key: "name", header: "Name", render: (r) => r.name, sortValue: (r) => r.name },
  { key: "value", header: "Value", render: (r) => String(r.value), align: "right", sortValue: (r) => r.value },
];

function renderTable(overrides: Partial<React.ComponentProps<typeof DataTable<Row>>> = {}) {
  return render(
    <DataTable columns={COLUMNS} rows={ROWS} getRowKey={(r) => r.id} caption="Test table" pageSize={2} {...overrides} />,
  );
}

function bodyRowNames() {
  const rows = screen.getAllByRole("row").slice(1); // drop the header row
  return rows.map((row) => within(row).getAllByRole("cell")[0].textContent);
}

describe("DataTable", () => {
  it("renders rows in the initial sort order (default: first column, descending)", () => {
    renderTable({ pageSize: 10 });
    expect(bodyRowNames()).toEqual(["Gamma", "Beta", "Alpha"]);
  });

  it("sorts ascending then descending when a header is clicked", async () => {
    const user = userEvent.setup();
    renderTable({ pageSize: 10, initialSort: { key: "value", direction: "desc" } });
    expect(bodyRowNames()).toEqual(["Alpha", "Gamma", "Beta"]); // 30, 20, 10

    await user.click(screen.getByRole("button", { name: /Value/ }));
    expect(bodyRowNames()).toEqual(["Beta", "Gamma", "Alpha"]); // ascending: 10, 20, 30

    await user.click(screen.getByRole("button", { name: /Value/ }));
    expect(bodyRowNames()).toEqual(["Alpha", "Gamma", "Beta"]); // back to descending
  });

  it("announces sort direction via aria-sort, defaulting to the first column descending", () => {
    renderTable({ pageSize: 10 });
    expect(screen.getByRole("columnheader", { name: /Name/ })).toHaveAttribute("aria-sort", "descending");
    expect(screen.getByRole("columnheader", { name: /Value/ })).toHaveAttribute("aria-sort", "none");
  });

  it("switches which column is announced as sorted when a different header is clicked", async () => {
    const user = userEvent.setup();
    renderTable({ pageSize: 10, initialSort: { key: "value", direction: "desc" } });
    await user.click(screen.getByRole("button", { name: /Name/ }));
    expect(screen.getByRole("columnheader", { name: /Name/ })).toHaveAttribute("aria-sort", "descending");
    expect(screen.getByRole("columnheader", { name: /Value/ })).toHaveAttribute("aria-sort", "none");
  });

  it("filters rows with the search predicate", async () => {
    const user = userEvent.setup();
    renderTable({
      pageSize: 10,
      searchPlaceholder: "Search",
      searchPredicate: (row, query) => row.name.toLowerCase().includes(query.toLowerCase()),
    });
    await user.type(screen.getByRole("searchbox", { name: "Search" }), "bet");
    expect(bodyRowNames()).toEqual(["Beta"]);
    expect(screen.getByText("1 of 3 rows")).toBeInTheDocument();
  });

  it("shows a no-match message instead of an empty table", async () => {
    const user = userEvent.setup();
    renderTable({ searchPlaceholder: "Search", searchPredicate: (row, query) => row.name.includes(query) });
    await user.type(screen.getByRole("searchbox"), "zzz");
    expect(screen.getByText("No rows match.")).toBeInTheDocument();
  });

  it("paginates and disables Previous on the first page", async () => {
    const user = userEvent.setup();
    renderTable({ pageSize: 2, initialSort: { key: "value", direction: "desc" } });
    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(bodyRowNames()).toEqual(["Alpha", "Gamma"]);

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Page 2 of 2")).toBeInTheDocument();
    expect(bodyRowNames()).toEqual(["Beta"]);
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("resets to the first page when the search query changes", async () => {
    const user = userEvent.setup();
    renderTable({ pageSize: 1, searchPlaceholder: "Search", searchPredicate: () => true });
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Page 2 of 3")).toBeInTheDocument();
    await user.type(screen.getByRole("searchbox"), "a");
    expect(screen.getByText(/Page 1 of/)).toBeInTheDocument();
  });
});
