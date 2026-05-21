import type { Metadata } from 'next'
import { AlertTriangle } from 'lucide-react'
import { createClient } from '@/lib/supabase/server'
import type { Event } from '@/types'
import { formatDate } from '@/lib/utils/date'
import Badge from '@/components/ui/Badge'
import Card from '@/components/ui/Card'

export const metadata: Metadata = { title: '爭議事件' }

async function getEvents(): Promise<Event[]> {
  const supabase = await createClient()
  const { data } = await supabase
    .from('events')
    .select('*, event_politicians(politician:politicians(id,name,party))')
    .order('event_date', { ascending: false })
  return (data ?? []) as Event[]
}

const SEVERITY_COLORS = ['', 'text-yellow-500', 'text-orange-400', 'text-orange-500', 'text-red-500', 'text-red-600']

export default async function EventsPage() {
  const events = await getEvents()

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="font-serif font-bold text-2xl text-ink mb-2">爭議事件</h1>
      <p className="text-ink/50 text-sm mb-8">記錄有來源佐證的重要爭議、醜聞與失言事件</p>

      {events.length === 0 ? (
        <div className="text-center py-16 text-ink/40">
          <AlertTriangle className="w-8 h-8 mx-auto mb-3 opacity-40" />
          <p>尚無爭議事件紀錄</p>
        </div>
      ) : (
        <div className="space-y-4">
          {events.map(e => (
            <Card key={e.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`font-mono font-bold text-base ${SEVERITY_COLORS[e.severity] ?? 'text-ink'}`}>
                    {'▲'.repeat(e.severity)}
                  </span>
                  {e.event_type && <Badge>{e.event_type}</Badge>}
                  {e.status === 'resolved' && <Badge variant="fulfilled">已解決</Badge>}
                  {e.status === 'dismissed' && <Badge variant="unknown">已撤銷</Badge>}
                </div>
                {e.event_date && (
                  <span className="text-xs text-ink/40 flex-shrink-0">{formatDate(e.event_date)}</span>
                )}
              </div>
              <h2 className="font-serif font-semibold text-ink mt-2">{e.title}</h2>
              {e.description && (
                <p className="text-sm text-ink/70 mt-2 leading-relaxed">{e.description}</p>
              )}
              {e.source_url && (
                <a href={e.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-xs text-ink/40 hover:text-ink mt-3 inline-flex items-center gap-1">
                  查看來源 {e.source_name && `・${e.source_name}`}
                </a>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
