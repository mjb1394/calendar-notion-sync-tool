.PHONY: setup update run-tk run-flask test lint

ENV?=notion_calendar_sync

# Environment Management
setup:
	@echo "Creating Conda environment '$(ENV)' from environment.dev.yml..."
	mamba env create -f environment.dev.yml -n $(ENV)

update:
	@echo "Updating Conda environment '$(ENV)'..."
	mamba env update -f environment.yml -n $(ENV) --prune

# Application Runners
run-tk:
	@echo "Starting Tkinter application..."
	python -m notion_calendar_sync.apps.tkinker.app

run-flask:
	@echo "Starting Flask development server..."
	python -m notion_calendar_sync.apps.flask.app

run-flask-prod:
	@echo "Starting Flask production server with waitress..."
	waitress --host=127.0.0.1 --port=5000 notion_calendar_sync.apps.flask.wsgi:application

run-cli-help:
	@echo "Displaying help for the CLI..."
	python -m notion_calendar_sync.main --help

run-cli-sync:
	@echo "Running Notion sync..."
	python -m notion_calendar_sync.main sync

run-cli-plan-study:
	@echo "Running study planner..."
	@echo "Note: You need to pass arguments, e.g., 'python -m notion_calendar_sync.main plan-study --exam \"Finals\" --date \"2024-12-15\"'"
	python -m notion_calendar_sync.main plan-study

# Development
test:
	@echo "Running tests..."
	PYTHONPATH=. pytest -q

lint:
	@echo "Running linters..."
	@echo "Skipping mypy due to environment issues."
	ruff check .
	black --check .

format:
	@echo "Formatting files with black and ruff..."
	ruff check . --fix
	black .
