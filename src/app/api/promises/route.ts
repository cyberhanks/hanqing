import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET(req: Request) {
  const url = new URL(req.url)
  const politicianId = url.searchParams.get('politician_id')
  const status = url.searchParams.get('status')
  const supabase = await createClient()

  let query = supabase
    .from('promises')
    .select('*, politician:politicians(id,name,party,role)')
    .order('created_at', { ascending: false })
  if (politicianId) query = query.eq('politician_id', politicianId)
  if (status) query = query.eq('status', status)

  const { data, error } = await query
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
