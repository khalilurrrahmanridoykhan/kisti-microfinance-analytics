.PHONY: setup fetch extract crosscheck analyse webdata web-install web-test web-build test lint

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

# Download the public source documents into data/real/raw/ and verify their checksums
fetch:
	.venv/bin/python -m kisti.fetch

# Extract the MRA tables (about a minute) and the census district populations into data/real/processed/
extract:
	.venv/bin/python -m kisti.extract
	.venv/bin/python -m kisti.extract.census

# Compare the extracted tables with a second extraction method (needs poppler's pdftotext)
crosscheck:
	.venv/bin/python scripts/crosscheck_pdftotext.py

# Run the sector analysis: writes RESULTS.md, results/tables, results/figures and results/summary.json
analyse:
	.venv/bin/python -m kisti.analysis

# Export the analysis as JSON for the dashboard into web/public/data/
webdata:
	.venv/bin/python -m kisti.webdata

test:
	.venv/bin/python -m pytest -q

# The dashboard (web/): install once, then test or build
web-install:
	cd web && npm ci

web-test:
	cd web && npx eslint src && npm run typecheck && npm test

web-build:
	cd web && npm run build

lint:
	.venv/bin/ruff check .
