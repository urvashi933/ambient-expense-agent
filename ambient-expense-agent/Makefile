.PHONY: install playground ambient generate-traces grade

install:
	uv sync

playground:
	uv run adk web expense_agent

ambient:
	uv run uvicorn expense_agent.fast_api_app:app --host 0.0.0.0 --port 8080

generate-traces:
	uv run python tests/eval/generate_traces.py

grade:
	uv run agents-cli eval grade --traces artifacts/traces/generated_traces.json --config tests/eval/eval_config.yaml
