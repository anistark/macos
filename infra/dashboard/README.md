# infra/dashboard

Local-first React + Vite + TS frontend that visualizes benchmark runs from the repo-root `outputs/` directory.

## Run

```bash
cd infra/dashboard
npm install
npm run dev
```

Serves on `http://localhost:5173`.

## Data source

The dashboard reads from `<repo-root>/outputs/runs/*/summary.json` — the same directory that the CLI in `infra/cli/` writes to. The relationship is local-only: both pieces share the filesystem.

A symlink at `public/outputs` is used to make those JSON files reachable via the dev server. Recreate it with:

```bash
ln -s ../../../outputs public/outputs
```

## Stack

Standard Vite React-TS template — see `vite.config.ts`, `tsconfig*.json`, `eslint.config.js`. Real UI (run list, drill-down, charts) is a follow-up.
