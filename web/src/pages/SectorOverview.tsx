import { useMemo } from "react";
import { HorizontalBars } from "../components/HorizontalBars";
import { RangeDots } from "../components/RangeDots";
import { Histogram } from "../components/Histogram";
import { ScatterPlot } from "../components/ScatterPlot";
import { StackedBars, type StackedSeries } from "../components/StackedBars";
import { LorenzCurve } from "../components/LorenzCurve";
import { KpiTile } from "../components/KpiTile";
import { DataTable, type Column } from "../components/DataTable";
import type { AppData } from "../lib/data";
import { bandOrder, rangeByBand } from "../lib/bands";
import { formatCompactTaka, formatInt, formatPercent } from "../lib/format";
import type { ConcentrationRow, FundingChangeRow } from "../lib/types";

// The full check text (from kisti.analysis.quality.RULES) is long and would be clipped in the
// bar chart's fixed label column, so a short label is shown there and the full text stays
// available on hover and to screen readers via BarRow.fullLabel.
const QUALITY_CHECK_SHORT_LABELS: Record<string, string> = {
  "Portfolio yield outside 3% to 40%": "Yield out of range",
  "OSS outside 40% to 250%": "OSS out of range",
  "ROA outside -25% to 25%": "ROA out of range",
  "Operating cost above 50 per 100 taka of loans": "Very high op. cost",
  "More than 1,000 borrowers per employee": "Borrowers/employee",
  "Average loan below 5,000 or above 250,000 taka": "Avg loan out of range",
};

const FUNDING_SERIES: StackedSeries[] = [
  { key: "clients_savings", label: "Clients' savings", color: "var(--series-1)" },
  { key: "bank_loans", label: "Commercial-bank loans", color: "var(--series-2)" },
  { key: "pksf_loans", label: "PKSF loans", color: "var(--series-3)" },
  { key: "other_borrowing", label: "Other borrowing", color: "var(--series-4)" },
  { key: "donor_funds", label: "Donors' funds", color: "var(--series-5)" },
  { key: "surplus_and_other", label: "Surplus and other funds", color: "var(--series-6)" },
];

const CONCENTRATION_COLUMNS: Column<ConcentrationRow>[] = [
  { key: "measure", header: "Measure", render: (r) => r.measure },
  { key: "n", header: "MFIs", render: (r) => formatInt(r.n_mfis), align: "right", sortValue: (r) => r.n_mfis },
  { key: "top1", header: "Top 1", render: (r) => formatPercent(r.top1_share_pct), align: "right", sortValue: (r) => r.top1_share_pct },
  { key: "top4", header: "Top 4", render: (r) => formatPercent(r.top4_share_pct), align: "right", sortValue: (r) => r.top4_share_pct },
  { key: "top10", header: "Top 10", render: (r) => formatPercent(r.top10_share_pct), align: "right", sortValue: (r) => r.top10_share_pct },
  { key: "gini", header: "Gini", render: (r) => r.gini.toFixed(2), align: "right", sortValue: (r) => r.gini },
];

const FUNDING_CHANGE_COLUMNS: Column<FundingChangeRow>[] = [
  { key: "source", header: "Source of funds", render: (r) => r.source },
  {
    key: "share25",
    header: "Share Jun 2025",
    render: (r) => formatPercent(r.share_2025_06_pct),
    align: "right",
    sortValue: (r) => r.share_2025_06_pct,
  },
  {
    key: "change",
    header: "Change since Jun 2024",
    render: (r) => `${r.change_pp > 0 ? "+" : ""}${r.change_pp.toFixed(1)} pp`,
    align: "right",
    sortValue: (r) => r.change_pp,
  },
];

