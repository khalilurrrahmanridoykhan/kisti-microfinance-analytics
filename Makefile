.PHONY: setup fetch extract crosscheck test lint

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

# Download the public source documents into data/real/raw/ and verify their checksums
fetch:
	.venv/bin/python -m kisti.fetch

# Extract the MRA tables from the PDF into data/real/processed/ (about a minute)
extract:
	.venv/bin/python -m kisti.extract

# Compare the extracted tables with a second extraction method (needs poppler's pdftotext)
crosscheck:
	.venv/bin/python scripts/crosscheck_pdftotext.py

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check .
