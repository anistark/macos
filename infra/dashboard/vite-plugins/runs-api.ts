import { promises as fs } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

function resolveOutputsRoot(): string {
  const env = process.env.MACOSWORLD_OUTPUTS_DIR
  if (env) return path.resolve(env)
  return path.resolve(__dirname, '..', '..', '..', 'outputs', 'runs')
}

async function listRuns(root: string) {
  let entries: import('fs').Dirent[]
  try {
    entries = await fs.readdir(root, { withFileTypes: true })
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return []
    throw err
  }

  const runs = await Promise.all(
    entries
      .filter((d) => d.isDirectory())
      .map(async (d) => {
        const runDir = path.join(root, d.name)
        const stat = await fs.stat(runDir)

        let nTasks = 0
        let summary: unknown = null
        try {
          const summaryRaw = await fs.readFile(path.join(runDir, 'summary.json'), 'utf8')
          summary = JSON.parse(summaryRaw)
          if (Array.isArray(summary)) nTasks = summary.length
        } catch {
          const subdirs = await fs.readdir(runDir, { withFileTypes: true })
          nTasks = subdirs.filter((s) => s.isDirectory()).length
        }

        return {
          run_id: d.name,
          n_tasks: nTasks,
          mtime: stat.mtimeMs,
          has_summary: summary !== null,
        }
      }),
  )

  runs.sort((a, b) => b.mtime - a.mtime)
  return runs
}

async function readRunSummary(root: string, runId: string) {
  const runDir = path.join(root, runId)
  try {
    const raw = await fs.readFile(path.join(runDir, 'summary.json'), 'utf8')
    return JSON.parse(raw)
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code !== 'ENOENT') throw err
  }

  let subdirs: import('fs').Dirent[]
  try {
    subdirs = await fs.readdir(runDir, { withFileTypes: true })
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return null
    throw err
  }
  const results = await Promise.all(
    subdirs
      .filter((d) => d.isDirectory())
      .map(async (d) => {
        try {
          const resultRaw = await fs.readFile(
            path.join(runDir, d.name, 'result.json'),
            'utf8',
          )
          return JSON.parse(resultRaw)
        } catch {
          return { task_id: d.name, status: 'unknown' }
        }
      }),
  )
  return results
}

function sendJson(res: import('http').ServerResponse, status: number, body: unknown) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(body))
}

export function runsApi(): Plugin {
  return {
    name: 'runs-api',
    configureServer(server) {
      const outputsRoot = resolveOutputsRoot()
      server.config.logger.info(`[runs-api] serving runs from ${outputsRoot}`)

      server.middlewares.use('/api/runs', async (req, res, next) => {
        if (req.method !== 'GET') return next()
        try {
          const url = new URL(req.url || '/', 'http://x')
          const rest = url.pathname.replace(/^\/+|\/+$/g, '')
          if (!rest) {
            const runs = await listRuns(outputsRoot)
            return sendJson(res, 200, runs)
          }
          const [runId, ...extra] = rest.split('/')
          if (extra.length > 0) return next()
          const summary = await readRunSummary(outputsRoot, runId)
          if (summary === null) return sendJson(res, 404, { error: 'run not found' })
          return sendJson(res, 200, summary)
        } catch (err) {
          const message = err instanceof Error ? err.message : String(err)
          return sendJson(res, 500, { error: message })
        }
      })
    },
  }
}
