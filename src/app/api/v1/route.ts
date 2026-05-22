import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    version: 'v1',
    description: '汗青 HanQing 公開 API',
    endpoints: {
      politicians: {
        url: '/api/v1/politicians',
        method: 'GET',
        params: {
          party:  'DPP | KMT | TPP | IND | OTHER',
          limit:  'number (max 200, default 50)',
          offset: 'number (default 0)',
        },
      },
      promises: {
        url: '/api/v1/promises',
        method: 'GET',
        params: {
          politician_id: 'uuid',
          status:        'active | fulfilled | broken | stalled',
          topic:         'string (partial match)',
          limit:         'number (max 200, default 50)',
          offset:        'number (default 0)',
        },
      },
      search: {
        url: '/api/v1/search',
        method: 'GET',
        params: {
          q: 'string (min 2 chars)',
        },
      },
    },
    rateLimit: {
      anonymous: '匿名請求無需 API Key（受 IP 限制）',
      withKey:   '使用 x-api-key header 提升配額，聯繫我們申請 Key',
    },
    dataUpdated: '每週更新一次，每月完整重算',
  })
}
