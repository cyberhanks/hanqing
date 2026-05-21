import { clsx } from 'clsx'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export default function Card({ children, className, hover = false }: CardProps) {
  return (
    <div className={clsx(
      'rounded-lg border border-ink/10 bg-white/60 p-5',
      hover && 'transition-shadow hover:shadow-md hover:border-ink/20',
      className
    )}>
      {children}
    </div>
  )
}
