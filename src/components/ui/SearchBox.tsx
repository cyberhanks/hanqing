'use client'
import { Search } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

interface SearchBoxProps {
  placeholder?: string
  defaultValue?: string
  className?: string
}

export default function SearchBox({ placeholder = '搜尋政治人物、承諾、發言…', defaultValue = '', className }: SearchBoxProps) {
  const router = useRouter()
  const [q, setQ] = useState(defaultValue)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <form onSubmit={handleSubmit} className={className}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40" />
        <input
          type="search"
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder={placeholder}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-ink/15 bg-white/80 text-sm placeholder:text-ink/40 focus:outline-none focus:border-ink/40 focus:ring-1 focus:ring-ink/20"
        />
      </div>
    </form>
  )
}
