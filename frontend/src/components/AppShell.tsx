import { type ReactNode, useState } from 'react'

import type { ApiError, Execution } from '../lib/types'
import { ExecutionHistory } from './ExecutionHistory'
import { ProviderManager } from './ProviderManager'
import { TelegramBotManager } from './TelegramBotManager'
import { UserMenu } from './UserMenu'

export type ViewMode = 'build' | 'chat'

interface AppShellProps {
  email: string
  workflowName: string
  executionStatus: string | null
  error: string | null
  viewMode: ViewMode
  executions: Execution[]
  onViewModeChange: (mode: ViewMode) => void
  onLogout: () => void
  onDeleteAccount: () => void
  onError: (err: ApiError) => void
  children: ReactNode
}

export function AppShell({
  email,
  workflowName,
  executionStatus,
  error,
  viewMode,
  executions,
  onViewModeChange,
  onLogout,
  onDeleteAccount,
  onError,
  children,
}: AppShellProps) {
  const [showProviders, setShowProviders] = useState(false)
  const [showTelegramBots, setShowTelegramBots] = useState(false)
  const [showExecutions, setShowExecutions] = useState(false)

  const mainClassName =
    viewMode === 'build'
      ? 'grid h-[calc(100vh-84px)] grid-cols-[280px_1fr_320px] gap-3 px-4 pt-4 pb-4'
      : 'mx-auto flex h-[calc(100vh-84px)] w-full max-w-3xl flex-col px-4 pt-4 pb-4'

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <header className="pixel-topbar grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <div className="flex min-w-0 items-center gap-4">
          <div className="font-pixel text-sm uppercase text-[var(--accent)]">
            Graph AI
          </div>
          <div className="truncate text-xs text-[var(--muted)]">/ {workflowName}</div>
        </div>
        <div className="flex justify-self-center">
          <button
            type="button"
            className={`pixel-tab ${viewMode === 'build' ? 'is-active' : ''}`}
            onClick={() => onViewModeChange('build')}
          >
            Build
          </button>
          <button
            type="button"
            className={`pixel-tab ${viewMode === 'chat' ? 'is-active' : ''}`}
            onClick={() => onViewModeChange('chat')}
          >
            Chat
          </button>
        </div>
        <div className="flex items-center justify-self-end gap-3">
          {executionStatus ? (
            <div className="pixel-pill">Status: {executionStatus}</div>
          ) : null}
          <button
            type="button"
            className="pixel-button ghost small"
            onClick={() => setShowProviders(true)}
          >
            Providers
          </button>
          <button
            type="button"
            className="pixel-button ghost small"
            onClick={() => setShowTelegramBots(true)}
          >
            Telegram Bots
          </button>
          <button
            type="button"
            className="pixel-button ghost small"
            onClick={() => setShowExecutions(true)}
          >
            Executions
          </button>
          <UserMenu
            email={email}
            onLogout={onLogout}
            onDeleteAccount={onDeleteAccount}
          />
        </div>
      </header>
      {showProviders ? (
        <ProviderManager
          onClose={() => setShowProviders(false)}
          onError={onError}
        />
      ) : null}
      {showTelegramBots ? (
        <TelegramBotManager
          onClose={() => setShowTelegramBots(false)}
          onError={onError}
        />
      ) : null}
      {showExecutions ? (
        <ExecutionHistory
          executions={executions}
          onClose={() => setShowExecutions(false)}
        />
      ) : null}
      {error ? <div className="pixel-banner">{error}</div> : null}
      <main className={mainClassName}>{children}</main>
    </div>
  )
}
