import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { checkRateLimit } from '@/lib/api/rate_limit'

export async function GET(req: NextRequest) {
  const apiKey = req.headers.get('x-api-key') ?? 'anonymous'
  const allowed = await checkRateLimit(apiKey)
  if (!allowed) {
    return NextResponse.json(
      { error: 'Rate limit exceeded.' },
      { status: 429 }
    )
  }

  const { searchParams } = new URL(req.url)
  const politicianId = searchParams.get('politician_id')
  const status       = searchParams.get('status')
  const topic        = searchParams.get('topic')
  const limit        = Math.min(parseInt(searchParams.get('limit')  ?? '50', 10), 200)
  const offset       = parseInt(searchParams.get('offset') ?? '0', 10)

  const supabase = await createClient()
  let query = supabase
    .from('promises')
    .select(
      `id, politician_id, summary, topic, status, deadline, source_url, source_name, source_date,
       confidence, keywords, scope, verified_at, created_at, updated_at,
       politicians(id, name, party)`,
      { count: 'exact' }
    )
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (politicianId) query = query.eq('politician_id', politicianId)
  if (status)       query = query.eq('status', status)
  if (topic)        query = query.ilike('topic', `%${topic}%`)

  const { data, count, error } = await query
  if (error) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }

  return NextResponse.json({
    data,
    meta: { total: count ?? 0, limit, offset },
  }, {
    headers: {
      'Cache-Control': 'public, s-maxage=120, stale-while-revalidate=300',
    },
  })
}
