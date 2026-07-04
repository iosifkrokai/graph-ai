import { type ReactNode, useState } from 'react'

import type { ApiError } from '../lib/types'
import { SettingsModal } from './SettingsModal'
import { UserMenu } from './UserMenu'

interface AppShellProps {
  email: string
  workflowName: string
  executionStatus: string | null
  error: string | null
  onOpenHistory: () => void
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
  onOpenHistory,
  onLogout,
  onDeleteAccount,
  onError,
  children,
}: AppShellProps) {
  const [showSettings, setShowSettings] = useState(false)

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <header className="pixel-topbar flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-4">
          <div className="font-pixel text-sm uppercase text-[var(--accent)]">
            Graph AI
          </div>
          <div className="truncate text-xs text-[var(--muted)]">/ {workflowName}</div>
        </div>
        <div className="flex items-center gap-3">
          {executionStatus ? (
            <div className="pixel-pill">Status: {executionStatus}</div>
          ) : null}
          <button type="button" className="pixel-icon" onClick={onOpenHistory}>
            History
          </button>
          <button
            type="button"
            className="pixel-icon"
            title="Settings"
            onClick={() => setShowSettings(true)}
          >
            ⚙
          </button>
          <UserMenu
            email={email}
            onLogout={onLogout}
            onDeleteAccount={onDeleteAccount}
          />
        </div>
      </header>
      {showSettings ? (
        <SettingsModal
          onClose={() => setShowSettings(false)}
          onError={onError}
        />
      ) : null}
      {error ? <div className="pixel-banner">{error}</div> : null}
      <main className="grid h-[calc(100vh-84px)] grid-cols-[280px_1fr_320px] gap-3 px-4 pt-4 pb-4">
        {children}
      </main>
    </div>
  )
}
