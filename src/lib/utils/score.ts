import type { PromiseStatus } from '@/types'

const STATUS_WEIGHT: Record<PromiseStatus, number> = {
  fulfilled: 20,
  active: 0,
  stalled: -5,
  broken: -20,
  unknown: 0,
}

export function calcTrustScore(
  base: number,
  promises: Array<{ status: PromiseStatus }>
): number {
  if (promises.length === 0) return base
  const delta = promises.reduce((acc, p) => acc + STATUS_WEIGHT[p.status], 0)
  return Math.max(0, Math.min(100, base + delta))
}

export function trustLabel(score: number): string {
  if (score >= 75) return '高度信任'
  if (score >= 50) return '一般信任'
  if (score >= 30) return '偏低'
  return '低度信任'
}

export function trustColor(score: number): string {
  if (score >= 75) return 'text-status-fulfilled'
  if (score >= 50) return 'text-status-active'
  if (score >= 30) return 'text-status-stalled'
  return 'text-status-broken'
}
