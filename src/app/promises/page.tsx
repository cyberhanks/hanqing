import { Suspense } from 'react'
import type { Metadata } from 'next'
import { getPromises } from '@/lib/api/promises'
import PromiseCard from '@/components/promise/PromiseCard'
import TopicFilter from '@/components/filters/TopicFilter'
import type { PromiseStatus } from '@/types'

export const metadata: Metadata = { title: '承諾追蹤' }

const STATUS_TABS: Array<{ value: string; label: string }> = [
  { value: '', label: '全部' },
  { value: 'active', label: '進行中' },
  { value: 'fulfilled', label: '已兌現' },
  { value: 'broken', label: '跳票' },
  { value: 'stalled', label: '停滯中' },
]

interface PageProps {
  searchParams: Promise<{ status?: string; topic?: string }>
}

export default async function PromisesPage({ searchParams }: PageProps) {
  const { status, topic } = await searchParams
  const promises = await getPromises({
    status: status as PromiseStatus | undefined,
    topic: topic || undefined,
  })

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="font-serif font-bold text-2xl text-ink mb-6">承諾追蹤</h1>

      {/* Status tabs */}
      <div className="flex gap-2 flex-wrap mb-4">
        {STATUS_TABS.map(({ value, label }) => (
          <a
            key={value}
            href={`/promises${value ? `?status=${value}` : ''}`}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              (status ?? '') === value
                ? 'bg-ink text-paper border-ink'
                : 'bg-white/60 text-ink/70 border-ink/15 hover:border-ink/30'
            }`}
          >
            {label}
          </a>
        ))}
      </div>

      <Suspense fallback={null}>
        <TopicFilter />
      </Suspense>

      <div className="mt-6 space-y-4">
        {promises.length === 0
          ? <p className="text-center text-ink/40 py-12">目前沒有符合條件的承諾紀錄</p>
          : promises.map(p => (
            <PromiseCard key={p.id} promise={p} showPolitician />
          ))
        }
      </div>
    </div>
  )
}
