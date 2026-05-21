import type { Politician } from '@/types'
import PoliticianCard from './PoliticianCard'

interface PoliticianGridProps {
  politicians: Politician[]
}

export default function PoliticianGrid({ politicians }: PoliticianGridProps) {
  if (politicians.length === 0) {
    return (
      <div className="text-center py-16 text-ink/40">
        <p className="text-lg">目前沒有符合條件的政治人物</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {politicians.map(p => (
        <PoliticianCard key={p.id} politician={p} />
      ))}
    </div>
  )
}
