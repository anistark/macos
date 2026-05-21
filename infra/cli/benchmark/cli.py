from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from benchmark.config import MODEL_CONFIG
from benchmark.runner import run_task
from benchmark.task import load_tasks

OUTPUTS_ROOT = Path(
    os.environ.get(
        "MACOSWORLD_OUTPUTS_DIR",
        Path(__file__).resolve().parents[3] / "outputs",
    )
) / "runs"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, choices=sorted(MODEL_CONFIG.keys()))
    p.add_argument("--tasks", default="smoke", help="'smoke', 'all', or comma-separated task IDs")
    p.add_argument("--run-id", default=None, help="Override the run directory name (default: <model>-<ts>)")
    args = p.parse_args()

    if not os.getenv("USE_COMPUTER_API_KEY"):
        sys.exit("USE_COMPUTER_API_KEY not set")
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set")

    if args.tasks == "smoke":
        tasks = load_tasks(smoke=True)
    elif args.tasks == "all":
        tasks = load_tasks()
    else:
        tasks = load_tasks(ids=[t.strip() for t in args.tasks.split(",") if t.strip()])

    run_id = args.run_id or f"{args.model}-{int(time.time())}"
    run_dir = OUTPUTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run dir: {run_dir}")
    print(f"Tasks  : {len(tasks)} ({', '.join(t.id[:8] for t in tasks)})")

    results = []
    for task in tasks:
        res = run_task(args.model, task, run_dir)
        results.append(res)

    (run_dir / "summary.json").write_text(json.dumps([asdict(r) for r in results], indent=2))

    print("\n" + "=" * 80)
    print(f"SUMMARY — {args.model} — {len(results)} tasks")
    print("=" * 80)
    print(f"{'category':<20} {'task':<10} {'score':>5} {'steps':>5} {'in_tok':>8} {'out_tok':>8} {'cost$':>7} {'status':<10}")
    for r in results:
        print(f"{r.category:<20} {r.task_id[:8]:<10} {r.score:>5} {r.n_steps:>5} {r.input_tokens:>8} {r.output_tokens:>8} {r.cost_usd:>7.4f} {r.status:<10}")
    total_score = sum(r.score for r in results)
    total_cost = sum(r.cost_usd for r in results)
    print("-" * 80)
    print(f"{'TOTAL':<20} {'':<10} {total_score:>5} {'':<5} {sum(r.input_tokens for r in results):>8} {sum(r.output_tokens for r in results):>8} {total_cost:>7.4f}")


if __name__ == "__main__":
    main()
