import { useEffect, useRef } from 'react'

type Props = {
  value: number
  total: number
  playing: boolean
  onChange: (v: number) => void
  onTogglePlay: () => void
  intervalMs?: number
}

export default function Scrubber({
  value,
  total,
  playing,
  onChange,
  onTogglePlay,
  intervalMs = 500,
}: Props) {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!playing) return
    timerRef.current = setInterval(() => {
      onChange(value + 1 >= total ? 0 : value + 1)
    }, intervalMs)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [playing, value, total, intervalMs, onChange])

  const last = Math.max(0, total - 1)
  return (
    <div className="scrubber">
      <button onClick={() => onChange(0)} disabled={total === 0}>
        ⏮
      </button>
      <button onClick={() => onChange(Math.max(0, value - 1))} disabled={value <= 0}>
        ◀
      </button>
      <button onClick={onTogglePlay} disabled={total === 0}>
        {playing ? '⏸' : '▶'}
      </button>
      <button
        onClick={() => onChange(Math.min(last, value + 1))}
        disabled={value >= last}
      >
        ▶
      </button>
      <button onClick={() => onChange(last)} disabled={total === 0}>
        ⏭
      </button>
      <input
        type="range"
        min={0}
        max={last}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <div className="counter">
        {total === 0 ? '0 / 0' : `${value + 1} / ${total}`}
      </div>
    </div>
  )
}
