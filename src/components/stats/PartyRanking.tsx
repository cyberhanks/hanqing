import { createClient } from '@/lib/supabase/server'

const PARTY_NAME: Record<string, string> = {
  DPP: '民進黨', KMT: '國民黨', TPP: '民眾黨',
  NPP: '時代力量', TSP: '台灣基進', IND: '無黨籍',
  NPSU: '無黨團結', OTHER: '其他',
}

const PARTY_COLOR: Record<string, string> = {
  DPP: '#1B9431', KMT: '#000095', TPP: '#28C8C8',
  NPP: '#FBBE01', TSP: '#C00000', IND: '#888888',
  OTHER: '#AAAAAA',
}

export default async function PartyRanking() {
  const supabase = await createClient()
  const { data: politicians } = await supabase
    .from('politicians')
    .select('party, trust_score, consistency_score, fulfill_rate')

  if (!politicians?.length) return null

  const stats: Record<string, { count: number; trust: number; consistency: number; fulfill: number }> = {}
  for (const p of politicians) {
    if (!stats[p.party]) stats[p.party] = { count: 0, trust: 0, consistency: 0, fulfill: 0 }
    stats[p.party].count++
    stats[p.party].trust       += p.trust_score || 50
    stats[p.party].consistency += p.consistency_score || 50
    stats[p.party].fulfill     += parseFloat(p.fulfill_rate as unknown as string) || 0
  }

  const rankings = Object.entries(stats)
    .map(([party, s]) => ({
      party,
      name:          PARTY_NAME[party] || party,
      color:         PARTY_COLOR[party] || '#888',
      count:         s.count,
      avgTrust:      Math.round(s.trust / s.count),
      avgConsistency: Math.round(s.consistency / s.count),
      avgFulfill:    Math.round(s.fulfill / s.count * 10) / 10,
    }))
    .filter(r => r.count >= 1)
    .sort((a, b) => b.avgTrust - a.avgTrust)

  return (
    <div className="bg-white/60 rounded-lg border border-ink/10 overflow-hidden">
      <div className="px-5 py-3 border-b border-ink/10">
        <h3 className="font-serif font-bold text-ink text-sm">黨派信任指數排名</h3>
      </div>
      <div className="divide-y divide-ink/5">
        {rankings.map((r, i) => (
          <div key={r.party} className="flex items-center gap-4 px-5 py-3">
            <span className="text-ink/30 font-mono text-xs w-4">{i + 1}</span>
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: r.color }}
            />
            <span className="font-medium text-sm flex-1">{r.name}</span>
            <span className="text-xs text-ink/40">{r.count} 人</span>
            <div className="text-right">
              <div className="font-mono font-bold text-sm">{r.avgTrust}</div>
              <div className="text-xs text-ink/40">信任指數</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
