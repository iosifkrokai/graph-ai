import { useCallback, useEffect, useMemo, useState } from 'react'

import { createExecution, getExecutions, streamExecution } from '../lib/api'
import type {
  ApiError,
  Execution,
  ExecutionStatus,
  RunInputPayload,
} from '../lib/types'

// Executions in these states are still being processed by the worker.
const ACTIVE_STATUSES: ExecutionStatus[] = ['created', 'running']

interface UseExecutionsParams {
  token: string | null
  activeWorkflowId: number | null
  setLoading: (value: boolean) => void
  setError: (value: string | null) => void
  handleError: (error: ApiError) => void
}

interface UseExecutionsResult {
  executions: Execution[]
  executionsLoading: boolean
  lastExecution: Execution | null
  runInput: RunInputPayload
  clearExecutions: () => void
  handleRun: (input: RunInputPayload) => Promise<void>
  refreshExecutions: (workflowId: number) => Promise<void>
}

export function useExecutions({
  token,
  activeWorkflowId,
  setLoading,
  setError,
  handleError,
}: UseExecutionsParams): UseExecutionsResult {
  const [runInput, setRunInput] = useState<RunInputPayload>({ value: '' })
  const [executions, setExecutions] = useState<Execution[]>([])
  const [executionsLoading, setExecutionsLoading] = useState<boolean>(false)
  const [lastExecution, setLastExecution] = useState<Execution | null>(null)

  const refreshExecutions = useCallback(
    async (workflowId: number): Promise<void> => {
      setExecutionsLoading(true)
      try {
        const items = await getExecutions(workflowId)
        setExecutions(items)
        const latest = [...items].sort((first, second) => second.id - first.id)[0] ?? null
        setLastExecution(latest)
      } catch (error) {
        handleError(error as ApiError)
      } finally {
        setExecutionsLoading(false)
      }
    },
    [handleError],
  )

  useEffect(() => {
    if (!token || !activeWorkflowId) {
      setExecutions([])
      setLastExecution(null)
      return
    }

    void refreshExecutions(activeWorkflowId)
  }, [activeWorkflowId, refreshExecutions, token])

  const activeExecutionId = useMemo(
    () =>
      lastExecution && ACTIVE_STATUSES.includes(lastExecution.status)
        ? lastExecution.id
        : null,
    [lastExecution],
  )

  useEffect(() => {
    if (!token || !activeWorkflowId || activeExecutionId === null) {
      return
    }

    const controller = new AbortController()
    const workflowId = activeWorkflowId

    void streamExecution(
      activeExecutionId,
      (execution) => {
        setLastExecution(execution)
        setExecutions((previous) =>
          previous.map((item) =>
            item.id === execution.id ? execution : item,
          ),
        )
      },
      controller.signal,
    )
      .catch(() => {
        // Stream unsupported or interrupted; the finally block re-syncs state.
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          void refreshExecutions(workflowId)
        }
      })

    return () => controller.abort()
  }, [activeExecutionId, activeWorkflowId, refreshExecutions, token])

  const handleRun = useCallback(
    async (input: RunInputPayload): Promise<void> => {
      if (!activeWorkflowId) {
        return
      }
      setRunInput(input)
      setLoading(true)
      try {
        const execution = await createExecution(activeWorkflowId, input)
        setLastExecution(execution)
        await refreshExecutions(activeWorkflowId)
        setError(null)
      } catch (error) {
        handleError(error as ApiError)
      } finally {
        setLoading(false)
      }
    },
    [activeWorkflowId, handleError, refreshExecutions, setError, setLoading],
  )

  const clearExecutions = useCallback(() => {
    setExecutions([])
    setLastExecution(null)
  }, [])

  return {
    executions,
    executionsLoading,
    lastExecution,
    runInput,
    clearExecutions,
    handleRun,
    refreshExecutions,
  }
}
