'use client'
import { useState } from 'react'
import { Bell } from 'lucide-react'

interface Props {
  politicianId?: string
  politicianName?: string
}

export default function SubscribeForm({ politicianId, politicianName }: Props) {
  const [email, setEmail]     = useState('')
  const [status, setStatus]   = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email) return
    setStatus('loading')
    try {
      const res = await fetch('/api/webhooks/notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, politician_id: politicianId }),
      })
      if (res.ok) {
        setStatus('done')
        setMessage('訂閱成功！承諾狀態更新時將通知你。')
      } else {
        throw new Error('訂閱失敗')
      }
    } catch {
      setStatus('error')
      setMessage('訂閱失敗，請稍後再試。')
    }
  }

  if (status === 'done') {
    return (
      <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 rounded-lg px-4 py-3">
        <Bell className="w-4 h-4" />
        {message}
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder={`訂閱${politicianName ? ` ${politicianName}` : ''}的動態`}
        className="flex-1 px-3 py-2 text-sm border border-ink/20 rounded-md bg-white focus:outline-none focus:border-ink/40"
        required
      />
      <button
        type="submit"
        disabled={status === 'loading'}
        className="flex items-center gap-1.5 px-3 py-2 bg-ink text-paper text-sm rounded-md hover:bg-ink/80 disabled:opacity-50 whitespace-nowrap"
      >
        <Bell className="w-3.5 h-3.5" />
        {status === 'loading' ? '訂閱中...' : '訂閱通知'}
      </button>
      {status === 'error' && <p className="text-xs text-red-500 mt-1">{message}</p>}
    </form>
  )
}
