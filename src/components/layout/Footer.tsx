import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="border-t border-ink/10 mt-16 py-8 bg-paper-dark">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ink/40">
          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-ink/60">汗青 HanQing</span>
            <span>・台灣政治人物公民監督平台</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/politicians" className="hover:text-ink/70">政治人物</Link>
            <Link href="/promises" className="hover:text-ink/70">承諾追蹤</Link>
            <Link href="/events" className="hover:text-ink/70">爭議事件</Link>
          </div>
          <p>資料來源均附原始連結，本站政治中立，不代表任何黨派立場。</p>
        </div>
      </div>
    </footer>
  )
}
