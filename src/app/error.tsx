'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-paper">
      <div className="text-center p-8 max-w-md">
        <h2 className="text-2xl font-serif font-bold text-ink mb-2">暫時無法載入</h2>
        <p className="text-ink/50 text-sm mb-6">{error.message || '資料庫連線錯誤，請稍後再試'}</p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-ink text-paper rounded-md text-sm hover:bg-ink/80"
        >
          重新載入
        </button>
      </div>
    </div>
  )
}
