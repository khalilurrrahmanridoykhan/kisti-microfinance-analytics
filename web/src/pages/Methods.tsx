import type { AppData } from "../lib/data";
import { formatCompactTaka, formatInt, formatPercent } from "../lib/format";

const REPO = "https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics";

export function Methods({ data }: { data: AppData }) {
  const { methods, meta, sector } = data;
  const flaggedShares = sector.quality_flags.map((f) => f.loans_share_of_flagged_pct);
  const minFlagged = Math.min(...flaggedShares);
  const maxFlagged = Math.max(...flaggedShares);
  return (
    <div>
      <section className="card">
        <h2>What this dashboard shows</h2>
        <p>
          Institution-level statistics for {formatInt(meta.mfis_in_basic)} MRA-licensed microfinance institutions in
          Bangladesh, from the Microcredit Regulatory Authority's <em>Microfinance in Bangladesh (Annual Statistics)</em>,
          edition {meta.edition}, plus district populations from the Bangladesh Bureau of Statistics' Census 2022 (via the
          Humanitarian Data Exchange, CC0). Everything here is real, published data — no synthetic or loan-level records are
          used in this dashboard.
        </p>
        <p>
          <strong>{formatInt(meta.mfis_active)}</strong> of those MFIs are "active" (loans outstanding and borrowers both
          above zero) and are what the Sector Overview and MFI Benchmark pages analyse, holding{" "}
          {formatCompactTaka(meta.loan_outstanding_active_bdt)} of loans.
        </p>
      </section>

      <section className="card">
        <h2>What it cannot tell you</h2>
        <ul>
          <li>
            <strong>No per-MFI delinquency.</strong> MRA publishes portfolio-at-risk only for the whole sector, never by
            institution. The "risk ratios" in the source report are financial-structure ratios (yield, self-sufficiency,
            capital, borrowing), not measures of loan quality.
          </li>
          <li>
            <strong>No client-level or loan-level data.</strong> Every number here is an institution-level aggregate.
          </li>
          <li>
            <strong>Not every MFI reports every table.</strong> Operating cost ratios cover{" "}
            {formatInt(methods.coverage.active_with_cost_ratios)} MFIs, risk ratios{" "}
            {formatInt(methods.coverage.active_with_ratios)}, fund composition{" "}
            {formatInt(methods.coverage.active_with_funds)} — always fewer than the {formatInt(methods.coverage.mfis_active)}{" "}
            active MFIs. Each figure states its own denominator.
          </li>
          <li>Not a tool for credit, lending, supervisory or investment decisions.</li>
        </ul>
      </section>

      <section className="card">
        <h2>Size bands</h2>
        <p>MFIs are grouped by loan outstanding into five bands, used throughout the Sector Overview page:</p>
        <table>
          <thead>
            <tr>
              <th scope="col">Band</th>
              <th scope="col">Range</th>
            </tr>
          </thead>
          <tbody>
            {methods.size_bands.map((band) => (
              <tr key={band.label}>
                <td>{band.label}</td>
                <td>
                  {band.min_bdt !== null ? formatCompactTaka(band.min_bdt) : "0"} to{" "}
                  {band.max_bdt !== null ? formatCompactTaka(band.max_bdt) : "above"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2>The 24% reference line</h2>
        <p>{methods.reference_ceiling_note}</p>
      </section>

      <section className="card">
        <h2>The screening rule</h2>
        <p>{methods.screening_rule.note}</p>
      </section>

      <section className="card">
        <h2>Data quality</h2>
        <p>
          The published tables have gaps and printed inconsistencies (a handful of totals that do not equal their parts, a
          licence number printed twice, and similar). Every one of them is listed, with the page it appears on, in{" "}
          <a href={`${REPO}/blob/main/docs/extraction-notes.md`}>docs/extraction-notes.md</a>. Beyond those, the plausibility
          checks shown in the Sector Overview tab flag MFIs holding {formatPercent(minFlagged, 2)} to{" "}
          {formatPercent(maxFlagged, 2)} of loans, depending on the check — a very small share, but enough to distort an
          average, which is why medians are used throughout.
        </p>
      </section>

      <section className="card">
        <h2>Sources and how this was built</h2>
        <ul>
          <li>
            <a href={`${REPO}/blob/main/data/README.md`}>Data sources, checksums and terms</a> — every input document with
            its URL, retrieval date and licence.
          </li>
          <li>
            <a href={`${REPO}/blob/main/docs/glossary.md`}>Glossary</a> — every ratio's formula, as MRA defines it.
          </li>
          <li>
            <a href={`${REPO}/blob/main/docs/data-dictionary.md`}>Data dictionary</a> — every column in every table.
          </li>
          <li>
            <a href={`${REPO}/blob/main/RESULTS.md`}>RESULTS.md</a> — the full written analysis this dashboard is built
            from, generated by the same pipeline.
          </li>
          <li>
            <a href={REPO}>Source code</a> — Apache 2.0. <code>make analyse</code> regenerates every number;{" "}
            <code>make webdata</code> regenerates the files this page reads.
          </li>
        </ul>
        <p className="card-caption">
          Report edition {meta.edition}. Dashboard data generated {new Date(meta.generated_at).toLocaleString()}.
        </p>
      </section>
    </div>
  );
}
