import { createClient } from '@/lib/supabase/server'
import { CheckCircle2, AlertTriangle, Users, Clock } from 'lucide-react'

export default async function GlobalStats() {
  const supabase = await createClient()

  const [politiciansRes, promisesRes] = await Promise.all([
    supabase.from('politicians').select('id', { count: 'exact', head: true }),
    supabase.from('promises').select('status'),
  ])

  const promises = promisesRes.data || []
  const total     = promises.length
  const fulfilled = promises.filter(p => p.status === 'fulfilled').length
  const broken    = promises.filter(p => p.status === 'broken').length
  const active    = promises.filter(p => p.status === 'active').length

  const stats = [
    { icon: Users,        label: '受監督人物', value: politiciansRes.count ?? 0,  color: 'text-ink' },
    { icon: CheckCircle2, label: '已兌現承諾', value: fulfilled,                   color: 'text-green-600' },
    { icon: AlertTriangle,label: '已跳票承諾', value: broken,                      color: 'text-red-500' },
    { icon: Clock,        label: '追蹤中承諾', value: active,                      color: 'text-amber-500' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map(({ icon: Icon, label, value, color }) => (
        <div key={label} className="bg-white/60 rounded-lg border border-ink/10 p-4 text-center">
          <Icon className={`w-5 h-5 mx-auto mb-1.5 ${color}`} />
          <div className={`text-2xl font-mono font-bold ${color}`}>{value.toLocaleString()}</div>
          <div className="text-xs text-ink/50 mt-0.5">{label}</div>
        </div>
      ))}
    </div>
  )
}
