import { useEffect, useRef, useState } from 'react'

interface ContextMenuProps {
  label: string
  x: number
  y: number
  onDelete: () => void
  onClose: () => void
}

export function ContextMenu({
  label,
  x,
  y,
  onDelete,
  onClose,
}: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as HTMLElement)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  return (
    <div
      ref={ref}
      className="fixed z-50 min-w-[160px] border-2 border-white/10 bg-[var(--panel)] shadow-lg"
      style={{ top: y, left: x }}
    >
      <div className="border-b border-white/10 px-3 py-2 text-xs text-[var(--muted)]">
        {label}
      </div>
      {confirming ? (
        <div className="flex">
          <button
            type="button"
            className="flex-1 px-3 py-2 text-sm text-[var(--danger)] hover:bg-white/5"
            onClick={onDelete}
          >
            Confirm delete
          </button>
          <button
            type="button"
            className="px-3 py-2 text-sm text-[var(--muted)] hover:bg-white/5"
            onClick={() => setConfirming(false)}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--danger)] hover:bg-white/5"
          onClick={() => setConfirming(true)}
        >
          Delete
        </button>
      )}
    </div>
  )
}
