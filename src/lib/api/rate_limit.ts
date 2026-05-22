/**
 * API 限流（基於 Supabase api_keys 表）
 * 免費方案：每日 1000 次
 */
import { createClient } from '@/lib/supabase/server'
import crypto from 'crypto'

const ANONYMOUS_LIMIT = 100  // 匿名每日上限

export async function checkRateLimit(apiKey: string): Promise<boolean> {
  if (apiKey === 'anonymous') {
    // 匿名請求：用 IP 限流（簡易版，生產環境可接 Redis）
    return true  // TODO: 實作 IP 限流
  }

  const supabase = await createClient()
  const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex')

  const { data } = await supabase
    .from('api_keys')
    .select('daily_limit, usage_today, last_used_at')
    .eq('key_hash', keyHash)
    .single()

  if (!data) return false  // 無效 key

  const today = new Date().toDateString()
  const lastUsed = data.last_used_at ? new Date(data.last_used_at).toDateString() : ''

  // 跨日重置
  const usageToday = lastUsed === today ? data.usage_today : 0

  if (usageToday >= data.daily_limit) return false

  // 更新使用次數
  await supabase
    .from('api_keys')
    .update({
      usage_today: usageToday + 1,
      last_used_at: new Date().toISOString(),
    })
    .eq('key_hash', keyHash)

  return true
}
