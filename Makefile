.PHONY: setup fetch test lint

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

# Download the public source documents into data/real/raw/ and verify their checksums
fetch:
	.venv/bin/python -m kisti.fetch

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check .
