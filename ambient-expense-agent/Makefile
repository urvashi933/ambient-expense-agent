.PHONY: install playground ambient

install:
	uv sync

playground:
	uv run adk web expense_agent

ambient:
	uv run uvicorn expense_agent.fast_api_app:app --host 0.0.0.0 --port 8080
