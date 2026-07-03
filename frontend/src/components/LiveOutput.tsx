import type { LiveTokens } from '../hooks/useExecutions'

interface LiveOutputProps {
  liveTokens: LiveTokens
}

export function LiveOutput({ liveTokens }: LiveOutputProps) {
  const text = Object.entries(liveTokens)
    .sort(([first], [second]) => Number(first) - Number(second))
    .map(([, value]) => value)
    .join('\n\n')

  if (!text) {
    return null
  }

  return (
    <div className="pixel-panel fixed bottom-4 right-4 z-40 flex max-h-64 w-96 flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="live-dot" />
        <span className="pixel-section-title">Streaming</span>
      </div>
      <pre className="hide-scrollbar overflow-auto whitespace-pre-wrap text-xs text-[var(--text)]">
        {text}
      </pre>
    </div>
  )
}
