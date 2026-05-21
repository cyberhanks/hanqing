'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import { clsx } from 'clsx'

const TOPICS = ['全部', '能源', '交通', '住宅', '經濟', '廉政', '教育', '醫療', '外交', '國防', '政治改革']

export default function TopicFilter() {
  const router = useRouter()
  const params = useSearchParams()
  const current = params.get('topic') ?? '全部'

  function select(topic: string) {
    const p = new URLSearchParams(params.toString())
    if (topic === '全部') p.delete('topic')
    else p.set('topic', topic)
    router.push(`?${p.toString()}`)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {TOPICS.map(t => (
        <button
          key={t}
          onClick={() => select(t)}
          className={clsx(
            'px-3 py-1 rounded text-xs font-medium border transition-colors',
            current === t
              ? 'bg-ink text-paper border-ink'
              : 'bg-white/60 text-ink/70 border-ink/15 hover:border-ink/30'
          )}
        >
          {t}
        </button>
      ))}
    </div>
  )
}
