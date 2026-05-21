import type { Promise as HQPromise } from '@/types'
import PromiseCard from './PromiseCard'

interface PromiseTimelineProps {
  promises: HQPromise[]
}

export default function PromiseTimeline({ promises }: PromiseTimelineProps) {
  if (promises.length === 0) {
    return <p className="text-ink/40 text-sm py-8 text-center">尚無承諾紀錄</p>
  }

  return (
    <div className="relative space-y-4 pl-4 before:absolute before:left-0 before:top-2 before:bottom-2 before:w-px before:bg-ink/10">
      {promises.map(p => (
        <div key={p.id} className="relative">
          <div className="absolute -left-[17px] top-5 w-2.5 h-2.5 rounded-full border-2 border-paper bg-ink/20" />
          <PromiseCard promise={p} />
        </div>
      ))}
    </div>
  )
}
