import type { PromiseStatus } from "@/types"

const CONFIG: Record<PromiseStatus, { label: string; className: string }> = {
  fulfilled: { label: "已兌現", className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  broken:    { label: "已跳票", className: "bg-red-50 text-red-600 border-red-200" },
  stalled:   { label: "停滯中", className: "bg-amber-50 text-amber-600 border-amber-200" },
  active:    { label: "進行中", className: "bg-blue-50 text-blue-600 border-blue-200" },
  unknown:   { label: "不明",   className: "bg-gray-50 text-gray-500 border-gray-200" },
}

export function PromiseStatusBadge({ status }: { status: PromiseStatus }) {
  const cfg = CONFIG[status] ?? CONFIG.unknown
  return (
    <span className={`text-xs px-2 py-0.5 border rounded-sm font-mono ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}
