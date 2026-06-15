.PHONY: install dev test lint run-api demo
install:
	pip install -e .
dev:
	pip install -e ".[dev,llm]"
test:
	pytest -q
lint:
	ruff check src tests
run-api:
	uvicorn bravelab.api:app --reload
demo:
	python examples/demo.py
