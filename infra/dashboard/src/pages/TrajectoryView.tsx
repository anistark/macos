import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Scrubber from '../components/Scrubber'
import {
  flattenFrames,
  parseJsonl,
  screenshotUrl,
  statusPill,
  type StepRecord,
  type TaskResult,
} from '../lib/trajectory'

const PRELOAD_AHEAD = 5

export default function TrajectoryView() {
  const { runId = '', taskId = '' } = useParams()
  const [steps, setSteps] = useState<StepRecord[] | null>(null)
  const [result, setResult] = useState<TaskResult | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [frameIdx, setFrameIdx] = useState(0)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    if (!runId || !taskId) return
    const base = `/outputs/runs/${encodeURIComponent(runId)}/${encodeURIComponent(taskId)}`
    fetch(`${base}/trajectory.jsonl`)
      .then((r) => {
        if (!r.ok) throw new Error(`trajectory.jsonl HTTP ${r.status}`)
        return r.text()
      })
      .then((text) => setSteps(parseJsonl<StepRecord>(text)))
      .catch((e) => setErr(String(e)))

    fetch(`${base}/result.json`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setResult)
      .catch(() => {})
  }, [runId, taskId])

  const frames = useMemo(() => (steps ? flattenFrames(steps) : []), [steps])
  const cur = frames[frameIdx]

  useEffect(() => {
    if (!cur || !runId || !taskId) return
    for (let i = 1; i <= PRELOAD_AHEAD; i++) {
      const next = frames[frameIdx + i]
      if (!next || !next.screenshot) continue
      const img = new Image()
      img.src = screenshotUrl(runId, taskId, next.screenshot)
    }
  }, [frameIdx, frames, cur, runId, taskId])

  const pill = statusPill(result?.status)

  return (
    <div className="page">
      <div className="crumbs">
        <Link to="/">macos-world</Link>
        <span className="sep">/</span>
        <Link to={`/r/${encodeURIComponent(runId)}`}>{runId}</Link>
        <span className="sep">/</span>
        <span>{taskId}</span>
        {result?.status && (
          <>
            <span className="sep">·</span>
            <span className={pill.cls}>{pill.label}</span>
          </>
        )}
        {result && result.score !== undefined && result.score !== null && (
          <>
            <span className="sep">·</span>
            <span className="muted">
              score {result.score}
              {result.max_score ? ` / ${result.max_score}` : ''}
            </span>
          </>
        )}
        {result?.n_steps !== undefined && (
          <>
            <span className="sep">·</span>
            <span className="muted">{result.n_steps} steps</span>
          </>
        )}
      </div>

      {err && <div className="empty">Failed to load trajectory: {err}</div>}
      {!err && steps === null && <div className="empty muted">Loading…</div>}
      {!err && steps && frames.length === 0 && (
        <div className="empty">No frames in this trajectory.</div>
      )}

      {!err && cur && (
        <>
          <div className="viewer">
            <div className="stage">
              {cur.screenshot ? (
                <img
                  src={screenshotUrl(runId, taskId, cur.screenshot)}
                  alt={`step ${cur.step}`}
                />
              ) : (
                <div className="muted">(no screenshot)</div>
              )}
            </div>
            <div className="side">
              <div className="card">
                <div className="label">Step {cur.step} · Action</div>
                <div style={{ marginBottom: 6 }}>
                  <span className={`pill ${cur.ok ? 'green' : 'red'}`}>
                    {cur.action || '—'}
                  </span>
                </div>
                <pre>{JSON.stringify(cur.input, null, 2)}</pre>
                {cur.msg && (
                  <>
                    <div className="label" style={{ marginTop: 10 }}>
                      msg
                    </div>
                    <pre className={cur.ok ? '' : 'muted'}>{cur.msg}</pre>
                  </>
                )}
              </div>
              <div className="card">
                <div className="label">Model thinking</div>
                <pre>{cur.text?.trim() || '(none captured)'}</pre>
              </div>
            </div>
          </div>

          <Scrubber
            value={frameIdx}
            total={frames.length}
            playing={playing}
            onChange={(v) => setFrameIdx(v)}
            onTogglePlay={() => setPlaying((p) => !p)}
          />
        </>
      )}
    </div>
  )
}
