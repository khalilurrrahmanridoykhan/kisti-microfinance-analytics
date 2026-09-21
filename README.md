# Kisti: Microfinance Analytics for Bangladesh

[![CI](https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

*Kisti* (কিস্তি) is the Bengali word for a loan instalment, the unit every microfinance loan is
repaid in. This project analyses Bangladesh's microfinance sector in two clearly separated layers:

| Layer | Data | What it can claim |
|---|---|---|
| **Real** | The Microcredit Regulatory Authority's *Microfinance in Bangladesh (Annual Statistics)*: institution-level figures for 693 licensed MFIs, division and district coverage, sector series | Findings about the real sector |
| **Synthetic** | A generated loan, client and savings book, calibrated to the real tables | How portfolio mechanics behave under stated assumptions, never findings about Bangladesh |

Planned outputs: a sector analysis on the real data (concentration, sustainability, scale
efficiency, pricing, funding mix, outreach, district coverage), portfolio analytics on the
synthetic book (PAR, roll rates, vintage curves, collection efficiency, client and savings
dynamics) in SQL and Python, finance models in Excel (effective interest rate, break-even,
provisioning), and an interactive web dashboard.

## Status

Phases MF0 (repo, data provenance, glossary) and MF1 (the MRA June 2025 tables extracted to
tested CSVs) are complete. Analysis begins in MF2. See the [roadmap](docs/roadmap.md). No
analysis results are published yet, and none are claimed.

## What this project cannot tell you

- **Delinquency by institution.** MRA publishes portfolio quality only for the sector as a
  whole. Per-MFI "risk" ratios in the report are financial-structure ratios, not PAR.
- **Anything about real clients or loans.** No client-level or loan-level data is public,
  and none is used. All loan-level data here is synthetic and labeled as such.
- **Credit, lending or supervisory decisions.** Outputs are analysis, not advice.

## Privacy and sensitive data

The real layer is published, institution-level and aggregate: it describes organisations
and their totals, not people. The synthetic layer is generated and describes no real
person. The repository holds no person-level records and no sensitive data, and none must
be added: no client names, national IDs, phone numbers, addresses, loan files or
field-collected submissions.

## Ethics

No human participants are involved, so no institutional review or informed consent applies:
the work uses only published aggregate statistics and synthetic data. One care point
remains. The real tables name individual institutions, and ratios can be misread as
accusations. Results are therefore reported as what the published figures show, with
their limits, and a screening rule based on financial ratios is never presented as
evidence of poor practice by a named institution.

## Data description

Conventions, units and missing-value handling are in the
[data dictionary](docs/data-dictionary.md); every metric formula is in the
[glossary](docs/glossary.md).

## Quick start

```sh
make setup   # create .venv and install the package with dev tools
make fetch   # download the MRA reports into data/real/raw/ and verify their checksums
make extract # read the June 2025 tables into data/real/processed/ (about a minute)
make test    # run the tests
make lint    # ruff
```

Requires Python 3.11 or newer.

## Data

Sources, checksums and terms are in [`data/README.md`](data/README.md) and
[`data/source-manifest.json`](data/source-manifest.json). The MRA reports carry a copyright
notice and no open licence, so the PDFs are fetched, never committed; extracted tables
contain published numbers only and are attributed to MRA.

## Layout

```
data/          provenance, real (raw, processed) and synthetic data
docs/          roadmap, glossary, data dictionary, extraction notes
src/kisti/     package code (fetch, extract)
scripts/       cross-check of the extracted tables against a second method
tests/         tests, including reconciliation of the extracted tables
```

## Contributing

Issues and corrections are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). To report a security problem, see
[SECURITY.md](SECURITY.md).

## License

Code is released under the [Apache License 2.0](LICENSE). Published statistics remain the
property of their publisher; see [`data/README.md`](data/README.md).

## Citation

See [`CITATION.cff`](CITATION.cff), or use GitHub's "Cite this repository".
