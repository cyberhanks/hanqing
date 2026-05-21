import type { Vote } from "@/types"

const POSITION_STYLE: Record<string, string> = {
  "贊成": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "反對": "bg-red-50 text-red-600 border-red-200",
  "棄權": "bg-amber-50 text-amber-600 border-amber-200",
  "缺席": "bg-gray-50 text-gray-500 border-gray-200",
}

export function VoteRecord({ votes }: { votes: Vote[] }) {
  if (!votes.length) {
    return (
      <p className="text-center text-gray-400 py-12 text-sm">
        目前沒有投票紀錄
      </p>
    )
  }

  return (
    <div className="mt-4 space-y-2">
      {votes.map(vote => (
        <div key={vote.id}
          className="bg-white border border-gray-100 hover:border-gray-300
            transition-colors p-4 flex items-start gap-4">

          {/* 立場標籤 */}
          <span className={`
            text-xs px-2 py-1 border rounded-sm font-mono flex-shrink-0 mt-0.5
            ${POSITION_STYLE[vote.position] ?? "bg-gray-50 text-gray-500 border-gray-200"}
          `}>
            {vote.position}
          </span>

          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 leading-snug">
              {vote.bill_name}
            </p>
            <div className="flex items-center gap-3 mt-1.5">
              {vote.vote_date && (
                <span className="text-xs text-gray-400 font-mono">
                  {vote.vote_date}
                </span>
              )}
              {vote.bill_id && (
                <span className="text-xs text-gray-300 font-mono">
                  #{vote.bill_id}
                </span>
              )}
              {vote.source_url && (
                <a href={vote.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-xs text-gray-400 hover:text-gray-600 ml-auto">
                  查看原始紀錄 →
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