export function SectorOverview({ data }: { data: AppData }) {
  const { sector, mfis, methods } = data;
  const order = useMemo(() => bandOrder(methods.size_bands).slice().reverse(), [methods]);
  const costRange = useMemo(() => rangeByBand(mfis, order, (m) => m.total_operating_cost_ratio), [mfis, order]);
  const loanSizeRange = useMemo(() => rangeByBand(mfis, order, (m) => m.avg_loan_size_bdt / 1000), [mfis, order]);
  const yieldValues = useMemo(() => mfis.filter((m) => m.has_ratios).map((m) => m.portfolio_yield as number), [mfis]);
  const scatterPoints = useMemo(
    () =>
      mfis
        .filter((m) => m.has_ratios && (m.portfolio_yield as number) <= 40)
        .map((m) => ({ x: m.portfolio_yield as number, y: m.operating_self_sufficiency as number, label: m.name })),
    [mfis],
  );

  return (
    <div>
      <div className="kpi-grid">
        <KpiTile label="Active MFIs" value={formatInt(sector.kpis.n_mfis)} title="Loans outstanding and borrowers both above zero" />
        <KpiTile label="Loan outstanding" value={formatCompactTaka(sector.kpis.loan_outstanding_bdt)} />
        <KpiTile label="Borrowers" value={formatInt(sector.kpis.borrowers_total)} />
        <KpiTile label="Members (clients)" value={formatInt(sector.kpis.clients_total)} />
        <KpiTile label="Savings" value={formatCompactTaka(sector.kpis.savings_bdt)} />
        <KpiTile label="Branches" value={formatInt(sector.kpis.branches_total)} />
      </div>

      <section className="card">
        <h2>Who is counted</h2>
        <p>
          The Basic table lists {formatInt(sector.coverage.mfis_in_basic)} MFIs; {formatInt(sector.coverage.mfis_active)} are
          "active" (loans and borrowers both above zero) and analysed here. The ratio tables cover fewer of them:
        </p>
        <ul>
          <li>
            Operating cost ratios: {formatInt(sector.coverage.active_with_cost_ratios)} MFIs (
            {formatPercent(sector.coverage.loans_share_with_cost_ratios_pct)} of loans)
          </li>
          <li>
            Risk ratios (yield, OSS, ROA): {formatInt(sector.coverage.active_with_ratios)} MFIs (
            {formatPercent(sector.coverage.loans_share_with_ratios_pct)} of loans)
          </li>
          <li>
            Fund composition: {formatInt(sector.coverage.active_with_funds)} MFIs ({formatPercent(sector.coverage.loans_share_with_funds_pct)} of loans)
          </li>
        </ul>
      </section>

      <section className="card">
        <h2>1. Concentration</h2>
        <LorenzCurve
          points={sector.lorenz}
          top4SharePct={sector.concentration.find((c) => c.measure === "Loan outstanding")!.top4_share_pct}
          gini={sector.concentration.find((c) => c.measure === "Loan outstanding")!.gini}
        />
        <DataTable
          columns={CONCENTRATION_COLUMNS}
          rows={sector.concentration}
          getRowKey={(r) => r.measure}
          caption="Concentration by measure"
          pageSize={10}
        />
        <p className="card-caption">
          {sector.largest_mfis.map((m) => m.name).join(", ")} hold {formatPercent(sector.concentration[0].top4_share_pct)} of loan
          outstanding. June 2025, {sector.kpis.n_mfis} active MFIs.
        </p>
      </section>

      <section className="card">
        <h2>2. Sustainability</h2>
        <HorizontalBars
          rows={sector.oss_by_band.map((b) => ({
            label: b.size_band,
            value: b.below_100_share_pct,
            endLabel: `${b.below_100_share_pct.toFixed(0)}% (${b.below_100_count} of ${b.n_mfis})`,
          }))}
          domainMax={65}
          valueSuffix="%"
        />
        <p className="card-caption">
          Share of MFIs with operating self-sufficiency (OSS) below 100%, by size band. Below-100 MFIs hold only{" "}
          {formatPercent(sector.oss_overall.share_of_loans_in_below_100_pct)} of loans. Median OSS is{" "}
          {sector.oss_overall.oss_median.toFixed(1)}%; median ROA {sector.oss_overall.roa_median.toFixed(1)}%.
        </p>
      </section>

      <section className="card">
        <h2>3. Efficiency and scale</h2>
        <RangeDots rows={costRange.map((r) => ({ ...r, label: r.label }))} domainMin={0} domainMax={30} unit="" formatValue={(v) => v.toFixed(1)} />
        <p className="card-caption">
          Operating cost per 100 taka of loans, by size band (median and middle half of MFIs, computed from the per-MFI
          export). Larger MFIs do not lend more cheaply per taka: the rank correlation with size is{" "}
          {sector.efficiency_correlations.find((e) => e.measure === "op_cost_ratio")?.spearman_with_size.toFixed(2)}.
        </p>
      </section>

      <section className="card">
        <h2>4. Pricing</h2>
        <Histogram
          values={yieldValues}
          binWidth={1}
          domainMax={40}
          reference={{ value: sector.reference_ceiling_pct, label: `${sector.reference_ceiling_pct}%: press-reported reference (unverified)` }}
          xLabel="Portfolio yield, % of average loan outstanding (values above 40% clipped to 40)"
        />
        <p className="card-caption">
          Median yield {sector.yield_distribution.median.toFixed(1)}%; {sector.yield_distribution.above_reference_count} MFIs above the
          reference line. Yield is service-charge income over average loans, so it includes fees — it is not the
          declining-balance rate a client pays, and this cannot show whether any MFI breaches a limit.
        </p>
        <ScatterPlot
          points={scatterPoints}
          xDomain={[0, 40]}
          yDomain={[40, 250]}
          xLabel="Portfolio yield, %"
          yLabel="Operating self-sufficiency, %"
          referenceY={{ value: 100, label: "Costs just covered" }}
        />
        <p className="card-caption">One point per MFI; hover for its name. June 2025.</p>
      </section>

      <section className="card">
        <h2>5. Funding mix</h2>
        <StackedBars
          series={FUNDING_SERIES}
          rows={sector.funding_by_band.map((b) => ({
            label: b.size_band,
            values: {
              clients_savings: b.clients_savings_share_pct,
              bank_loans: b.bank_loans_share_pct,
              pksf_loans: b.pksf_loans_share_pct,
              other_borrowing: b.other_borrowing_share_pct,
              donor_funds: b.donor_funds_share_pct,
              surplus_and_other: b.surplus_and_other_share_pct,
            },
          }))}
        />
        <DataTable
          columns={FUNDING_CHANGE_COLUMNS}
          rows={sector.funding_change}
          getRowKey={(r) => r.source}
          caption="Funding mix change, June 2024 to June 2025"
          pageSize={10}
        />
      </section>

      <section className="card">
        <h2>6. Outreach</h2>
        <RangeDots rows={loanSizeRange} domainMin={0} domainMax={80} unit="K taka" formatValue={(v) => v.toFixed(0)} />
        <p className="card-caption">
          Average loan per borrower, thousand taka, by size band. Sector-wide average{" "}
          {formatCompactTaka(sector.outreach_sector.avg_loan_size_bdt)} per borrower; typical MFI's median{" "}
          {formatCompactTaka(sector.outreach_typical.median_avg_loan_size_bdt)}. Women are{" "}
          {formatPercent(sector.outreach_sector.female_client_share_pct)} of clients.
        </p>
      </section>

      <section className="card">
        <h2>7. Data quality</h2>
        <HorizontalBars
          rows={sector.quality_flags.map((f) => ({
            label: QUALITY_CHECK_SHORT_LABELS[f.check] ?? f.check,
            fullLabel: f.check,
            value: f.mfis_flagged,
            endLabel: `${f.mfis_flagged} of ${f.mfis_checked}`,
          }))}
          domainMax={Math.max(...sector.quality_flags.map((f) => f.mfis_flagged), 5)}
        />
        <p className="card-caption">
          Plausibility checks, counts only — no institution is named. Full list of published inconsistencies in{" "}
          <a href="https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics/blob/main/docs/extraction-notes.md">
            docs/extraction-notes.md
          </a>
          .
        </p>
      </section>

      <section className="card">
        <h2>8. Peer groups and a screening rule</h2>
        <p>
          K-means on seven standardised ratios gives {sector.peer_groups.length} groups (best silhouette{" "}
          {Math.max(...sector.peer_silhouette.map((s) => s.silhouette)).toFixed(2)} — a low score means the structure is weak;
          these are a summary, not natural clusters).
        </p>
        <DataTable
          columns={[
            { key: "group", header: "Group", render: (r) => `Group ${r.group}`, sortValue: (r) => r.group },
            { key: "n", header: "MFIs", render: (r) => formatInt(r.n_mfis), align: "right", sortValue: (r) => r.n_mfis },
            {
              key: "share",
              header: "% of loans",
              render: (r) => formatPercent(r.loans_share_pct),
              align: "right",
              sortValue: (r) => r.loans_share_pct,
            },
            {
              key: "oss",
              header: "Median OSS",
              render: (r) => formatPercent(r.oss_median),
              align: "right",
              sortValue: (r) => r.oss_median,
            },
          ]}
          rows={sector.peer_groups}
          getRowKey={(r) => r.group}
          caption="Peer groups"
          pageSize={10}
        />
        <p className="card-caption">
          Screening rule (OSS below 100% and borrowing at or above 50% of loans): {sector.screening.flagged} of{" "}
          {sector.screening.n_mfis} MFIs ({formatPercent(sector.screening.flagged_share_pct)}), holding{" "}
          {formatPercent(sector.screening.flagged_loans_share_pct)} of loans. A filter on financial-structure ratios, not a
          measure of delinquency; reported as a count only, not a named list.
        </p>
      </section>
    </div>
  );
}
