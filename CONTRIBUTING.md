# Contributing

Thanks for your interest. This is a small analysis project, and issues, corrections and
suggestions are welcome.

## Ground rules

- **Public or synthetic data only.** Never add real client, loan, savings or
  field-collected records, or anything that could identify a real person or borrower.
- **Keep real and synthetic apart.** Real tables live under `data/real/`, synthetic ones
  under `data/synthetic/`. Every synthetic table, chart and dashboard view is labeled
  **SYNTHETIC**, and findings from it are never described as findings about Bangladesh.
- **Assumptions are written down.** Generator parameters and model assumptions go in
  `docs/assumptions.md` with a source (a real number and where it comes from, or the word
  "assumed"). Do not hard-code them in scripts.
- **Regulatory numbers need a citation.** Interest-rate ceilings, provisioning rates and
  classification bands come from an MRA or Bangladesh Bank document that is linked in the
  pull request, not from memory.
- **Record provenance.** Any new input needs an entry in `data/source-manifest.json` and a
  row in `data/README.md`.
- **Not financial advice.** Outputs must not be presented as credit decisions, regulatory
  findings or assessments of a named institution beyond what the published data supports.

## Workflow

1. Open an issue first for anything larger than a small fix.
2. Branch from `main` (`phase-mfX-<name>` for roadmap phases, `fix-...` or `docs-...`
   otherwise).
3. Keep commits small: one logical change each, with an imperative message
   ("Parse operating cost ratio table").
4. Run `make lint` and `make test` before opening a pull request.
5. Open a pull request using the template. CI must pass.

## Running locally

```sh
make setup   # create .venv and install the package with dev tools
make fetch   # download the source PDFs and verify their checksums
make test    # run the tests
make lint    # ruff
```

## Code of conduct

Participation is covered by the [Code of Conduct](CODE_OF_CONDUCT.md).
