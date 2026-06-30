"""One-off importer: push the 15 published MyPCBench curated trajectories into the
backend as a single run of rollouts, in an ISOLATED environment so they never mix
with our own cuaworld-macos dataset.

These are third-party trajectories (other vendors' models, judged by MyPCBench's
own gemini judge) scraped from https://mypcbench.com/#trajectories — every record
is tagged source=mypcbench so provenance is unambiguous. Run dir is the converted
copy under outputs/runs/mypcbench-imported-curated15/, holding the verbatim upstream
JSON under _source/trajectories/ plus the downloaded frames/ per rollout.

Each rollout's trajectory.jsonl is generated fresh from the upstream JSON in the
shape the dashboard viewer expects: per-action `input.coordinate` (rescaled from
the native 1280x800 capture into the viewer's 1024x768 marker space) and a bare
basename `screenshot` (the backend artifact manifest keys screenshots by basename,
and shotUrl() does screens[screenshot]).

Usage:
    uv run python scripts/import_mypcbench.py [--run-dir DIR] [--env ENV] [--no-frames] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from benchmark.backend import BackendClient
from mw import auth

IMPORT_ENV = "mypcbench-import"
SOURCE = "mypcbench.com"
JUDGE = "gemini-3.1-flash-lite-preview"
SESSION = "mypcbench-curated15-import"
CONTENT_TYPES = {
    ".jsonl": "application/x-ndjson",
    ".json": "application/json",
    ".jpg": "image/jpeg",
    ".png": "image/png",
}

# pyautogui display 1280x800 -> dashboard's assumed 1024x768 marker space
SX, SY = 1024 / 1280, 768 / 800
NAME_MAP = {
    "click": "left_click",
    "doubleClick": "double_click",
    "tripleClick": "triple_click",
    "rightClick": "right_click",
    "moveTo": "mouse_move",
    "dragTo": "left_click_drag",
    "drag": "left_click_drag",
}


def content_type(p: Path) -> str:
    return CONTENT_TYPES.get(p.suffix, "application/octet-stream")


def _rescale(x: int, y: int) -> list[int]:
    return [round(x * SX), round(y * SY)]


def _first_quoted(s: str) -> str:
    m = re.search(r"""(['"])(.*?)\1""", s, re.S)
    return m.group(2) if m else ""


def action_to_record(raw: str) -> dict:
    """pyautogui/bash action string -> {action, input} in dashboard shape.

    Every record carries an `input` object (its absence is what crashed the
    viewer's input.coordinate read); coordinates land under input.coordinate
    only for the pointer-family actions, rescaled to 1024x768.
    """
    raw = (raw or "").strip()
    inp: dict = {"raw": raw}
    up = raw.upper()
    if up.startswith("DONE"):
        return {"action": "terminate", "input": {**inp, "status": "DONE"}}
    if up.startswith("FAIL"):
        return {"action": "terminate", "input": {**inp, "status": "FAIL"}}
    if up.startswith("WAIT") or raw == "wait" or raw.startswith("pyautogui.sleep"):
        return {"action": "wait", "input": inp}
    if raw.startswith(("bash:", "bash ")):
        return {"action": "bash", "input": inp}
    if raw.startswith("_text"):
        return {"action": "set_text", "input": inp}
    if raw.startswith("TOOL_CALL"):
        return {"action": "tool_call", "input": inp}
    if raw.startswith("edit"):
        return {"action": "edit", "input": inp}
    if raw.startswith("pyautogui.typewrite") or raw.startswith(("type '", 'type "')):
        return {"action": "type", "input": {**inp, "text": _first_quoted(raw)}}
    if raw.startswith(("pyautogui.press", "pyautogui.hotkey")):
        keys = re.findall(r"""['"]([^'"]+)['"]""", raw)
        return {"action": "key", "input": {**inp, "keys": keys}}
    if raw.startswith(("pyautogui.scroll", "pyautogui.hscroll")):
        xy = dict(re.findall(r"(x|y)=(-?\d+)", raw))
        if "x" in xy and "y" in xy:
            inp["coordinate"] = _rescale(int(xy["x"]), int(xy["y"]))
        return {"action": "scroll", "input": inp}
    m = re.match(r"pyautogui\.(\w+)\((.*)\)", raw, re.S)
    if m:
        nums = re.findall(r"-?\d+", m.group(2))[:2]
        if len(nums) == 2:
            inp["coordinate"] = _rescale(int(nums[0]), int(nums[1]))
        return {"action": NAME_MAP.get(m.group(1), m.group(1)), "input": inp}
    m = re.match(r"(\w+)\s*\[(-?\d+),\s*(-?\d+)\]", raw)  # "click [x, y]"
    if m:
        inp["coordinate"] = _rescale(int(m.group(2)), int(m.group(3)))
        return {"action": "left_click", "input": inp}
    return {"action": "unknown", "input": inp}


def build_trajectory(run_dir: Path, slug: str) -> Path:
    """Generate <slug>/trajectory.jsonl from _source upstream JSON, dashboard-shaped."""
    src = json.loads((run_dir / "_source" / "trajectories" / f"{slug}.json").read_text())
    lines = []
    for s in src["steps"]:
        basename = Path(s["image"]).name if s.get("image") else ""
        act = action_to_record(s.get("action", ""))
        act.update(ok=True, msg="ok", screenshot=basename)
        lines.append(json.dumps({
            "step": s["i"],
            "input_tokens": 0,
            "output_tokens": 0,
            "actions": [act],
            "text": s.get("thought", ""),
        }))
    out = run_dir / slug / "trajectory.jsonl"
    out.write_text("\n".join(lines) + "\n")
    return out


def upload(client: BackendClient, rollout_id: int, task_dir: Path, relpath: str) -> str:
    path = task_dir / relpath
    ct = content_type(path)
    presigned = client.presign_artifact(rollout_id, relpath, ct)
    client.upload_artifact(presigned["upload_url"], path, ct)
    return relpath


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="outputs/runs/mypcbench-imported-curated15")
    ap.add_argument("--env", default=IMPORT_ENV)
    ap.add_argument("--no-frames", action="store_true", help="skip screenshot upload")
    ap.add_argument("--dry-run", action="store_true", help="print plan, no backend writes")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    results = json.loads((run_dir / "summary.json").read_text())
    src = run_dir / "_source"
    leaderboard = json.loads((src / "leaderboard.json").read_text()) if (src / "leaderboard.json").exists() else None

    print(f"importing {len(results)} rollouts into env '{args.env}' (session '{SESSION}')")
    if args.dry_run:
        for r in results:
            tdir = run_dir / r["slug"]
            nframes = len(list((tdir / "frames").glob("*.jpg"))) if (tdir / "frames").is_dir() else 0
            print(f"  {r['model']:18} {r['kind']:7} {r['score']:>5}%  {r['task_id']:32} steps={r['n_steps']:3} frames={nframes}")
        return

    client = auth.make_client(require=True)
    me = client.whoami()
    print(f"auth ok: {me['username']} @ {client.api_url}")

    # 1) register tasks (one per distinct task_id) in the isolated env -----
    task_map: dict[str, int] = {}
    for r in results:
        tid = r["task_id"]
        if tid in task_map:
            continue
        full = json.loads((run_dir / r["slug"] / "result.json").read_text())
        rubrics = [
            {"id": g["id"], "requirement": g["requirement"], "weight": g["weight"]}
            for g in full.get("grade_log", [])
        ]
        task = client.create_task(
            {
                "environment": args.env,
                "prompt": r.get("instruction") or full.get("instruction", ""),
                "tags": [r["category"], "mypcbench-import"],
                "metadata": {
                    "local_task_id": tid,
                    "category": r["category"],
                    "source": SOURCE,
                    "legacy_id": full.get("legacy_id"),
                    "apps": full.get("apps"),
                    "rubrics": rubrics,
                    "judge": JUDGE,
                    "imported": True,
                },
            }
        )
        task_map[tid] = task["id"]
    print(f"registered {len(task_map)} tasks")

    # idempotent: drop any prior import run for this session
    for stale in client.runs_by_session(SESSION):
        client.delete_run(stale["id"])
        print(f"replaced stale run #{stale['id']}")

    run = client.create_run(
        {
            "session_id": SESSION,
            "environment": args.env,
            "total_tasks": len(task_map),
            "status": "running",
            "metadata": {
                "model": "mixed (MyPCBench curated)",
                "source": SOURCE,
                "imported": True,
                "note": "15 curated trajectories published on mypcbench.com; 5 models, 6 categories; "
                "MyPCBench gemini judge. NOT our runs.",
                "paper": "arXiv:2606.16748",
                "paper_leaderboard": leaderboard,
            },
        }
    )
    run_id = run["id"]
    print(f"run #{run_id} created")

    # 2) one rollout per trajectory --------------------------------------
    for r in results:
        tdir = run_dir / r["slug"]
        full = json.loads((tdir / "result.json").read_text())
        build_trajectory(run_dir, r["slug"])  # dashboard-shaped, basename screenshots
        rollout = client.create_rollout(
            {
                "run_id": run_id,
                "task_id": task_map[r["task_id"]],
                "model": r["model"],
                "mode": "local",
                "session_id": SESSION,
            }
        )
        rid = rollout["id"]

        artifacts: dict = {}
        for rel in ("trajectory.jsonl", "result.json"):
            if (tdir / rel).exists():
                upload(client, rid, tdir, rel)
                artifacts[rel.split(".")[0]] = rel

        frames_dir = tdir / "frames"
        if not args.no_frames and frames_dir.is_dir():
            frames = sorted(frames_dir.glob("*.jpg"))
            shots: list[str] = []
            with ThreadPoolExecutor(max_workers=8) as pool:
                futs = {pool.submit(upload, client, rid, tdir, f"frames/{f.name}"): f.name for f in frames}
                for fut in as_completed(futs):
                    shots.append(fut.result())
            artifacts["screenshots"] = sorted(shots)

        passed = bool(full.get("passed"))
        client.patch_rollout(
            rid,
            {
                "status": "completed",
                "duration_seconds": None,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "result": {"passed": passed, "agent_passed": full.get("status") == "done"},
                "metadata": {
                    "score": full.get("score"),
                    "max_score": full.get("max_score"),
                    "n_steps": full.get("n_steps"),
                    "category": full.get("category"),
                    "terminal_reason": full.get("status"),
                    "kind": full.get("kind"),
                    "model": r["model"],
                    "rubrics_passed": full.get("rubrics_passed"),
                    "rubric_count": full.get("rubric_count"),
                    "source": SOURCE,
                    "imported": True,
                    "grade_log": full.get("grade_log"),
                    "artifacts": artifacts,
                },
            },
        )
        nshots = len(artifacts.get("screenshots", []))
        print(f"  rollout #{rid}  {r['model']:18} {r['task_id']:32} {full.get('score')}%  ({nshots} frames)")

    passed = sum(1 for r in results if bool(json.loads((run_dir / r["slug"] / "result.json").read_text()).get("passed")))
    client.patch_run(
        run_id,
        {"status": "completed", "total_rollouts": len(results), "passed_rollouts": passed, "total_tokens": 0},
    )
    print(f"done: run #{run_id}, {len(results)} rollouts, {passed} perfect, env '{args.env}'")
    client.close()


if __name__ == "__main__":
    main()
