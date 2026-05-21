import { NextResponse } from 'next/server'
import { search } from '@/lib/api/search'

export async function GET(req: Request) {
  const url = new URL(req.url)
  const q = url.searchParams.get('q') ?? ''
  try {
    const results = await search(q)
    return NextResponse.json(results)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Search failed'
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
