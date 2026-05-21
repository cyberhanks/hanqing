import Link from 'next/link'
import { ExternalLink } from 'lucide-react'
import type { Promise as HQPromise } from '@/types'
import PromiseStatusBadge from './PromiseStatus'
import Badge from '@/components/ui/Badge'
import Card from '@/components/ui/Card'
import { formatDate } from '@/lib/utils/date'

interface PromiseCardProps {
  promise: HQPromise
  showPolitician?: boolean
}

export default function PromiseCard({ promise: p, showPolitician = false }: PromiseCardProps) {
  return (
    <Card className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <PromiseStatusBadge status={p.status} />
          {p.topic && <Badge>{p.topic}</Badge>}
          {showPolitician && p.politician && (
            <Link href={`/politicians/${p.politician.id}`} className="text-xs text-ink/60 hover:text-ink underline">
              {p.politician.name}
            </Link>
          )}
        </div>
        {p.source_url && (
          <a href={p.source_url} target="_blank" rel="noopener noreferrer" className="text-ink/30 hover:text-ink/60 flex-shrink-0">
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      <p className="text-sm text-ink leading-relaxed">{p.text}</p>

      {p.summary && p.summary !== p.text && (
        <p className="text-xs text-ink/60 border-l-2 border-ink/15 pl-3">{p.summary}</p>
      )}

      <div className="flex items-center gap-3 text-xs text-ink/40">
        {p.source_name && <span>來源：{p.source_name}</span>}
        {p.source_date && <span>{formatDate(p.source_date)}</span>}
        {p.deadline && <span>期限：{p.deadline}</span>}
      </div>
    </Card>
  )
}
