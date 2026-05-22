import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export async function POST(req: NextRequest) {
  let body: { email?: string; politician_id?: string; topic?: string }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const { email, politician_id, topic } = body

  if (!email || !isValidEmail(email)) {
    return NextResponse.json({ error: '請提供有效的 email' }, { status: 400 })
  }

  const supabase = await createClient()

  // Check if already subscribed to this exact combination
  const { data: existing } = await supabase
    .from('subscriptions')
    .select('id')
    .eq('email', email)
    .eq('politician_id', politician_id ?? null)
    .maybeSingle()

  if (existing) {
    // Already subscribed — return success silently (avoid user enumeration)
    return NextResponse.json({ ok: true, message: '訂閱成功' })
  }

  const { error } = await supabase
    .from('subscriptions')
    .insert({
      email,
      politician_id: politician_id ?? null,
      topic: topic ?? null,
    })

  if (error) {
    console.error('[notify] insert error:', error)
    return NextResponse.json({ error: '訂閱失敗，請稍後再試' }, { status: 500 })
  }

  return NextResponse.json({ ok: true, message: '訂閱成功' })
}
