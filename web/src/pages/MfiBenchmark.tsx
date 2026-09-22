import { useMemo, useState } from "react";
import { DataTable, type Column } from "../components/DataTable";
import { PercentileBar } from "../components/PercentileBar";
import type { AppData } from "../lib/data";
import { formatCompactTaka, formatInt, formatPercent } from "../lib/format";
import type { MfiRecord } from "../lib/types";

function columns(): Column<MfiRecord>[] {
  return [
    {
      key: "name",
      header: "MFI",
      render: (r) => (
        <span>
          {r.name}
          {r.flagged && (
            <span className="pill pill-flagged" style={{ marginLeft: 6 }} title="Fails a data-quality plausibility check">
              flagged
            </span>
          )}
        </span>
      ),
      sortValue: (r) => r.name,
    },
    { key: "band", header: "Size band", render: (r) => r.size_band ?? "—", sortValue: (r) => r.size_band ?? "" },
    {
      key: "loans",
      header: "Loan outstanding",
      render: (r) => formatCompactTaka(r.loan_outstanding_bdt),
      align: "right",
      sortValue: (r) => r.loan_outstanding_bdt,
    },
    {
      key: "borrowers",
      header: "Borrowers",
      render: (r) => formatInt(r.borrowers_total),
      align: "right",
      sortValue: (r) => r.borrowers_total,
    },
    {
      key: "avg_loan",
      header: "Avg loan",
      render: (r) => formatCompactTaka(r.avg_loan_size_bdt),
      align: "right",
      sortValue: (r) => r.avg_loan_size_bdt,
    },
    {
      key: "yield",
      header: "Yield (percentile in band)",
      render: (r) => (
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span>{r.portfolio_yield !== null ? formatPercent(r.portfolio_yield) : "—"}</span>
          <PercentileBar value={r.yield_percentile_in_band} />
        </span>
      ),
      align: "right",
      sortValue: (r) => r.portfolio_yield ?? -1,
    },
    {
      key: "oss",
      header: "OSS (percentile in band)",
      render: (r) => (
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span>{r.operating_self_sufficiency !== null ? formatPercent(r.operating_self_sufficiency) : "—"}</span>
          <PercentileBar value={r.oss_percentile_in_band} />
        </span>
      ),
      align: "right",
      sortValue: (r) => r.operating_self_sufficiency ?? -1,
    },
    {
      key: "cost",
      header: "Op. cost / 100 taka",
      render: (r) => (r.total_operating_cost_ratio !== null ? r.total_operating_cost_ratio.toFixed(1) : "—"),
      align: "right",
      sortValue: (r) => r.total_operating_cost_ratio ?? -1,
    },
    {
      key: "savings_share",
      header: "Savings / funds",
      render: (r) => (r.savings_share_of_funds_pct !== null ? formatPercent(r.savings_share_of_funds_pct) : "—"),
      align: "right",
      sortValue: (r) => r.savings_share_of_funds_pct ?? -1,
    },
  ];
}

export function MfiBenchmark({ data }: { data: AppData }) {
  const [band, setBand] = useState("all");
  const cols = useMemo(() => columns(), []);
  const bands = useMemo(() => [...new Set(data.mfis.map((m) => m.size_band).filter((b): b is string => !!b))], [data.mfis]);
  const rows = useMemo(() => (band === "all" ? data.mfis : data.mfis.filter((m) => m.size_band === band)), [data.mfis, band]);

  return (
    <div className="card">
      <h2>MFI benchmark</h2>
      <p>
        All {data.mfis.length} active MFIs. Percentile is the MFI's rank against others in the same size band (100 = highest in
        the band). Where a ratio is blank, that MFI does not appear in the underlying MRA table — see{" "}
        <a href="https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics/blob/main/docs/extraction-notes.md">
          docs/extraction-notes.md
        </a>
        .
      </p>
      <DataTable
        columns={cols}
        rows={rows}
        getRowKey={(r) => r.license_no}
        caption="MFI benchmark table"
        searchPlaceholder="Search by name…"
        searchPredicate={(row, query) => row.name.toLowerCase().includes(query.toLowerCase()) || String(row.license_no).includes(query)}
        initialSort={{ key: "loans", direction: "desc" }}
        pageSize={25}
        extraControls={
          <select aria-label="Filter by size band" value={band} onChange={(event) => setBand(event.target.value)}>
            <option value="all">All size bands</option>
            {bands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        }
      />
    </div>
  );
}
