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
  created_at: string
  updated_at: string
  politician?: Politician
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
