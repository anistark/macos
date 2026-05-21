default:
    @just --list

# Sync submodules
sync:
    git submodule update --init --recursive

# Run the benchmark CLI (model defaults to claude-haiku-4-5, tasks to smoke)
bench model="claude-haiku-4-5" tasks="smoke":
    uv run --package macosworld-usecomputer python -m benchmark.cli --model {{model}} --tasks {{tasks}}

# Start the dashboard dev server
dashboard:
    cd infra/dashboard && npm run dev

# Install dashboard deps
dashboard-install:
    cd infra/dashboard && npm install
