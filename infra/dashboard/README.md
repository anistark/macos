# infra/dashboard

Local-first React + Vite + TS frontend that visualizes benchmark runs from the repo-root `outputs/` directory.

## Run

```bash
cd infra/dashboard
npm install
npm run dev
```

Serves on `http://localhost:5173`.

## Routes

- `/` — list of runs found under `outputs/runs/`.
- `/r/:runId` — list of tasks in that run (parsed from `summary.json`).
- `/r/:runId/t/:taskId` — trajectory player: scrub through screenshots, see action + model thinking per frame.

## Data source

The dashboard reads run data from `<repo-root>/outputs/runs/` — the same directory the CLI in `infra/cli/` writes to. Override with the `MACOSWORLD_OUTPUTS_DIR` env var (same convention as the CLI).

Two ways the data reaches the browser:

- **Listing** — a small dev-only Vite plugin (`vite-plugins/runs-api.ts`) exposes:
  - `GET /api/runs` → array of `{ run_id, n_tasks, mtime, has_summary }`
  - `GET /api/runs/:runId` → contents of `summary.json` (array of `TaskResult`)
- **Static files** — `trajectory.jsonl`, `result.json`, and `context/step_NNN.png` are served via the `public/outputs → ../../../outputs` symlink. Recreate the symlink with:

  ```bash
  ln -s ../../../outputs public/outputs
  ```

## Stack

Vite + React 19 + TypeScript + React Router 7. No CSS framework — plain CSS variables in `src/index.css`.
