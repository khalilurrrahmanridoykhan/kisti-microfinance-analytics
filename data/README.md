# Data

Two layers, kept in separate folders and never mixed in one table or chart.

| Folder | Layer | Status |
|---|---|---|
| `data/real/raw/` | Source PDFs fetched from the publisher (not committed) | Fetched by `make fetch` |
| `data/real/processed/` | Tidy tables extracted from the PDFs, with attribution | Phase MF1 |
| `data/synthetic/` | Generated loan, client and savings records, **not real people** | Phase MF4 |

## Real sources

Every input is recorded in [`source-manifest.json`](source-manifest.json) with its URL,
SHA-256 checksum, size and retrieval date. `make fetch` downloads a file only if it is
missing or its checksum differs, and refuses a download whose checksum does not match.

| Input | Publisher | Used for |
|---|---|---|
| *Microfinance in Bangladesh (Annual Statistics), June 2025* (394 pages) | Microcredit Regulatory Authority (MRA) | Main analysis: per-MFI tables for 693 MFIs, division and district coverage, sector series, loan-loss classification |
| *Microfinance in Bangladesh (Annual Statistics), June 2024* (394 pages) | MRA | Two-year comparison (MF3) |

**Terms.** The reports carry an MRA copyright notice and state no open licence. The PDFs are
therefore not committed here. The processed tables contain published numbers only and are
attributed to MRA; if the publisher objects, they will be removed.

## What the real data does not contain

- No per-MFI portfolio at risk. Loan-loss classification is published only for the
  sector as a whole (June 2025 report, Table 2.1).
- No client-level or loan-level records. That is why the loan-level work uses a
  synthetic book.
- The report's headline totals mix scopes: all-sector figures (MFIs, Grameen Bank,
  government agencies, banks) and MFI-only figures. Each table states its scope, and
  reconciliation checks keep them apart.

## Synthetic data rules

- Generated from a seed, calibrated to the real tables, and documented in
  `docs/assumptions.md` (phase MF4).
- Every synthetic table, chart and dashboard view is labeled **SYNTHETIC**.
- Findings from synthetic data describe how the mechanics behave under stated
  assumptions. They are never findings about Bangladesh or any real institution.
- No real client, loan or field-collected records are ever added to this repository.
