import type { Metadata } from 'next'
import Link from 'next/link'
import { search } from '@/lib/api/search'
import SearchBox from '@/components/ui/SearchBox'
import { PARTY_SHORT } from '@/lib/utils/party'
import type { Party } from '@/types'

export const metadata: Metadata = { title: '搜尋' }

interface PageProps {
  searchParams: Promise<{ q?: string }>
}

export default async function SearchPage({ searchParams }: PageProps) {
  const { q = '' } = await searchParams
  const results = q ? await search(q) : []

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="font-serif font-bold text-2xl text-ink mb-6">搜尋</h1>
      <SearchBox defaultValue={q} className="mb-8" />

      {q && (
        <p className="text-sm text-ink/50 mb-4">
          「{q}」的搜尋結果，共 {results.length} 筆
        </p>
      )}

      <div className="space-y-3">
        {results.map(r => (
          <div key={`${r.type}-${r.id}`} className="bg-white/60 border border-ink/10 rounded-lg p-4 hover:border-ink/25 transition-colors">
            <div className="flex items-start gap-3">
              <span className="text-xs bg-ink/8 text-ink/60 px-2 py-0.5 rounded mt-0.5 flex-shrink-0">
                {r.type === 'politician' ? '人物' : r.type === 'promise' ? '承諾' : '發言'}
              </span>
              <div className="min-w-0 flex-1">
                {r.type === 'politician' ? (
                  <Link href={`/politicians/${r.id}`} className="font-medium text-ink hover:underline">
                    {r.title}
                  </Link>
                ) : (
                  <p className="font-medium text-ink text-sm">{r.title}</p>
                )}
                {r.politician && (
                  <Link href={`/politicians/${r.politician.id}`} className="text-xs text-ink/50 hover:text-ink mt-0.5 inline-flex items-center gap-1">
                    {r.politician.name}
                    <span className="text-ink/30">・{PARTY_SHORT[r.politician.party as Party]}</span>
                  </Link>
                )}
                <p className="text-sm text-ink/60 mt-1.5 line-clamp-2">{r.excerpt}</p>
              </div>
            </div>
          </div>
        ))}
        {q && results.length === 0 && (
          <p className="text-center text-ink/40 py-12">找不到相關結果</p>
        )}
        {!q && (
          <p className="text-center text-ink/40 py-12">輸入關鍵字開始搜尋</p>
        )}
      </div>
    </div>
  )
}
