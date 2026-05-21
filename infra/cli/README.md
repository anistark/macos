# infra/cli

Benchmark harness for evaluating Claude models on macOS computer-use tasks via the Use Computer API.

## Usage

From the repo root:

```bash
export USE_COMPUTER_API_KEY=...
export ANTHROPIC_API_KEY=...

uv run --package macosworld-usecomputer python -m benchmark.cli \
  --model claude-haiku-4-5 --tasks smoke
```

Models: `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-7` (see `benchmark/config.py`).
Tasks: `smoke`, `all`, or a comma-separated list of task IDs.

## Outputs

Run results are written to `<repo-root>/outputs/runs/<run-id>/`. Override with:

```bash
export MACOSWORLD_OUTPUTS_DIR=/absolute/path/to/outputs
```

When set, runs land in `$MACOSWORLD_OUTPUTS_DIR/runs/<run-id>/`.

## Layout

- `benchmark/` — agent loop, runner, env bridge, CLI entry point
- `tasks/` — task definitions (JSON, organized by category)
- `smoke_tasks.txt` — task IDs used by `--tasks smoke`
- `main.py` — sandbox connection helper for the Use Computer API
