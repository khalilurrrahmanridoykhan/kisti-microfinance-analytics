import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DistrictRecord } from "../lib/types";
import { DistrictMap } from "./DistrictMap";

function district(name: string, division: string, borrowersPer1000: number): DistrictRecord {
  return {
    division,
    district: name,
    population: 1_000_000,
    households: 250_000,
    branches: 100,
    members: 300_000,
    borrowers: borrowersPer1000 * 1000,
    loan_outstanding_bdt: 1e10,
    members_per_1000: 300,
    borrowers_per_1000: borrowersPer1000,
    loan_outstanding_per_person_bdt: 10_000,
    avg_loan_size_bdt: 50_000,
    branches_per_100k: 10,
    financial_account_pct: 30,
    mobile_banking_pct: 40,
  };
}

const DISTRICTS = [district("Cumilla", "Chattogram", 474), district("Sylhet", "Sylhet", 98), district("Dhaka", "Dhaka", 200)];
const GEO = {
  source: "test",
  license: "CC BY 3.0 IGO",
  viewBox: [0, 0, 100, 100],
  districts: DISTRICTS.map((d, i) => ({ district: d.district, path: `M${i * 10},0L${i * 10 + 9},0L${i * 10 + 9},9Z`, label: [i * 10 + 5, 5] })),
};

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(GEO) }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DistrictMap", () => {
  it("draws one focusable shape per district, labelled with its value", async () => {
    render(<DistrictMap districts={DISTRICTS} />);
    expect(await screen.findByRole("button", { name: "Cumilla, Chattogram: 474" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sylhet, Sylhet: 98" })).toBeInTheDocument();
  });

  it("shows the Bangladesh figure until a district is selected, then that district's detail", async () => {
    const user = userEvent.setup();
    render(<DistrictMap districts={DISTRICTS} />);
    // (474 + 98 + 200) thousand borrowers over 3 million people.
    expect(screen.getByText("Bangladesh")).toBeInTheDocument();
    expect(screen.getByText("257")).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: "Cumilla, Chattogram: 474" }));
    await user.unhover(screen.getByRole("button", { name: "Cumilla, Chattogram: 474" }));
    expect(screen.getByText("Chattogram division")).toBeInTheDocument();
    expect(screen.getByText(/rank 1 of 3/)).toBeInTheDocument();
  });

  it("switches metric and relabels the shapes", async () => {
    const user = userEvent.setup();
    render(<DistrictMap districts={DISTRICTS} />);
    await screen.findByRole("button", { name: "Cumilla, Chattogram: 474" });
    await user.click(screen.getByRole("button", { name: "Account %" }));
    expect(screen.getByRole("button", { name: "Cumilla, Chattogram: 30%" })).toBeInTheDocument();
  });

  it("explains the failure and points to the table when the map cannot load", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404 }));
    render(<DistrictMap districts={DISTRICTS} />);
    expect(await screen.findByText(/could not be loaded \(HTTP 404\)/)).toBeInTheDocument();
  });
});
