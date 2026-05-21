import type { Party } from '@/types'

export const PARTY_LABELS: Record<Party, string> = {
  DPP: '民主進步黨',
  KMT: '中國國民黨',
  TPP: '台灣民眾黨',
  IND: '無黨籍',
  OTHER: '其他',
}

export const PARTY_SHORT: Record<Party, string> = {
  DPP: '民進黨',
  KMT: '國民黨',
  TPP: '民眾黨',
  IND: '無黨籍',
  OTHER: '其他',
}

export const PARTY_COLORS: Record<Party, string> = {
  DPP: 'bg-party-dpp text-white',
  KMT: 'bg-party-kmt text-white',
  TPP: 'bg-party-tpp text-white',
  IND: 'bg-party-ind text-white',
  OTHER: 'bg-gray-500 text-white',
}

export const PARTY_BORDER: Record<Party, string> = {
  DPP: 'border-party-dpp',
  KMT: 'border-party-kmt',
  TPP: 'border-party-tpp',
  IND: 'border-party-ind',
  OTHER: 'border-gray-400',
}
