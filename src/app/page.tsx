import { Suspense } from 'react'
import { getPoliticians } from '@/lib/api/politicians'
import PoliticianGrid from '@/components/politician/PoliticianGrid'
import PartyFilter from '@/components/filters/PartyFilter'
import SearchBox from '@/components/ui/SearchBox'
import GlobalStats from '@/components/stats/GlobalStats'
import PartyRanking from '@/components/stats/PartyRanking'
import Link from 'next/link'
import { ArrowRight, Scale, Trophy } from 'lucide-react'

interface PageProps {
  searchParams: Promise<{ party?: string }>
}

export default async function HomePage({ searchParams }: PageProps) {
  const { party } = await searchParams
  const politicians = await getPoliticians(party)

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Hero */}
      <section className="text-center py-12 mb-10">
        <div className="inline-flex items-center gap-2 mb-4 text-ink/50 text-sm border border-ink/15 rounded-full px-4 py-1.5">
          <Scale className="w-3.5 h-3.5" />
          公民監督平台
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-ink mb-4 leading-tight">
          汗青 HanQing
        </h1>
        <p className="text-ink/60 text-lg max-w-2xl mx-auto leading-relaxed">
          記錄政治人物的每一句承諾、每一次投票、每一個爭議事件。<br className="hidden sm:block" />
          讓言行不一無所遁形。
        </p>
        <div className="mt-6 max-w-md mx-auto">
          <SearchBox />
        </div>
      </section>

      {/* Live Stats */}
      <div className="mb-10">
        <Suspense fallback={
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white/60 rounded-lg border border-ink/10 p-4 h-20 animate-pulse" />
            ))}
          </div>
        }>
          <GlobalStats />
        </Suspense>
      </div>

      {/* Rankings + Politicians */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Politicians main column */}
        <section className="lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-serif font-bold text-xl text-ink">政治人物</h2>
            <Link href="/politicians" className="text-sm text-ink/50 hover:text-ink flex items-center gap-1">
              全部 <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <Suspense fallback={null}>
            <PartyFilter />
          </Suspense>
          <div className="mt-5">
            <PoliticianGrid politicians={politicians} />
          </div>
        </section>

        {/* Sidebar: Party ranking + leaderboard link */}
        <aside className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-serif font-bold text-base text-ink">黨派信任排名</h2>
              <Link href="/leaderboard" className="text-xs text-ink/50 hover:text-ink flex items-center gap-1">
                <Trophy className="w-3 h-3" /> 排行榜
              </Link>
            </div>
            <Suspense fallback={
              <div className="bg-white/60 rounded-lg border border-ink/10 h-48 animate-pulse" />
            }>
              <PartyRanking />
            </Suspense>
          </div>

          <div className="bg-amber-50 border border-amber-200/60 rounded-lg p-4 text-sm text-amber-800">
            <div className="font-medium mb-1 flex items-center gap-1.5">
              <Trophy className="w-4 h-4 text-amber-500" />
              兌現率排行榜
            </div>
            <p className="text-xs text-amber-700/80 mb-3">
              查看所有政治人物的承諾兌現率與言行一致性排名
            </p>
            <Link
              href="/leaderboard"
              className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 hover:text-amber-900"
            >
              前往排行榜 <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
