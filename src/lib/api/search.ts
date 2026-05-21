import { createClient } from '@/lib/supabase/server'
import type { SearchResult } from '@/types'

export async function search(q: string): Promise<SearchResult[]> {
  if (!q.trim()) return []
  const supabase = await createClient()

  const [{ data: politicians }, { data: promises }] = await Promise.all([
    supabase
      .from('politicians')
      .select('id, name, party, role, bio')
      .or(`name.ilike.%${q}%,bio.ilike.%${q}%`)
      .limit(5),
    supabase
      .from('promises')
      .select('id, text, summary, politician_id, politician:politicians(id,name,party)')
      .ilike('text', `%${q}%`)
      .limit(10),
  ])

  const results: SearchResult[] = []

  for (const p of politicians ?? []) {
    results.push({
      type: 'politician',
      id: p.id,
      title: p.name,
      excerpt: p.bio?.slice(0, 80) ?? p.role,
      politician: { id: p.id, name: p.name, party: p.party },
    })
  }

  for (const pr of promises ?? []) {
    results.push({
      type: 'promise',
      id: pr.id,
      title: pr.summary ?? pr.text.slice(0, 40),
      excerpt: pr.text.slice(0, 100),
      politician: pr.politician as unknown as SearchResult['politician'],
    })
  }

  return results
}
