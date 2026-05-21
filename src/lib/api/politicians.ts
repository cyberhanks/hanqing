import { createClient } from '@/lib/supabase/server'
import type { Politician } from '@/types'

export async function getPoliticians(party?: string): Promise<Politician[]> {
  const supabase = await createClient()
  let query = supabase.from('politicians').select('*').order('trust_score', { ascending: false })
  if (party && party !== 'ALL') query = query.eq('party', party)
  const { data, error } = await query
  if (error) throw error
  return data as Politician[]
}

export async function getPolitician(id: string): Promise<Politician | null> {
  const supabase = await createClient()
  const { data, error } = await supabase
    .from('politicians')
    .select('*')
    .eq('id', id)
    .single()
  if (error) return null
  return data as Politician
}
