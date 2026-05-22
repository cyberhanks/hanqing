/**
 * 言行一致性分數工具
 */
export function getConsistencyLabel(score: number): string {
  if (score >= 80) return '言行一致'
  if (score >= 60) return '大致一致'
  if (score >= 40) return '有所落差'
  return '言行不一'
}

export function getConsistencyColor(score: number): string {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}
