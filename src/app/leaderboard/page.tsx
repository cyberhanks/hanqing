import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import { PARTY_SHORT, PARTY_COLORS } from '@/lib/utils/party'
import { clsx } from 'clsx'
import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: '兌現率排行榜 | 汗青',
  description: '台灣政治人物承諾兌現率與信任指數排行榜',
}

export const revalidate = 3600 // revalidate every hour

export default async function LeaderboardPage() {
  const supabase = await createClient()

  const { data: politicians } = await supabase
    .from('politicians')
    .select('id, name, party, role, region, trust_score, consistency_score, fulfill_rate, total_promises, fulfilled_count, broken_count')
    .order('trust_score', { ascending: false })

  if (!politicians?.length) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-ink/50">
        暫無資料
      </div>
    )
  }

  // Top 3 and full list
  const top3   = politicians.slice(0, 3)
  const rest   = politicians.slice(3)

  const medals = ['🥇', '🥈', '🥉']

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Page header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <Trophy className="w-5 h-5 text-amber-500" />
          <h1 className="font-serif font-bold text-2xl text-ink">兌現率排行榜</h1>
        </div>
        <p className="text-sm text-ink/50">依信任指數（兌現率 × 0.6 + 言行一致性 × 0.4）排列</p>
      </div>

      {/* Top 3 podium */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {top3.map((p, i) => (
          <Link
            key={p.id}
            href={`/politicians/${p.id}`}
            className="bg-white/70 border border-ink/10 rounded-xl p-5 text-center hover:border-ink/25 hover:shadow-sm transition-all group"
          >
            <div className="text-3xl mb-2">{medals[i]}</div>
            <div className={clsx('inline-block text-xs rounded px-1.5 py-0.5 mb-2 font-medium', PARTY_COLORS[p.party as keyof typeof PARTY_COLORS] ?? 'bg-ink/10 text-ink')}>
              {PARTY_SHORT[p.party as keyof typeof PARTY_SHORT] ?? p.party}
            </div>
            <div className="font-serif font-bold text-lg text-ink group-hover:underline">{p.name}</div>
            <div className="text-xs text-ink/50 mb-3">{p.role}</div>
            <div className="font-mono font-bold text-2xl text-ink">{p.trust_score}</div>
            <div className="text-xs text-ink/40">信任指數</div>
            {p.fulfill_rate != null && (
              <div className="mt-2 text-xs text-green-600">兌現率 {Math.round(p.fulfill_rate)}%</div>
            )}
          </Link>
        ))}
      </div>

      {/* Full table */}
      <div className="bg-white/60 rounded-lg border border-ink/10 overflow-hidden">
        <div className="px-5 py-3 border-b border-ink/10 flex items-center justify-between">
          <h2 className="font-serif font-bold text-sm text-ink">完整排名</h2>
          <span className="text-xs text-ink/40">{politicians.length} 位政治人物</span>
        </div>
        <div className="divide-y divide-ink/5">
          {politicians.map((p, i) => {
            const fulfillRate = p.fulfill_rate != null ? Math.round(p.fulfill_rate) : null
            const consistency = p.consistency_score ?? null

            return (
              <Link
                key={p.id}
                href={`/politicians/${p.id}`}
                className="flex items-center gap-4 px-5 py-3 hover:bg-ink/3 transition-colors"
              >
                {/* Rank */}
                <span className="text-ink/30 font-mono text-xs w-6 text-right flex-shrink-0">
                  {i < 3 ? medals[i] : i + 1}
                </span>

                {/* Name + party */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-ink">{p.name}</span>
                    <span className={clsx('text-xs rounded px-1.5 py-0.5 font-medium', PARTY_COLORS[p.party as keyof typeof PARTY_COLORS] ?? 'bg-ink/10 text-ink')}>
                      {PARTY_SHORT[p.party as keyof typeof PARTY_SHORT] ?? p.party}
                    </span>
                  </div>
                  <div className="text-xs text-ink/40 truncate">{p.role}{p.region ? `・${p.region}` : ''}</div>
                </div>

                {/* Promise stats */}
                {p.total_promises != null && p.total_promises > 0 && (
                  <div className="hidden sm:flex items-center gap-3 text-xs text-ink/50">
                    <span className="text-green-600">{p.fulfilled_count ?? 0}✓</span>
                    <span className="text-red-500">{p.broken_count ?? 0}✗</span>
                    <span>/{p.total_promises}</span>
                  </div>
                )}

                {/* Fulfill rate bar */}
                <div className="hidden md:block w-20">
                  {fulfillRate != null ? (
                    <div className="relative">
                      <div className="h-1.5 w-full bg-ink/10 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-green-500"
                          style={{ width: `${Math.min(100, fulfillRate)}%` }}
                        />
                      </div>
                      <div className="text-xs text-ink/50 mt-0.5 text-right">{fulfillRate}%</div>
                    </div>
                  ) : (
                    <div className="text-xs text-ink/25 text-center">—</div>
                  )}
                </div>

                {/* Consistency */}
                <div className="hidden lg:block w-14 text-center">
                  {consistency != null ? (
                    <>
                      <div className="text-xs font-mono font-bold text-ink">{consistency}</div>
                      <div className="text-xs text-ink/40">一致性</div>
                    </>
                  ) : (
                    <Minus className="w-3 h-3 text-ink/20 mx-auto" />
                  )}
                </div>

                {/* Trust score */}
                <div className="text-right flex-shrink-0">
                  <div className={clsx(
                    'font-mono font-bold text-sm',
                    p.trust_score >= 70 ? 'text-green-600' :
                    p.trust_score >= 50 ? 'text-amber-500' : 'text-red-500'
                  )}>
                    {p.trust_score}
                  </div>
                  <div className="text-xs text-ink/40">信任</div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Legend */}
      <p className="mt-4 text-xs text-ink/40 text-center">
        信任指數 = 兌現率 × 60% + 言行一致性 × 40%。資料每月更新。
      </p>
    </div>
  )
}
