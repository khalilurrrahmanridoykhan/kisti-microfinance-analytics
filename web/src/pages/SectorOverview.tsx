import { useMemo } from "react";
import { HorizontalBars } from "../components/HorizontalBars";
import { RangeDots } from "../components/RangeDots";
import { Histogram } from "../components/Histogram";
import { ScatterPlot } from "../components/ScatterPlot";
import { StackedBars, type StackedSeries } from "../components/StackedBars";
import { LorenzCurve } from "../components/LorenzCurve";
import { KpiTile } from "../components/KpiTile";
import { SectionCard } from "../components/SectionCard";
import { DistrictMap } from "../components/DistrictMap";
import { Icon, type IconName } from "../components/Icon";
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
  const { sector, mfis, methods, districts } = data;
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

  const loanConcentration = sector.concentration.find((c) => c.measure === "Loan outstanding")!;
  const lowest = districts.reduce((a, b) => (b.borrowers_per_1000 < a.borrowers_per_1000 ? b : a));
  const highest = districts.reduce((a, b) => (b.borrowers_per_1000 > a.borrowers_per_1000 ? b : a));
  const findings: { icon: IconName; value: string; text: string; link: string; href: string }[] = [
    {
      icon: "pie",
      value: formatPercent(loanConcentration.top4_share_pct, 0),
      text: `of all loans are held by just four MFIs: ${sector.largest_mfis.map((m) => m.name).join(", ")}.`,
      link: "Concentration",
      href: "#concentration",
    },
    {
      icon: "alert",
      value: formatPercent(sector.oss_overall.below_100_share_pct, 0),
      text: `of MFIs do not cover their operating costs, but together they hold only ${formatPercent(sector.oss_overall.share_of_loans_in_below_100_pct)} of loans.`,
      link: "Sustainability",
      href: "#sustainability",
    },
    {
      icon: "scale",
      value: (sector.efficiency_correlations.find((e) => e.measure === "op_cost_ratio")?.spearman_with_size ?? 0).toFixed(2),
      text: "rank correlation of size with cost per taka lent: larger MFIs do not run more cheaply.",
      link: "Efficiency",
      href: "#efficiency",
    },
    {
      icon: "map",
      value: `${lowest.borrowers_per_1000.toFixed(0)}–${highest.borrowers_per_1000.toFixed(0)}`,
      text: `MFI borrowers per 1,000 people, from ${lowest.district} to ${highest.district}.`,
      link: "Open the map",
      href: "#map",
    },
  ];
  const coverage = [
    { label: "Operating cost ratios", n: sector.coverage.active_with_cost_ratios, share: sector.coverage.loans_share_with_cost_ratios_pct },
    { label: "Risk ratios (yield, OSS, ROA)", n: sector.coverage.active_with_ratios, share: sector.coverage.loans_share_with_ratios_pct },
    { label: "Fund composition", n: sector.coverage.active_with_funds, share: sector.coverage.loans_share_with_funds_pct },
  ];

  return (
    <div>
      <div className="kpi-grid">
        <KpiTile
          label="Active MFIs"
          icon="institution"
          value={formatInt(sector.kpis.n_mfis)}
          detail={`of ${formatInt(sector.coverage.mfis_in_basic)} licensed`}
          title="Loans outstanding and borrowers both above zero"
        />
        <KpiTile label="Loan outstanding"
          icon="banknote" value={formatCompactTaka(sector.kpis.loan_outstanding_bdt)} detail="June 2025" />
        <KpiTile label="Borrowers"
          icon="users" value={formatInt(sector.kpis.borrowers_total)} detail="Active loan accounts" />
        <KpiTile label="Members (clients)"
          icon="member" value={formatInt(sector.kpis.clients_total)} detail="Enrolled members" />
        <KpiTile label="Savings"
          icon="savings" value={formatCompactTaka(sector.kpis.savings_bdt)} detail="Clients' deposits" />
        <KpiTile label="Branches"
          icon="pin" value={formatInt(sector.kpis.branches_total)} detail="Across all MFIs" />
      </div>

      <section className="findings" aria-label="Key findings">
        {findings.map((f) => (
          <a key={f.href} className="finding" href={f.href}>
            <span className="finding-icon">
              <Icon name={f.icon} size={20} />
            </span>
            <span className="finding-value">{f.value}</span>
            <span className="finding-text">{f.text}</span>
            <span className="finding-link">
              {f.link} <Icon name="arrow" size={14} />
            </span>
          </a>
        ))}
      </section>

      <SectionCard
        id="map"
        eyebrow="Interactive map"
        title="Where microfinance reaches"
        lead="Every district of Bangladesh, shaded by MFI coverage. Pick a division to zoom in, or a district to see its details."
        className="card-feature"
      >
        <DistrictMap districts={districts} />
      </SectionCard>

      <SectionCard
        title="Who is counted"
        lead={
          <>
            The Basic table lists {formatInt(sector.coverage.mfis_in_basic)} MFIs; {formatInt(sector.coverage.mfis_active)} are
            "active" (loans and borrowers both above zero) and analysed here. The ratio tables cover fewer of them:
          </>
        }
      >
        <ul className="coverage-list">
          {coverage.map((c) => (
            <li key={c.label}>
              <div className="coverage-row">
                <span className="coverage-label">{c.label}</span>
                <span className="coverage-value">
                  {formatInt(c.n)} MFIs ({formatPercent(c.share)} of loans)
                </span>
              </div>
              <div className="meter" aria-hidden="true">
                <div className="meter-fill" style={{ width: `${Math.min(100, c.share)}%` }} />
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard index={1} id="concentration" title="Concentration" lead="How unevenly loans, borrowers and savings are spread across MFIs.">
        <div className="split">
          <div className="split-chart">
            <LorenzCurve points={sector.lorenz} top4SharePct={loanConcentration.top4_share_pct} gini={loanConcentration.gini} />
          </div>
          <div>
            <DataTable
              columns={CONCENTRATION_COLUMNS}
              rows={sector.concentration}
              getRowKey={(r) => r.measure}
              caption="Concentration by measure"
              pageSize={10}
            />
            <p className="card-caption">
              {sector.largest_mfis.map((m) => m.name).join(", ")} hold {formatPercent(sector.concentration[0].top4_share_pct)} of
              loan outstanding. June 2025, {sector.kpis.n_mfis} active MFIs.
            </p>
          </div>
        </div>
      </SectionCard>

      <div className="card-grid">
        <SectionCard index={2} id="sustainability" title="Sustainability" lead="Share of MFIs not covering their operating costs.">
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
        </SectionCard>
        <SectionCard index={3} id="efficiency" title="Efficiency and scale" lead="Operating cost per 100 taka of loans, by size band.">
          <RangeDots rows={costRange.map((r) => ({ ...r, label: r.label }))} domainMin={0} domainMax={30} unit="" formatValue={(v) => v.toFixed(1)} />
          <p className="card-caption">
            Operating cost per 100 taka of loans, by size band (median and middle half of MFIs, computed from the per-MFI
            export). Larger MFIs do not lend more cheaply per taka: the rank correlation with size is{" "}
            {sector.efficiency_correlations.find((e) => e.measure === "op_cost_ratio")?.spearman_with_size.toFixed(2)}.
          </p>
        </SectionCard>
      </div>

      <SectionCard index={4} id="pricing" title="Pricing" lead="Portfolio yield across MFIs, and how it relates to self-sufficiency.">
        <div className="split split-even">
          <div>
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
          </div>
          <div>
            <ScatterPlot
              points={scatterPoints}
              xDomain={[0, 40]}
              yDomain={[40, 250]}
              xLabel="Portfolio yield, %"
              yLabel="Operating self-sufficiency, %"
              referenceY={{ value: 100, label: "Costs just covered" }}
            />
            <p className="card-caption">One point per MFI; hover for its name. June 2025.</p>
          </div>
        </div>
      </SectionCard>

      <SectionCard index={5} id="funding" title="Funding mix" lead="Where MFIs' funds come from, by size band.">
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
      </SectionCard>

      <div className="card-grid">
        <SectionCard index={6} id="outreach" title="Outreach" lead="Average loan per borrower, by size band.">
          <RangeDots rows={loanSizeRange} domainMin={0} domainMax={80} unit="K taka" formatValue={(v) => v.toFixed(0)} />
          <p className="card-caption">
            Average loan per borrower, thousand taka, by size band. Sector-wide average{" "}
            {formatCompactTaka(sector.outreach_sector.avg_loan_size_bdt)} per borrower; typical MFI's median{" "}
            {formatCompactTaka(sector.outreach_typical.median_avg_loan_size_bdt)}. Women are{" "}
            {formatPercent(sector.outreach_sector.female_client_share_pct)} of clients.
          </p>
        </SectionCard>
        <SectionCard index={7} id="quality" title="Data quality" lead="MFIs failing each plausibility check.">
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
        </SectionCard>
      </div>

      <SectionCard index={8} id="peers" title="Peer groups and a screening rule">
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
      </SectionCard>
    </div>
  );
}
