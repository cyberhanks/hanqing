import { Suspense } from 'react'
import type { Metadata } from 'next'
import { getPoliticians } from '@/lib/api/politicians'
import PoliticianGrid from '@/components/politician/PoliticianGrid'
import PartyFilter from '@/components/filters/PartyFilter'

export const metadata: Metadata = { title: '政治人物' }

interface PageProps {
  searchParams: Promise<{ party?: string }>
}

export default async function PoliticiansPage({ searchParams }: PageProps) {
  const { party } = await searchParams
  const politicians = await getPoliticians(party)

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="font-serif font-bold text-2xl text-ink mb-6">政治人物</h1>
      <Suspense fallback={null}>
        <PartyFilter />
      </Suspense>
      <div className="mt-6">
        <PoliticianGrid politicians={politicians} />
      </div>
    </div>
  )
}
