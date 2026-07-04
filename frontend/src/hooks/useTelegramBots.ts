import { useCallback, useEffect, useState } from 'react'

import {
  createTelegramBot,
  deleteTelegramBot,
  getTelegramBots,
} from '../lib/api'
import type {
  ApiError,
  TelegramBot,
  TelegramBotCreatePayload,
} from '../lib/types'

interface UseTelegramBotsParams {
  enabled?: boolean
  onError?: (error: ApiError) => void
}

interface UseTelegramBotsResult {
  bots: TelegramBot[]
  loading: boolean
  creating: boolean
  refreshBots: () => Promise<void>
  createBot: (
    payload: TelegramBotCreatePayload,
  ) => Promise<TelegramBot | null>
  removeBot: (botId: number) => Promise<boolean>
}

export function useTelegramBots({
  enabled = true,
  onError,
}: UseTelegramBotsParams): UseTelegramBotsResult {
  const [bots, setBots] = useState<TelegramBot[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)

  const reportError = useCallback(
    (error: ApiError): void => {
      if (onError) {
        onError(error)
      }
    },
    [onError],
  )

  const refreshBots = useCallback(async (): Promise<void> => {
    if (!enabled) {
      setBots([])
      return
    }

    setLoading(true)
    try {
      const items = await getTelegramBots()
      setBots(items)
    } catch (error) {
      reportError(error as ApiError)
      setBots([])
    } finally {
      setLoading(false)
    }
  }, [enabled, reportError])

  useEffect(() => {
    void refreshBots()
  }, [refreshBots])

  const createBot = useCallback(
    async (payload: TelegramBotCreatePayload): Promise<TelegramBot | null> => {
      setCreating(true)
      try {
        const created = await createTelegramBot(payload)
        setBots((previous) => [...previous, created])
        return created
      } catch (error) {
        reportError(error as ApiError)
        return null
      } finally {
        setCreating(false)
      }
    },
    [reportError],
  )

  const removeBot = useCallback(
    async (botId: number): Promise<boolean> => {
      try {
        await deleteTelegramBot(botId)
        setBots((previous) => previous.filter((item) => item.id !== botId))
        return true
      } catch (error) {
        reportError(error as ApiError)
        return false
      }
    },
    [reportError],
  )

  return {
    bots,
    loading,
    creating,
    refreshBots,
    createBot,
    removeBot,
  }
}
