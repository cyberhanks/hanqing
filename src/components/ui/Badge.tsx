import { clsx } from 'clsx'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'fulfilled' | 'broken' | 'stalled' | 'active' | 'unknown'
  className?: string
}

const variants = {
  default: 'bg-ink/10 text-ink',
  fulfilled: 'bg-status-fulfilled/15 text-status-fulfilled',
  broken: 'bg-status-broken/15 text-status-broken',
  stalled: 'bg-status-stalled/15 text-status-stalled',
  active: 'bg-status-active/15 text-status-active',
  unknown: 'bg-status-unknown/15 text-status-unknown',
}

export default function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center rounded px-2 py-0.5 text-xs font-medium',
      variants[variant],
      className
    )}>
      {children}
    </span>
  )
}
