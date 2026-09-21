# Data

Two layers, kept in separate folders and never mixed in one table or chart.

| Folder | Layer | Status |
|---|---|---|
| `data/real/raw/` | Source PDFs fetched from the publisher (not committed) | Fetched by `make fetch` |
| `data/real/processed/` | Tidy tables extracted from the June 2025 report and the census, with attribution | Done (MF1, MF2), see [docs/extraction-notes.md](../docs/extraction-notes.md) |
| `data/synthetic/` | Generated loan, client and savings records, **not real people** | Phase MF4 |

## Real sources

Every input is recorded in [`source-manifest.json`](source-manifest.json) with its URL,
SHA-256 checksum, size and retrieval date. `make fetch` downloads a file only if it is
missing or its checksum differs, and refuses a download whose checksum does not match.

| Input | Publisher | Used for |
|---|---|---|
| *Microfinance in Bangladesh (Annual Statistics), June 2025* (394 pages) | Microcredit Regulatory Authority (MRA) | Main analysis: per-MFI tables for 693 MFIs, division and district coverage, sector series, loan-loss classification |
| *Microfinance in Bangladesh (Annual Statistics), June 2024* (394 pages) | MRA | Two-year comparison (MF3) |
| *Population and Housing Census 2022*, district (Admin 2) tables, 64 districts | Bangladesh Bureau of Statistics, via the Humanitarian Data Exchange (UN in Bangladesh) | District population and account-ownership context for coverage per 1,000 people (MF2) |

**Terms.** The census tables are listed on HDX as public domain (CC0); attribute BBS. The MRA reports carry an MRA copyright notice and state no open licence. The PDFs are
therefore not committed here. The processed tables contain published numbers only and are
attributed to MRA; if the publisher objects, they will be removed.

## What the real data does not contain

- Not every MFI appears in every table: 693 in the Basic table, 626, 600, 540 and 569 in the
  positions, cost, risk and fund tables. The per-MFI rows also fall slightly short of the
  printed sector totals. Details are in the extraction notes.
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
