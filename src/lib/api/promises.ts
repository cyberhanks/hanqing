import { createClient } from '@/lib/supabase/server'
import type { Promise as HQPromise, PromiseStatus } from '@/types'

export async function getPromises(opts?: {
  politicianId?: string
  status?: PromiseStatus
  topic?: string
}): Promise<HQPromise[]> {
  const supabase = await createClient()
  let query = supabase
    .from('promises')
    .select('*, politician:politicians(id,name,party,role)')
    .order('created_at', { ascending: false })
  if (opts?.politicianId) query = query.eq('politician_id', opts.politicianId)
  if (opts?.status) query = query.eq('status', opts.status)
  if (opts?.topic) query = query.eq('topic', opts.topic)
  const { data, error } = await query
  if (error) throw error
  return data as HQPromise[]
}
