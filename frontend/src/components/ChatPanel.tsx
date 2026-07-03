import { useEffect, useMemo, useRef, useState } from 'react'

import type { LiveTokens } from '../hooks/useExecutions'
import type { Execution, ExecutionStatus, RunInputPayload } from '../lib/types'

// Executions in these states are still being processed by the worker.
const ACTIVE_STATUSES: ExecutionStatus[] = ['created', 'running']

interface ChatPanelProps {
  workflowName: string
  hasWorkflow: boolean
  executions: Execution[]
  liveTokens: LiveTokens
  lastExecution: Execution | null
  runEnabled: boolean
  runDisabledReason: string | null
  loading: boolean
  onRun: (input: RunInputPayload) => void
}

interface ChatTurn {
  id: number
  status: ExecutionStatus
  input: string
  output: string
  error: string | null
  isActive: boolean
}

function joinLiveTokens(liveTokens: LiveTokens): string {
  return Object.entries(liveTokens)
    .sort(([first], [second]) => Number(first) - Number(second))
    .map(([, value]) => value)
    .join('\n\n')
}

function buildTurns(
  executions: Execution[],
  activeId: number | null,
  liveText: string,
): ChatTurn[] {
  return [...executions]
    .sort((first, second) => first.id - second.id)
    .map((execution) => {
      const isActive = execution.id === activeId
      const streamed =
        isActive && liveText ? liveText : String(execution.output_data?.value ?? '')
      return {
        id: execution.id,
        status: execution.status,
        input: String(execution.input_data?.value ?? ''),
        output: streamed,
        error: execution.error,
        isActive,
      }
    })
}

export function ChatPanel({
  workflowName,
  hasWorkflow,
  executions,
  liveTokens,
  lastExecution,
  runEnabled,
  runDisabledReason,
  loading,
  onRun,
}: ChatPanelProps) {
  const [draft, setDraft] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const activeExecutionId = useMemo(
    () =>
      lastExecution && ACTIVE_STATUSES.includes(lastExecution.status)
        ? lastExecution.id
        : null,
    [lastExecution],
  )
  const isRunning = activeExecutionId !== null
  const liveText = joinLiveTokens(liveTokens)

  const turns = useMemo(
    () => buildTurns(executions, activeExecutionId, liveText),
    [executions, activeExecutionId, liveText],
  )

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  const canSend = runEnabled && !isRunning && !loading && draft.trim().length > 0

  function handleSend(): void {
    if (!canSend) {
      return
    }
    onRun({ value: draft.trim() })
    setDraft('')
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const placeholder = !hasWorkflow
    ? 'Select a workflow in Build mode first.'
    : runDisabledReason ?? 'Type a message to run the flow...'

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="mb-3 flex items-center justify-between">
        <div className="pixel-section-title">Chat · {workflowName}</div>
        {isRunning ? (
          <div className="flex items-center gap-2">
            <span className="live-dot" />
            <span className="text-xs text-[var(--muted)]">running…</span>
          </div>
        ) : null}
      </div>

      <div className="pixel-scroll flex-1 overflow-y-auto pr-1">
        {turns.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--muted)]">
            {hasWorkflow
              ? 'No runs yet. Send a message to test this flow.'
              : 'Select a workflow in Build mode to start chatting.'}
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {turns.map((turn) => (
              <ChatTurnView key={turn.id} turn={turn} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="mt-3 border-t border-white/10 pt-3">
        <div className="flex items-end gap-2">
          <textarea
            className="pixel-textarea min-h-[56px] flex-1"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!hasWorkflow || !runEnabled || isRunning || loading}
            placeholder={placeholder}
          />
          <button
            type="button"
            className="pixel-button small"
            disabled={!canSend}
            onClick={handleSend}
          >
            {isRunning ? 'Running…' : 'Send'}
          </button>
        </div>
        {hasWorkflow && runDisabledReason ? (
          <div className="mt-2 text-xs text-[var(--danger)]">{runDisabledReason}</div>
        ) : null}
      </div>
    </div>
  )
}

function ChatTurnView({ turn }: { turn: ChatTurn }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-end">
        <div className="pixel-panel max-w-[80%] whitespace-pre-wrap px-3 py-2 text-sm">
          {turn.input || <span className="text-[var(--muted)]">(empty input)</span>}
        </div>
      </div>
      <div className="flex justify-start">
        <ChatTurnResponse turn={turn} />
      </div>
    </div>
  )
}

function ChatTurnResponse({ turn }: { turn: ChatTurn }) {
  if (turn.status === 'failed') {
    return (
      <div className="pixel-error max-w-[80%] whitespace-pre-wrap text-sm">
        {turn.error ?? 'Execution failed.'}
      </div>
    )
  }

  if (turn.status === 'success' || turn.output) {
    return (
      <div className="pixel-panel max-w-[80%] whitespace-pre-wrap border-[rgba(53,255,188,0.4)] px-3 py-2 text-sm">
        {turn.output}
        {turn.isActive ? <span className="live-dot ml-2 inline-block align-middle" /> : null}
      </div>
    )
  }

  return (
    <div className="pixel-panel flex max-w-[80%] items-center gap-2 px-3 py-2 text-sm text-[var(--muted)]">
      <span className="live-dot" />
      thinking…
    </div>
  )
}
