import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import type { AppData } from "./lib/data";

// App only orchestrates loading, error display and which page is mounted for the active tab;
// each page's own rendering is covered where it is defined. Mocking the pages and the loader
// here keeps this test from having to maintain a full, schema-valid fixture of every dataset.
vi.mock("./lib/data", () => ({ loadAppData: vi.fn() }));
vi.mock("./pages/SectorOverview", () => ({ SectorOverview: () => <div>Sector page</div> }));
vi.mock("./pages/MfiBenchmark", () => ({ MfiBenchmark: () => <div>MFI page</div> }));
vi.mock("./pages/Districts", () => ({ Districts: () => <div>Districts page</div> }));
vi.mock("./pages/Methods", () => ({ Methods: () => <div>Methods page</div> }));

import { loadAppData } from "./lib/data";

const STUB = {} as AppData;

beforeEach(() => {
  vi.mocked(loadAppData).mockReset();
});

describe("App", () => {
  it("shows a loading banner, then the first tab once data resolves", async () => {
    vi.mocked(loadAppData).mockResolvedValue(STUB);
    render(<App />);
    expect(screen.getByText(/Loading the dashboard data/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Sector page")).toBeInTheDocument());
    expect(screen.queryByText(/Loading the dashboard data/)).not.toBeInTheDocument();
  });

  it("shows an error banner with the failure message when loading fails", async () => {
    vi.mocked(loadAppData).mockRejectedValue(new Error("boom: schema mismatch"));
    render(<App />);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("boom: schema mismatch");
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("switches the mounted page when a different tab is clicked", async () => {
    vi.mocked(loadAppData).mockResolvedValue(STUB);
    const user = userEvent.setup();
    render(<App />);
    await waitFor(() => expect(screen.getByText("Sector page")).toBeInTheDocument());

    await user.click(screen.getByRole("tab", { name: "MFI benchmark" }));
    expect(screen.getByText("MFI page")).toBeInTheDocument();
    expect(screen.queryByText("Sector page")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "District coverage" }));
    expect(screen.getByText("Districts page")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Methods & limits" }));
    expect(screen.getByText("Methods page")).toBeInTheDocument();
  });

  it("always renders the not-for-decisions footer", async () => {
    vi.mocked(loadAppData).mockResolvedValue(STUB);
    render(<App />);
    expect(screen.getByText(/not for credit, lending, supervisory or investment decisions/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Sector page")).toBeInTheDocument());
  });
});
