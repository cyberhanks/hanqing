import Link from 'next/link'
import { clsx } from 'clsx'
import type { Politician } from '@/types'
import { PARTY_SHORT, PARTY_COLORS, PARTY_BORDER } from '@/lib/utils/party'
import TrustMeter from './TrustMeter'
import Card from '@/components/ui/Card'

interface PoliticianCardProps {
  politician: Politician
}

export default function PoliticianCard({ politician: p }: PoliticianCardProps) {
  return (
    <Link href={`/politicians/${p.id}`}>
      <Card hover className={clsx('border-l-4 h-full', PARTY_BORDER[p.party])}>
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-full bg-ink/10 flex-shrink-0 flex items-center justify-center text-lg font-serif font-bold text-ink/60 overflow-hidden">
            {p.avatar_url
              ? <img src={p.avatar_url} alt={p.name} className="w-full h-full object-cover" />
              : p.name.charAt(0)
            }
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-serif font-bold text-base text-ink">{p.name}</h3>
              <span className={clsx('text-xs rounded px-1.5 py-0.5 font-medium', PARTY_COLORS[p.party])}>
                {PARTY_SHORT[p.party]}
              </span>
            </div>
            <p className="text-xs text-ink/60 mt-0.5">{p.role}{p.region ? `・${p.region}` : ''}</p>
          </div>
        </div>
        <div className="mt-4">
          <p className="text-xs text-ink/50 mb-1">信任指數</p>
          <TrustMeter score={p.trust_score} />
        </div>
        {p.bio && (
          <p className="mt-3 text-xs text-ink/60 line-clamp-2">{p.bio}</p>
        )}
      </Card>
    </Link>
  )
}
