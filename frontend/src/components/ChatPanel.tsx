import { useEffect, useMemo, useRef, useState } from 'react'

import { getExecutionNodeResults, getWorkflowVersions } from '../lib/api'
import type { LiveTokens } from '../hooks/useExecutions'
import type {
  Execution,
  ExecutionStatus,
  NodeExecutionResult,
  PortType,
  RunInputPayload,
} from '../lib/types'
import { OutputRenderer } from './OutputRenderer'

export interface NodeMeta {
  type: string
  label: string
  portType: PortType | null
}

// Executions in these states are still being processed by the worker.
const ACTIVE_STATUSES: ExecutionStatus[] = ['created', 'running']

const STATUS_COLORS: Record<ExecutionStatus, string> = {
  created: 'text-[var(--muted)]',
  running: 'text-[var(--accent-2)]',
  success: 'text-[var(--accent)]',
  failed: 'text-[var(--danger)]',
}

interface ChatPanelProps {
  workflowName: string
  hasWorkflow: boolean
  activeWorkflowId: number | null
  executions: Execution[]
  liveTokens: LiveTokens
  lastExecution: Execution | null
  runEnabled: boolean
  runDisabledReason: string | null
  loading: boolean
  nodeMetaByNodeId: Map<number, NodeMeta>
  onRun: (input: RunInputPayload) => void
}

interface ChatTurn {
  id: number
  execution: Execution
  status: ExecutionStatus
  input: string
  output: string
  error: string | null
  isActive: boolean
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDuration(startedAt: string, finishedAt: string | null): string | null {
  if (!finishedAt) {
    return null
  }
  const start = new Date(startedAt).getTime()
  const finish = new Date(finishedAt).getTime()
  if (Number.isNaN(start) || Number.isNaN(finish) || finish < start) {
    return null
  }
  const ms = finish - start
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
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
        execution,
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
  activeWorkflowId,
  executions,
  liveTokens,
  lastExecution,
  runEnabled,
  runDisabledReason,
  loading,
  nodeMetaByNodeId,
  onRun,
}: ChatPanelProps) {
  const [draft, setDraft] = useState('')
  const [versionNumbers, setVersionNumbers] = useState<Record<number, number>>({})
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
    if (activeWorkflowId === null) {
      return
    }
    let cancelled = false
    getWorkflowVersions(activeWorkflowId)
      .then((versions) => {
        if (cancelled) {
          return
        }
        const map: Record<number, number> = {}
        for (const version of versions) {
          map[version.id] = version.version
        }
        setVersionNumbers(map)
      })
      .catch(() => {
        // version labels are best-effort; ignore fetch failures
      })
    return () => {
      cancelled = true
    }
  }, [activeWorkflowId])

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
              <ChatTurnView
                key={turn.id}
                turn={turn}
                versionNumber={
                  turn.execution.version_id !== null
                    ? versionNumbers[turn.execution.version_id]
                    : undefined
                }
                nodeMetaByNodeId={nodeMetaByNodeId}
              />
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

function ChatTurnView({
  turn,
  versionNumber,
  nodeMetaByNodeId,
}: {
  turn: ChatTurn
  versionNumber: number | undefined
  nodeMetaByNodeId: Map<number, NodeMeta>
}) {
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [nodeResults, setNodeResults] = useState<NodeExecutionResult[] | null>(null)
  const [nodeResultsLoading, setNodeResultsLoading] = useState(false)

  function toggleDetails(): void {
    const opening = !detailsOpen
    setDetailsOpen(opening)
    if (opening && nodeResults === null) {
      setNodeResultsLoading(true)
      getExecutionNodeResults(turn.id)
        .then((results) => setNodeResults(results))
        .catch(() => setNodeResults([]))
        .finally(() => setNodeResultsLoading(false))
    }
  }

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
      <div className="flex items-center gap-2 pl-1 text-[10px] uppercase tracking-wide text-[var(--muted)]">
        <span className={STATUS_COLORS[turn.status]}>{turn.status}</span>
        {versionNumber !== undefined ? (
          <span className="pixel-pill text-[10px]">v{versionNumber}</span>
        ) : null}
        <span>{formatTime(turn.execution.started_at)}</span>
        {turn.execution.finished_at ? (
          <span>→ {formatTime(turn.execution.finished_at)}</span>
        ) : null}
        <button
          type="button"
          className="pixel-link underline"
          onClick={toggleDetails}
        >
          {detailsOpen ? 'Hide details' : 'Details'}
        </button>
      </div>
      {detailsOpen ? (
        <div className="pixel-panel ml-1 flex flex-col gap-2 px-3 py-2 text-xs">
          {nodeResultsLoading ? (
            <div className="text-[var(--muted)]">Loading node results…</div>
          ) : !nodeResults || nodeResults.length === 0 ? (
            <div className="text-[var(--muted)]">No node results recorded.</div>
          ) : (
            nodeResults.map((nodeResult) => {
              const meta = nodeMetaByNodeId.get(nodeResult.node_id)
              const duration = formatDuration(
                nodeResult.started_at,
                nodeResult.finished_at,
              )
              return (
                <div key={nodeResult.id} className="border-b border-white/10 pb-2 last:border-0 last:pb-0">
                  <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wide text-[var(--muted)]">
                    <span className="pixel-pill text-[10px] normal-case">
                      {meta?.label ?? `Node #${nodeResult.node_id}`}
                    </span>
                    <span className={STATUS_COLORS[nodeResult.status]}>
                      {nodeResult.status}
                    </span>
                    {duration ? <span>{duration}</span> : null}
                  </div>
                  {nodeResult.output !== null ? (
                    <OutputRenderer
                      value={nodeResult.output}
                      portType={meta?.portType ?? null}
                    />
                  ) : null}
                  {nodeResult.error ? (
                    <div className="text-[var(--danger)]">{nodeResult.error}</div>
                  ) : null}
                </div>
              )
            })
          )}
        </div>
      ) : null}
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
