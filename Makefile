.PHONY: test test-unit test-integration setup-dev

setup-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-coverage:
	pytest --cov=src --cov-report=html
