"use client"

import { createContext, useContext, useState } from "react"
import { clsx } from "clsx"

const TabsCtx = createContext<{ active: string; setActive: (v: string) => void }>({
  active: "", setActive: () => {}
})

export function Tabs({ defaultValue, children }: { defaultValue: string; children: React.ReactNode }) {
  const [active, setActive] = useState(defaultValue)
  return <TabsCtx.Provider value={{ active, setActive }}>{children}</TabsCtx.Provider>
}

export function TabsList({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-1 border-b border-gray-200 mb-4">
      {children}
    </div>
  )
}

export function TabsTrigger({ value, children }: { value: string; children: React.ReactNode }) {
  const { active, setActive } = useContext(TabsCtx)
  return (
    <button
      onClick={() => setActive(value)}
      className={clsx(
        "px-4 py-2 text-sm font-mono tracking-wide border-b-2 -mb-px transition-colors",
        active === value
          ? "border-ink text-ink"
          : "border-transparent text-gray-400 hover:text-gray-600"
      )}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children }: { value: string; children: React.ReactNode }) {
  const { active } = useContext(TabsCtx)
  if (active !== value) return null
  return <div>{children}</div>
}
