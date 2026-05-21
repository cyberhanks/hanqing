interface Props {
  label: string
  value: string | number
  color?: "green" | "red" | "orange" | "blue" | "default"
}

const colorMap = {
  green:   "text-emerald-600",
  red:     "text-red-500",
  orange:  "text-amber-500",
  blue:    "text-blue-500",
  default: "text-gray-800",
}

export function StatCard({ label, value, color = "default" }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-4 px-2">
      <span className={`text-2xl font-bold font-mono ${colorMap[color]}`}>
        {value}
      </span>
      <span className="text-xs text-gray-400 mt-1">{label}</span>
    </div>
  )
}
