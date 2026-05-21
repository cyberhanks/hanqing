import { Suspense } from 'react'
import { getPoliticians } from '@/lib/api/politicians'
import PoliticianGrid from '@/components/politician/PoliticianGrid'
import PartyFilter from '@/components/filters/PartyFilter'
import SearchBox from '@/components/ui/SearchBox'
import Link from 'next/link'
import { ArrowRight, Scale, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'

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

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {[
          { icon: Scale, label: '受監督人物', value: politicians.length, color: 'text-ink' },
          { icon: CheckCircle2, label: '承諾已兌現', value: '—', color: 'text-status-fulfilled' },
          { icon: AlertTriangle, label: '承諾跳票', value: '—', color: 'text-status-broken' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="bg-white/60 rounded-lg border border-ink/10 p-4 text-center">
            <Icon className={`w-5 h-5 mx-auto mb-2 ${color}`} />
            <div className={`text-2xl font-mono font-bold ${color}`}>{value}</div>
            <div className="text-xs text-ink/50 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Politicians list */}
      <section>
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
    </div>
  )
}
