import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { checkRateLimit } from '@/lib/api/rate_limit'

export async function GET(req: NextRequest) {
  // Rate limiting
  const apiKey = req.headers.get('x-api-key') ?? 'anonymous'
  const allowed = await checkRateLimit(apiKey)
  if (!allowed) {
    return NextResponse.json(
      { error: 'Rate limit exceeded. Upgrade your plan or try again tomorrow.' },
      { status: 429 }
    )
  }

  const { searchParams } = new URL(req.url)
  const party  = searchParams.get('party')
  const limit  = Math.min(parseInt(searchParams.get('limit')  ?? '50', 10), 200)
  const offset = parseInt(searchParams.get('offset') ?? '0', 10)

  const supabase = await createClient()
  let query = supabase
    .from('politicians')
    .select(
      'id, name, name_en, party, role, region, trust_score, consistency_score, fulfill_rate, total_promises, fulfilled_count, broken_count, last_synced_at',
      { count: 'exact' }
    )
    .order('trust_score', { ascending: false })
    .range(offset, offset + limit - 1)

  if (party) query = query.eq('party', party.toUpperCase())

  const { data, count, error } = await query
  if (error) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }

  return NextResponse.json({
    data,
    meta: { total: count ?? 0, limit, offset },
  }, {
    headers: {
      'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600',
    },
  })
}
