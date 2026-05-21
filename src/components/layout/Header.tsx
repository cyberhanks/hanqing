import Link from 'next/link'
import { Scale } from 'lucide-react'
import SearchBox from '@/components/ui/SearchBox'

const NAV = [
  { href: '/politicians', label: '政治人物' },
  { href: '/promises',    label: '承諾追蹤' },
  { href: '/events',      label: '爭議事件' },
]

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-ink/10 bg-paper/90 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center gap-4 h-14">
          <Link href="/" className="flex items-center gap-2 flex-shrink-0">
            <Scale className="w-5 h-5 text-ink" />
            <span className="font-serif font-bold text-lg tracking-wide text-ink">汗青</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1 ml-2">
            {NAV.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="px-3 py-1.5 text-sm text-ink/70 hover:text-ink hover:bg-ink/5 rounded transition-colors"
              >
                {label}
              </Link>
            ))}
          </nav>

          <div className="flex-1 max-w-xs ml-auto">
            <SearchBox />
          </div>
        </div>
      </div>
    </header>
  )
}
