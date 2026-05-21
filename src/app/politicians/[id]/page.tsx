import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { getPolitician } from '@/lib/api/politicians'
import { getPromises } from '@/lib/api/promises'
import { PARTY_SHORT, PARTY_COLORS } from '@/lib/utils/party'
import { clsx } from 'clsx'
import TrustMeter from '@/components/politician/TrustMeter'
import PromiseTimeline from '@/components/promise/PromiseTimeline'
import { VoteRecord } from '@/components/vote/VoteRecord'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'

interface PageProps {
  params: Promise<{ id: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params
  const p = await getPolitician(id)
  if (!p) return { title: '找不到此人物' }
  return { title: p.name }
}

export default async function PoliticianPage({ params }: PageProps) {
  const { id } = await params
  const supabase = (await import('@/lib/supabase/server')).createClient
  const db = await supabase()
  const [politician, promises, votes] = await Promise.all([
    getPolitician(id),
    getPromises({ politicianId: id }),
    db.from('votes').select('*').eq('politician_id', id).order('vote_date', { ascending: false }).limit(30).then(r => r.data ?? []),
  ])
  if (!politician) notFound()

  const p = politician
  const statusCounts = {
    fulfilled: promises.filter(x => x.status === 'fulfilled').length,
    broken:    promises.filter(x => x.status === 'broken').length,
    stalled:   promises.filter(x => x.status === 'stalled').length,
    active:    promises.filter(x => x.status === 'active').length,
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link href="/politicians" className="inline-flex items-center gap-1.5 text-sm text-ink/50 hover:text-ink mb-6">
        <ArrowLeft className="w-4 h-4" /> 回政治人物列表
      </Link>

      {/* Profile header */}
      <div className="flex items-start gap-5 mb-8">
        <div className="w-20 h-20 rounded-full bg-ink/10 flex-shrink-0 flex items-center justify-center text-3xl font-serif font-bold text-ink/50 overflow-hidden">
          {p.avatar_url
            ? <img src={p.avatar_url} alt={p.name} className="w-full h-full object-cover" />
            : p.name.charAt(0)
          }
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-serif font-bold text-3xl text-ink">{p.name}</h1>
            <span className={clsx('text-sm rounded px-2 py-0.5 font-medium', PARTY_COLORS[p.party])}>
              {PARTY_SHORT[p.party]}
            </span>
          </div>
          <p className="text-ink/60 mt-1">{p.role}{p.region ? `・${p.region}` : ''}</p>
          {p.bio && <p className="text-sm text-ink/70 mt-3 leading-relaxed">{p.bio}</p>}
        </div>
      </div>

      {/* Trust meter */}
      <div className="bg-white/60 border border-ink/10 rounded-lg p-5 mb-8">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-ink">信任指數</span>
          <span className="font-mono text-lg font-bold text-ink">{p.trust_score}</span>
        </div>
        <TrustMeter score={p.trust_score} showLabel={false} />
        <div className="grid grid-cols-4 gap-2 mt-4 text-center">
          {[
            { label: '已兌現', count: statusCounts.fulfilled, color: 'text-status-fulfilled' },
            { label: '進行中', count: statusCounts.active, color: 'text-status-active' },
            { label: '停滯中', count: statusCounts.stalled, color: 'text-status-stalled' },
            { label: '跳票', count: statusCounts.broken, color: 'text-status-broken' },
          ].map(({ label, count, color }) => (
            <div key={label}>
              <div className={clsx('text-xl font-mono font-bold', color)}>{count}</div>
              <div className="text-xs text-ink/50">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 分頁：承諾 / 投票 */}
      <Tabs defaultValue="promises">
        <TabsList>
          <TabsTrigger value="promises">承諾紀錄 ({promises.length})</TabsTrigger>
          <TabsTrigger value="votes">投票紀錄 ({votes.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="promises">
          <PromiseTimeline promises={promises} />
        </TabsContent>
        <TabsContent value="votes">
          <VoteRecord votes={votes} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
