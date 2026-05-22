/**
 * 信任指數計算邏輯（前端版）
 * 伺服器端完整版見 pipeline/processors/consistency.py
 */
export interface TrustComponents {
  fulfillRate: number      // 0–100
  consistencyScore: number // 0–100
  totalPromises: number
  brokenCount: number
  stalledCount: number
}

export function calculateTrustScore(c: TrustComponents): number {
  if (c.totalPromises === 0) return 50

  // 基礎分：兌現率 60% + 一致性 40%
  let score = c.fulfillRate * 0.6 + c.consistencyScore * 0.4

  // 懲罰：每筆跳票 -5（最多 -30）
  const brokenPenalty = Math.min(c.brokenCount * 5, 30)
  // 懲罰：每筆停滯 -2（最多 -15）
  const stalledPenalty = Math.min(c.stalledCount * 2, 15)

  score = Math.max(0, Math.min(100, score - brokenPenalty - stalledPenalty))
  return Math.round(score)
}

export function getTrustLabel(score: number): string {
  if (score >= 80) return '高度可信'
  if (score >= 60) return '尚可'
  if (score >= 40) return '存疑'
  return '低可信度'
}

export function getTrustColor(score: number): string {
  if (score >= 80) return 'text-status-fulfilled'
  if (score >= 60) return 'text-ink/70'
  if (score >= 40) return 'text-status-stalled'
  return 'text-status-broken'
}
