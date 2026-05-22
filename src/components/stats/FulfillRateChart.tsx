'use client'
import { CheckCircle2, XCircle, Clock, PauseCircle } from 'lucide-react'

interface Props {
  fulfilled: number
  broken: number
  stalled: number
  active: number
}

export default function FulfillRateChart({ fulfilled, broken, stalled, active }: Props) {
  const total = fulfilled + broken + stalled + active
  if (total === 0) return null

  const segments = [
    { label: '已兌現', value: fulfilled, color: '#16a34a', icon: CheckCircle2 },
    { label: '跳票',   value: broken,    color: '#ef4444', icon: XCircle },
    { label: '停滯中', value: stalled,   color: '#f59e0b', icon: PauseCircle },
    { label: '追蹤中', value: active,    color: '#6366f1', icon: Clock },
  ].filter(s => s.value > 0)

  return (
    <div className="space-y-2">
      {/* Stacked bar */}
      <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
        {segments.map(({ label, value, color }) => (
          <div
            key={label}
            style={{ width: `${(value / total) * 100}%`, backgroundColor: color }}
            title={`${label}: ${value}`}
            className="transition-all duration-500"
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {segments.map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="flex items-center gap-1.5 text-xs text-ink/60">
            <Icon className="w-3 h-3 flex-shrink-0" style={{ color }} />
            <span>{label}</span>
            <span className="font-mono font-bold text-ink/80">{value}</span>
            <span className="text-ink/30">({Math.round((value / total) * 100)}%)</span>
          </div>
        ))}
      </div>
    </div>
  )
}
