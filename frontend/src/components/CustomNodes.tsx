import { useEffect } from 'react'
import type { NodeProps } from 'reactflow'
import { Handle, Position, useUpdateNodeInternals } from 'reactflow'

import { NodeIcon } from './NodeIcons'

interface NodeData {
  label: string
  iconKey: string
  graph: {
    has_input: boolean
    has_output: boolean
    output_handles?: string[] | null
  }
}

// Evenly space N named handles along the bottom edge (matches the 50%
// center a single default handle gets).
function handleLeft(index: number, count: number): string {
  return `${((index + 1) / (count + 1)) * 100}%`
}

export function GenericNode({ id, data }: NodeProps<NodeData>) {
  const outputHandles = data.graph.output_handles
  const updateNodeInternals = useUpdateNodeInternals()

  // reactflow caches each handle's DOM position for edge routing and only
  // remeasures on an explicit nudge — without this, edges keep anchoring to
  // stale coordinates whenever a node's handle count/layout changes.
  useEffect(() => {
    updateNodeInternals(id)
  }, [id, outputHandles, updateNodeInternals])

  return (
    <div className="pixel-node flex flex-col gap-1">
      <div className="flex items-center gap-2">
        {data.graph.has_input ? <Handle type="target" position={Position.Top} /> : null}
        <NodeIcon iconKey={data.iconKey} />
        {data.label}
      </div>
      {data.graph.has_output && outputHandles && outputHandles.length > 0 ? (
        <>
          <div className="flex justify-around border-t border-white/10 pt-1 text-[10px] leading-none text-[var(--muted)]">
            {outputHandles.map((handle) => (
              <span key={handle}>{handle}</span>
            ))}
          </div>
          {outputHandles.map((handle, index) => (
            <Handle
              key={handle}
              type="source"
              id={handle}
              position={Position.Bottom}
              style={{ left: handleLeft(index, outputHandles.length) }}
            />
          ))}
        </>
      ) : data.graph.has_output ? (
        <Handle type="source" position={Position.Bottom} />
      ) : null}
    </div>
  )
}
