import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { statusPill, type TaskResult } from '../lib/trajectory'

export default function RunDetail() {
  const { runId = '' } = useParams()
  const [tasks, setTasks] = useState<TaskResult[] | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return
    fetch(`/api/runs/${encodeURIComponent(runId)}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setTasks)
      .catch((e) => setErr(String(e)))
  }, [runId])

  return (
    <div className="page">
      <div className="crumbs">
        <Link to="/">macos-world</Link>
        <span className="sep">/</span>
        <span>{runId}</span>
      </div>
      <h1 className="h1">Tasks</h1>

      {err && <div className="empty">Failed to load: {err}</div>}
      {!err && tasks === null && <div className="empty muted">Loading…</div>}
      {!err && tasks && tasks.length === 0 && (
        <div className="empty">No tasks in this run.</div>
      )}
      {!err && tasks && tasks.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Model</th>
              <th>Status</th>
              <th>Score</th>
              <th>Steps</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => {
              const pill = statusPill(t.status)
              const score =
                t.score === undefined || t.score === null
                  ? '—'
                  : `${t.score}${t.max_score ? ` / ${t.max_score}` : ''}`
              return (
                <tr key={t.task_id} className="clickable">
                  <td>
                    <Link
                      to={`/r/${encodeURIComponent(runId)}/t/${encodeURIComponent(t.task_id)}`}
                    >
                      <code>{t.task_id}</code>
                    </Link>
                  </td>
                  <td className="muted">{t.model ?? '—'}</td>
                  <td>
                    <span className={pill.cls}>{pill.label}</span>
                  </td>
                  <td>{score}</td>
                  <td>{t.n_steps ?? '—'}</td>
                  <td className="muted">
                    {t.duration_s ? `${t.duration_s.toFixed(1)}s` : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
