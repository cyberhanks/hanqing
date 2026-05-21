import type { PromiseStatus } from '@/types'
import Badge from '@/components/ui/Badge'

const STATUS_MAP: Record<PromiseStatus, { label: string; variant: 'fulfilled' | 'broken' | 'stalled' | 'active' | 'unknown' }> = {
  fulfilled: { label: '已兌現', variant: 'fulfilled' },
  broken:    { label: '跳票', variant: 'broken' },
  stalled:   { label: '停滯中', variant: 'stalled' },
  active:    { label: '進行中', variant: 'active' },
  unknown:   { label: '未知', variant: 'unknown' },
}

export default function PromiseStatusBadge({ status }: { status: PromiseStatus }) {
  const { label, variant } = STATUS_MAP[status] ?? STATUS_MAP.unknown
  return <Badge variant={variant}>{label}</Badge>
}
