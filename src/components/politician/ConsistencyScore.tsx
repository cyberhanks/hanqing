import { getConsistencyLabel, getConsistencyColor } from '@/lib/scoring/consistency'

interface Props {
  score: number
  showBar?: boolean
}

export default function ConsistencyScore({ score, showBar = true }: Props) {
  const label = getConsistencyLabel(score)
  const color = getConsistencyColor(score)

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-ink/50">言行一致性</span>
        <span className="font-mono font-bold" style={{ color }}>
          {score} <span className="font-normal text-ink/40">{label}</span>
        </span>
      </div>
      {showBar && (
        <div className="h-1.5 w-full rounded-full bg-ink/10 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${score}%`, backgroundColor: color }}
          />
        </div>
      )}
    </div>
  )
}
