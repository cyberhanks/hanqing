export type Party = 'DPP' | 'KMT' | 'TPP' | 'IND' | 'OTHER'
export type PromiseStatus = 'active' | 'fulfilled' | 'broken' | 'stalled' | 'unknown'
export type VotePosition = '贊成' | '反對' | '棄權' | '缺席'

export interface Politician {
  id: string
  name: string
  name_en?: string
  party: Party
  role: string
  region?: string
  avatar_url?: string
  trust_score: number
  consistency_score?: number
  fulfill_rate?: number
  response_rate?: number
  total_promises?: number
  fulfilled_count?: number
  broken_count?: number
  stalled_count?: number
  total_votes?: number
  absent_count?: number
  data_source?: string
  last_synced_at?: string
  term_start?: string
  term_end?: string
  bio?: string
}

export interface Promise {
  id: string
  politician_id: string
  text: string
  summary?: string
  topic?: string
  deadline?: string
  status: PromiseStatus
  source_url?: string
  source_name?: string
  source_date?: string
  confidence?: number
  evidence_url?: string
  evidence_title?: string
  verification_hint?: string
  verified_at?: string
  keywords?: string[]
  scope?: string
  created_at: string
  updated_at: string
  politician?: Politician
}

export interface Donation {
  id: string
  politician_id: string
  donor_name: string
  amount: number
  donation_date?: string
  donor_industry?: string
  report_year: number
  source_url?: string
}

export interface AssetDeclaration {
  id: string
  politician_id: string
  declared_year: number
  total_assets?: number
  total_liabilities?: number
  asset_detail?: Record<string, unknown>
  declared_at?: string
  source_url?: string
}

export interface Subscription {
  id: string
  email: string
  politician_id?: string
  topic?: string
  created_at: string
}

export interface ApiKey {
  id: string
  key_hash: string
  label?: string
  daily_limit: number
  usage_today: number
  last_used_at?: string
  created_at: string
}

export interface Statement {
  id: string
  politician_id: string
  content: string
  summary?: string
  topic?: string
  source_url?: string
  source_name?: string
  statement_date?: string
  statement_type?: string
}

export interface Vote {
  id: string
  politician_id: string
  bill_name: string
  bill_id?: string
  vote_date?: string
  position: VotePosition
  source_url?: string
}

export interface Event {
  id: string
  title: string
  description?: string
  event_date?: string
  event_type: string
  severity: number
  status: string
  source_url?: string
  source_name?: string
  politicians?: Politician[]
}

export interface SearchResult {
  type: 'politician' | 'promise' | 'statement'
  id: string
  title: string
  excerpt: string
  politician?: Pick<Politician, 'id' | 'name' | 'party'>
}
