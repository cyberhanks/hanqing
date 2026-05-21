'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import { clsx } from 'clsx'
import type { Party } from '@/types'

const PARTIES: Array<{ value: string; label: string }> = [
  { value: 'ALL', label: '全部' },
  { value: 'DPP', label: '民進黨' },
  { value: 'KMT', label: '國民黨' },
  { value: 'TPP', label: '民眾黨' },
  { value: 'IND', label: '無黨籍' },
]

export default function PartyFilter() {
  const router = useRouter()
  const params = useSearchParams()
  const current = params.get('party') ?? 'ALL'

  function select(value: string) {
    const p = new URLSearchParams(params.toString())
    if (value === 'ALL') p.delete('party')
    else p.set('party', value)
    router.push(`?${p.toString()}`)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {PARTIES.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => select(value)}
          className={clsx(
            'px-3 py-1.5 rounded-full text-xs font-medium border transition-colors',
            current === value
              ? 'bg-ink text-paper border-ink'
              : 'bg-white/60 text-ink/70 border-ink/15 hover:border-ink/30'
          )}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
