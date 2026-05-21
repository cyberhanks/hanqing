import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET(req: Request) {
  const url = new URL(req.url)
  const party = url.searchParams.get('party')
  const supabase = await createClient()

  let query = supabase.from('politicians').select('*').order('trust_score', { ascending: false })
  if (party && party !== 'ALL') query = query.eq('party', party)

  const { data, error } = await query
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
