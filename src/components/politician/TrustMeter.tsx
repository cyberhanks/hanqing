import { clsx } from 'clsx'
import { trustLabel, trustColor } from '@/lib/utils/score'

interface TrustMeterProps {
  score: number
  showLabel?: boolean
}

export default function TrustMeter({ score, showLabel = true }: TrustMeterProps) {
  const pct = Math.max(0, Math.min(100, score))

  const barColor = score >= 75
    ? 'bg-status-fulfilled'
    : score >= 50
    ? 'bg-status-active'
    : score >= 30
    ? 'bg-status-stalled'
    : 'bg-status-broken'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-ink/10 overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all', barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={clsx('text-xs font-mono tabular-nums font-medium', trustColor(score))}>
        {pct}
        {showLabel && <span className="ml-1 font-sans font-normal text-ink/50">{trustLabel(score)}</span>}
      </span>
    </div>
  )
}
