import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { checkRateLimit } from '@/lib/api/rate_limit'

export async function GET(req: NextRequest) {
  const apiKey = req.headers.get('x-api-key') ?? 'anonymous'
  const allowed = await checkRateLimit(apiKey)
  if (!allowed) {
    return NextResponse.json({ error: 'Rate limit exceeded.' }, { status: 429 })
  }

  const q = req.nextUrl.searchParams.get('q')?.trim()
  if (!q || q.length < 2) {
    return NextResponse.json({ error: 'Query must be at least 2 characters.' }, { status: 400 })
  }

  const supabase = await createClient()

  const [politiciansRes, promisesRes] = await Promise.all([
    supabase
      .from('politicians')
      .select('id, name, party, role, region, trust_score')
      .or(`name.ilike.%${q}%,bio.ilike.%${q}%`)
      .limit(10),
    supabase
      .from('promises')
      .select('id, politician_id, summary, topic, status, politicians(id, name, party)')
      .or(`summary.ilike.%${q}%,text.ilike.%${q}%,topic.ilike.%${q}%`)
      .limit(20),
  ])

  const results = [
    ...(politiciansRes.data ?? []).map(p => ({
      type: 'politician' as const,
      id: p.id,
      title: p.name,
      excerpt: `${p.role}${p.region ? `・${p.region}` : ''} | 信任指數 ${p.trust_score}`,
      politician: { id: p.id, name: p.name, party: p.party },
    })),
    ...(promisesRes.data ?? []).map(p => ({
      type: 'promise' as const,
      id: p.id,
      title: p.summary ?? p.topic ?? '承諾',
      excerpt: `狀態: ${p.status}`,
      politician: p.politicians as { id: string; name: string; party: string } | null,
    })),
  ]

  return NextResponse.json({ data: results, meta: { query: q, total: results.length } })
}
