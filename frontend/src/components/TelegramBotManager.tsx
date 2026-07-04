import { useEffect, useRef, useState } from 'react'

import type { ApiError } from '../lib/types'
import { useTelegramBots } from '../hooks/useTelegramBots'

interface TelegramBotManagerProps {
  onClose: () => void
  onError: (err: ApiError) => void
}

export function TelegramBotManager({ onClose, onError }: TelegramBotManagerProps) {
  const [name, setName] = useState('')
  const [botToken, setBotToken] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  const { bots, creating, createBot, removeBot } = useTelegramBots({ onError })

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as HTMLElement)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  async function handleCreate(): Promise<void> {
    try {
      const created = await createBot({
        name: name.trim(),
        bot_token: botToken.trim(),
      })
      if (created) {
        setName('')
        setBotToken('')
      }
    } catch (error) {
      onError(error as ApiError)
    }
  }

  async function handleDelete(botId: number): Promise<void> {
    await removeBot(botId)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        ref={ref}
        className="pixel-panel modal-scroll w-full max-w-md max-h-[80vh] overflow-y-auto"
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="pixel-section-title">Telegram Bots</div>
          <button
            type="button"
            className="pixel-icon"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        <div className="flex flex-col gap-3">
          {bots.length === 0 ? (
            <div className="text-xs text-[var(--muted)]">
              No bots yet.
            </div>
          ) : null}
          {bots.map((bot) => (
            <div key={bot.id} className="pixel-card">
              <div className="flex-1">
                <div className="text-sm">{bot.name}</div>
                <div className="text-xs text-[var(--muted)]">
                  {bot.enabled ? 'enabled' : 'disabled'}
                </div>
              </div>
              <button
                type="button"
                className="pixel-icon danger"
                onClick={() => void handleDelete(bot.id)}
              >
                Del
              </button>
            </div>
          ))}
        </div>

        <div className="mt-6 border-t border-white/10 pt-4">
          <div className="mb-3 text-xs uppercase tracking-widest text-[var(--muted)]">
            Add bot
          </div>
          <div className="flex flex-col gap-3">
            <label className="pixel-label">
              Name
              <input
                className="pixel-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Bot"
              />
            </label>
            <label className="pixel-label">
              Bot Token
              <input
                className="pixel-input"
                type="password"
                value={botToken}
                autoComplete="off"
                onChange={(e) => setBotToken(e.target.value)}
                placeholder="123456:ABC-DEF..."
              />
            </label>
            <button
              type="button"
              className="pixel-button small"
              disabled={creating || !name.trim() || !botToken.trim()}
              onClick={() => void handleCreate()}
            >
              {creating ? 'Saving...' : 'Add Bot'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
