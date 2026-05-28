export type ActionRecord = {
  action: string
  input: Record<string, unknown>
  ok: boolean
  msg: string
  screenshot: string
}

export type StepRecord = {
  step: number
  input_tokens?: number
  output_tokens?: number
  latency_s?: number
  actions?: ActionRecord[]
  text?: string
  status?: string
}

export type Frame = {
  frame_idx: number
  step: number
  action: string
  input: Record<string, unknown>
  ok: boolean
  msg: string
  screenshot: string
  text?: string
  status?: string
}

export type TaskResult = {
  task_id: string
  category?: string
  model?: string
  score?: number
  max_score?: number
  n_steps?: number
  status?: string
  duration_s?: number
  input_tokens?: number
  output_tokens?: number
  cost_usd?: number
  sandbox_id?: string
  error?: string | null
  grade_log?: unknown
}

export type RunInfo = {
  run_id: string
  n_tasks: number
  mtime: number
  has_summary: boolean
}

export function parseJsonl<T>(text: string): T[] {
  const out: T[] = []
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    try {
      out.push(JSON.parse(trimmed) as T)
    } catch {
      // skip malformed lines
    }
  }
  return out
}

export function flattenFrames(steps: StepRecord[]): Frame[] {
  const frames: Frame[] = []
  let idx = 0
  for (const step of steps) {
    const actions = step.actions ?? []
    if (actions.length === 0) {
      // step with no actions — surface as a single empty frame so the user sees it.
      frames.push({
        frame_idx: idx++,
        step: step.step,
        action: '(no action)',
        input: {},
        ok: true,
        msg: '',
        screenshot: '',
        text: step.text,
        status: step.status,
      })
      continue
    }
    for (const a of actions) {
      frames.push({
        frame_idx: idx++,
        step: step.step,
        action: a.action,
        input: a.input,
        ok: a.ok,
        msg: a.msg,
        screenshot: a.screenshot,
        text: step.text,
        status: step.status,
      })
    }
  }
  return frames
}

export function screenshotUrl(runId: string, taskId: string, file: string): string {
  if (!file) return ''
  return `/outputs/runs/${encodeURIComponent(runId)}/${encodeURIComponent(taskId)}/context/${file}`
}

export function statusPill(status?: string): { label: string; cls: string } {
  switch (status) {
    case 'done':
      return { label: 'done', cls: 'pill green' }
    case 'fail':
      return { label: 'fail', cls: 'pill red' }
    case 'max_steps':
      return { label: 'max steps', cls: 'pill amber' }
    case 'error':
      return { label: 'error', cls: 'pill red' }
    default:
      return { label: status ?? '—', cls: 'pill' }
  }
}
