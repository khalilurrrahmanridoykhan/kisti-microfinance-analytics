# Roadmap

One branch and one pull request per phase, tagged `phase-mfN` when merged. A phase is done
only when its "done when" gate passes.

| Phase | What it delivers | Data | Status |
|---|---|---|---|
| MF0 | Repo setup, checksum-verified data fetch, data provenance, glossary | Real | Done |
| MF1 | MRA tables extracted to tidy CSVs, with reconciliation tests against printed totals | Real | Done |
| MF2 | Sector analysis: concentration, sustainability, scale efficiency, pricing, funding mix, outreach, district coverage | Real | Planned |
| MF3 | Sector trend 2015-16 to 2024-25 and June 2024 to June 2025 movement per MFI | Real | Planned |
| MF4 | Seeded synthetic loan book, calibrated to the real sector and checked by tests | Synthetic | Planned |
| MF5 | Portfolio analytics in SQL and Python: PAR, roll rates, vintage curves, collection, clients, savings | Synthetic | Planned |
| MF6 | Finance models and Excel workbooks: flat vs declining rate, break-even, provisioning, branch MIS | Synthetic | Planned |
| MF7 | Climate-shock stress test on the synthetic portfolio (optional) | Synthetic | Planned |
| MF8 | Digital collection and fintech-partner pack: product spec, partner scorecard, reconciliation prototype (optional) | Synthetic | Planned |
| MF9 | Interactive web dashboard: sector overview, MFI benchmark, district coverage, synthetic portfolio monitor | Both, labeled | Planned |
| MF10 | Data API and command-line tool (optional) | Both, labeled | Planned |

The first three phases are a complete project on their own: they use only published data
and say true things about the sector. Phases MF4 to MF8 exist because no loan-level data is
public; what they show is how portfolio mechanics behave under stated assumptions, not
what happens at any real institution.
