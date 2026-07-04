import type { ReactNode } from 'react'

import type { PortType } from '../lib/types'

function renderText(value: string): ReactNode {
  return <div className="whitespace-pre-wrap">{value}</div>
}

function renderJson(value: string): ReactNode {
  try {
    const parsed = JSON.parse(value) as unknown
    return (
      <pre className="hide-scrollbar max-h-64 overflow-auto text-xs">
        {JSON.stringify(parsed, null, 2)}
      </pre>
    )
  } catch {
    // Malformed/legacy string; degrade to plain text rather than crashing.
    return renderText(value)
  }
}

// Registry keyed by PortType. Adding real FILE/LIST-producing node types later
// only needs a new entry here (e.g. a file preview/download link, list of
// cards) — not a redesign. Until then they fall back to plain text below.
const RENDERERS: Partial<Record<PortType, (value: string) => ReactNode>> = {
  text: renderText,
  json: renderJson,
}

interface OutputRendererProps {
  value: string
  portType?: PortType | null
}

export function OutputRenderer({ value, portType }: OutputRendererProps) {
  const renderer = (portType && RENDERERS[portType]) ?? renderText
  return <>{renderer(value)}</>
}
