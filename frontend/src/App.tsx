import { useCallback, useEffect, useMemo, useState } from 'react'

import { ActivityLog } from './components/ActivityLog'
import { AppShell } from './components/AppShell'
import { AuthScreen } from './components/AuthScreen'
import { ChatPanel } from './components/ChatPanel'
import { CreateNodeDialog } from './components/CreateNodeDialog'
import { GraphCanvas } from './components/GraphCanvas'
import { HistoryOverlay } from './components/HistoryOverlay'
import type { HistoryTabId } from './components/HistoryOverlay'
import { InspectorPanel } from './components/InspectorPanel'
import { NewFromTemplateDialog } from './components/NewFromTemplateDialog'
import { WorkflowSidebar } from './components/WorkflowSidebar'
import { useActivityLog } from './hooks/useActivityLog'
import { useAuthSession } from './hooks/useAuthSession'
import { useExecutions } from './hooks/useExecutions'
import { useGraphState } from './hooks/useGraphState'
import { useNodeCatalog } from './hooks/useNodeCatalog'
import { useWorkflowState } from './hooks/useWorkflowState'
import { useWorkflowTransfer } from './hooks/useWorkflowTransfer'
import type { ApiError, NodeMeta, NodeType } from './lib/types'

interface NodeCreateDraft {
  type: NodeType
  position: {
    x: number
    y: number
  }
}

export function App() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [historyTab, setHistoryTab] = useState<HistoryTabId | null>(null)
  const [nodeCreateDraft, setNodeCreateDraft] = useState<NodeCreateDraft | null>(null)
  const [showNewFromTemplate, setShowNewFromTemplate] = useState<boolean>(false)
  // Which Loop node's body the canvas is currently showing, or null for the
  // top-level graph — set by double-clicking into a Loop node.
  const [activeParentNodeId, setActiveParentNodeId] = useState<number | null>(null)

  const {
    token,
    email,
    handleError,
    handleLogin,
    handleRegister,
    handleLogout: logoutAuth,
    handleDeleteAccount: deleteAccountAuth,
  } = useAuthSession({
    setLoading,
    setError,
  })

  const {
    workflows,
    activeWorkflowId,
    setActiveWorkflowId,
    clearWorkflowState,
    handleCreateWorkflow,
    handleRenameWorkflow,
    handleDeleteWorkflow,
  } = useWorkflowState({
    token,
    setLoading,
    setError,
    handleError,
  })

  const {
    handleDuplicateWorkflow,
    handleExportWorkflow,
    handleImportWorkflow,
    handleInstantiateTemplate,
  } = useWorkflowTransfer({
    setLoading,
    setError,
    handleError,
    onWorkflowCreated: (created) => setActiveWorkflowId(created.id),
  })

  const {
    nodeCatalog,
    nodeCatalogByType,
  } = useNodeCatalog({
    handleError,
  })

  const {
    nodes,
    edges,
    selectedNodeIds,
    selectedNode,
    canUndo,
    canRedo,
    clearGraphState,
    handleSelectionChange,
    createNodeWithData,
    getInitialNodeData,
    handleDeleteNode,
    handleDeleteSelected,
    handleUpdateNodeData,
    handleNodesChange,
    handleMoveNode,
    handleConnect,
    handleDeleteEdge,
    copySelection,
    pasteClipboard,
    handleAutoLayout,
    undo,
    redo,
  } = useGraphState({
    token,
    activeWorkflowId,
    activeParentNodeId,
    nodeCatalogByType,
    setLoading,
    setError,
    handleError,
  })

  // Leaving a Loop body when the workflow changes (or its Loop node
  // disappears from the freshly-loaded graph) falls back to the top level
  // rather than showing an empty canvas for a scope that no longer exists.
  useEffect(() => {
    setActiveParentNodeId(null)
  }, [activeWorkflowId])
  useEffect(() => {
    if (activeParentNodeId === null) {
      return
    }
    if (!nodes.some((node) => Number(node.id) === activeParentNodeId)) {
      setActiveParentNodeId(null)
    }
  }, [activeParentNodeId, nodes])

  const {
    executions,
    lastExecution,
    liveTokens,
    clearExecutions,
    handleRun,
  } = useExecutions({
    token,
    activeWorkflowId,
    setLoading,
    setError,
    handleError,
  })

  const {
    executions: activityLogExecutions,
    loading: activityLogLoading,
  } = useActivityLog({
    token,
    activeWorkflowId,
    handleError,
  })

  const activeWorkflow = workflows.find((workflow) => workflow.id === activeWorkflowId) ?? null
  const activeParentNode = useMemo(
    () => nodes.find((node) => Number(node.id) === activeParentNodeId) ?? null,
    [nodes, activeParentNodeId],
  )
  // How many nodes live in each Loop's body — shown on the Loop node itself
  // so it's obvious there's something to drill into (see CustomNodes.tsx).
  const loopChildCounts = useMemo(() => {
    const counts = new Map<number, number>()
    for (const node of nodes) {
      const parentNodeId = node.data?.parentNodeId as number | null | undefined
      if (parentNodeId !== null && parentNodeId !== undefined) {
        counts.set(parentNodeId, (counts.get(parentNodeId) ?? 0) + 1)
      }
    }
    return counts
  }, [nodes])
  // The canvas shows exactly one scope at a time (top level, or one Loop's
  // body) — filtered client-side since the full node/edge list for every
  // scope is already loaded.
  const canvasNodes = useMemo(
    () =>
      nodes
        .filter(
          (node) =>
            (node.data?.parentNodeId as number | null | undefined) === activeParentNodeId,
        )
        .map((node) =>
          node.type === 'loop'
            ? {
                ...node,
                data: { ...node.data, childCount: loopChildCounts.get(Number(node.id)) ?? 0 },
              }
            : node,
        ),
    [nodes, activeParentNodeId, loopChildCounts],
  )
  const canvasNodeIds = useMemo(
    () => new Set(canvasNodes.map((node) => node.id)),
    [canvasNodes],
  )
  const canvasEdges = useMemo(
    () => edges.filter((edge) => canvasNodeIds.has(edge.source) && canvasNodeIds.has(edge.target)),
    [edges, canvasNodeIds],
  )
  // Loop/loop_input/loop_output only make sense in one of the two scopes:
  // a Loop node can't nest inside another Loop's body, and loop_input/
  // loop_output only exist as a Loop body's entry/exit points.
  const creatableNodeCatalog = useMemo(
    () =>
      nodeCatalog.filter((item) =>
        activeParentNodeId === null
          ? item.type !== 'loop_input' && item.type !== 'loop_output'
          : item.type !== 'loop' && item.type !== 'input' && item.type !== 'output',
      ),
    [nodeCatalog, activeParentNodeId],
  )
  const inputNodes = useMemo(
    () => nodes.filter((node) => node.type === 'input'),
    [nodes],
  )
  const outputNodes = useMemo(
    () => nodes.filter((node) => node.type === 'output'),
    [nodes],
  )
  const nodeMetaByNodeId = useMemo(() => {
    const map = new Map<number, NodeMeta>()
    for (const node of nodes) {
      const catalogItem = nodeCatalogByType[node.type ?? '']
      map.set(Number(node.id), {
        type: node.type ?? 'unknown',
        label: catalogItem?.label ?? node.type ?? 'Unknown',
        portType: catalogItem?.graph.output_port ?? null,
        parentNodeId: (node.data?.parentNodeId as number | null | undefined) ?? null,
      })
    }
    return map
  }, [nodes, nodeCatalogByType])
  const inputFormat = String(inputNodes[0]?.data?.format ?? 'txt')
  const runDisabledReason = useMemo((): string | null => {
    if (!activeWorkflowId) {
      return 'Select a workflow to run.'
    }
    if (inputNodes.length !== 1) {
      return 'Workflow must contain exactly one input node.'
    }
    if (outputNodes.length !== 1) {
      return 'Workflow must contain exactly one output node.'
    }
    if (inputFormat !== 'txt') {
      return `Unsupported input format: ${inputFormat}.`
    }
    return null
  }, [activeWorkflowId, inputFormat, inputNodes.length, outputNodes.length])
  const runEnabled = runDisabledReason === null

  const handleLogout = useCallback(() => {
    clearExecutions()
    clearGraphState()
    clearWorkflowState()
    setNodeCreateDraft(null)
    logoutAuth()
  }, [clearExecutions, clearGraphState, clearWorkflowState, logoutAuth])

  const handleDeleteAccount = useCallback(async () => {
    await deleteAccountAuth()
    clearExecutions()
    clearGraphState()
    clearWorkflowState()
    setNodeCreateDraft(null)
  }, [clearExecutions, clearGraphState, clearWorkflowState, deleteAccountAuth])

  // App-wide graph-editor shortcuts. Skipped while focused in an editable
  // field (Inspector inputs, workflow-name field, etc.) so typing a literal
  // "z" or hitting Backspace to delete a character doesn't also mutate the
  // graph.
  useEffect(() => {
    function isEditableTarget(target: EventTarget | null): boolean {
      if (!(target instanceof HTMLElement)) {
        return false
      }
      return (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      )
    }

    function handleKeyDown(event: KeyboardEvent): void {
      if (isEditableTarget(event.target)) {
        return
      }
      const meta = event.ctrlKey || event.metaKey

      if (!meta && (event.key === 'Delete' || event.key === 'Backspace')) {
        event.preventDefault()
        void handleDeleteSelected()
        return
      }
      if (meta && event.key.toLowerCase() === 'z') {
        event.preventDefault()
        void (event.shiftKey ? redo() : undo())
        return
      }
      if (meta && event.key.toLowerCase() === 'y') {
        event.preventDefault()
        void redo()
        return
      }
      if (meta && event.key.toLowerCase() === 'c') {
        copySelection()
        return
      }
      if (meta && event.key.toLowerCase() === 'v') {
        void pasteClipboard()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [copySelection, handleDeleteSelected, pasteClipboard, redo, undo])

  const requestCreateNode = useCallback(
    (type: NodeType, position: { x: number; y: number }) => {
      if (!activeWorkflowId) {
        return
      }
      setNodeCreateDraft({ type, position })
    },
    [activeWorkflowId],
  )

  const handleAddNode = useCallback(
    (type: NodeType) => {
      requestCreateNode(type, {
        x: 120 + canvasNodes.length * 36,
        y: 120 + canvasNodes.length * 36,
      })
    },
    [canvasNodes.length, requestCreateNode],
  )

  const handleDropNode = useCallback(
    (type: string, position: { x: number; y: number }) => {
      requestCreateNode(type, position)
    },
    [requestCreateNode],
  )

  const createNodeSpec = nodeCreateDraft
    ? nodeCatalogByType[nodeCreateDraft.type] ?? null
    : null

  const createNodeInitialData = useMemo(() => {
    if (!nodeCreateDraft) {
      return {}
    }
    return getInitialNodeData(nodeCreateDraft.type)
  }, [getInitialNodeData, nodeCreateDraft])

  const confirmCreateNode = useCallback(
    async (data: Record<string, unknown>) => {
      if (!nodeCreateDraft) {
        return
      }

      setLoading(true)
      try {
        await createNodeWithData(nodeCreateDraft.type, nodeCreateDraft.position, data)
        setNodeCreateDraft(null)
      } catch (issue) {
        handleError(issue as ApiError)
      } finally {
        setLoading(false)
      }
    },
    [createNodeWithData, handleError, nodeCreateDraft],
  )

  if (!token) {
    return (
      <AuthScreen
        loading={loading}
        error={error}
        onLogin={handleLogin}
        onRegister={handleRegister}
      />
    )
  }

  return (
    <>
      <AppShell
        email={email}
        workflowName={activeWorkflow?.name ?? 'Untitled workflow'}
        parentLoopLabel={
          activeParentNode ? String(activeParentNode.data?.label ?? 'Loop') : null
        }
        onExitLoop={() => setActiveParentNodeId(null)}
        error={error}
        canUndo={canUndo}
        canRedo={canRedo}
        onUndo={() => void undo()}
        onRedo={() => void redo()}
        onAutoLayout={() => void handleAutoLayout()}
        onOpenTestRuns={() => setHistoryTab('test-runs')}
        onOpenActivityLog={() => setHistoryTab('activity-log')}
        onDismissError={() => setError(null)}
        onLogout={handleLogout}
        onDeleteAccount={handleDeleteAccount}
        onError={handleError}
      >
        <WorkflowSidebar
          workflows={workflows}
          activeWorkflowId={activeWorkflowId}
          activeWorkflowStatus={lastExecution?.status ?? null}
          nodeCatalog={creatableNodeCatalog}
          onSelectWorkflow={setActiveWorkflowId}
          onCreateWorkflow={handleCreateWorkflow}
          onRenameWorkflow={handleRenameWorkflow}
          onDeleteWorkflow={handleDeleteWorkflow}
          onDuplicateWorkflow={(id) => void handleDuplicateWorkflow(id)}
          onExportWorkflow={(id) => void handleExportWorkflow(id)}
          onImportWorkflow={(file) => void handleImportWorkflow(file)}
          onOpenNewFromTemplate={() => setShowNewFromTemplate(true)}
          onAddNode={handleAddNode}
        />
        <GraphCanvas
          activeWorkflowId={activeWorkflowId}
          activeParentNodeId={activeParentNodeId}
          nodes={canvasNodes}
          edges={canvasEdges}
          nodeCatalog={nodeCatalog}
          runDisabledReason={activeWorkflowId ? runDisabledReason : null}
          selectedCount={selectedNodeIds.length}
          onSelectionChange={handleSelectionChange}
          onNodesChange={handleNodesChange}
          onMoveNode={handleMoveNode}
          onConnect={handleConnect}
          onDeleteEdge={handleDeleteEdge}
          onDropNode={handleDropNode}
          onDeleteNode={handleDeleteNode}
          onDrillIntoLoop={(nodeId) => setActiveParentNodeId(Number(nodeId))}
        />
        <InspectorPanel
          node={selectedNode}
          nodeCatalog={nodeCatalog}
          onSaveNode={handleUpdateNodeData}
        />
      </AppShell>

      {historyTab ? (
        <HistoryOverlay
          title={historyTab === 'test-runs' ? 'Test Runs' : 'Activity Log'}
          onClose={() => setHistoryTab(null)}
        >
          {historyTab === 'test-runs' ? (
            <ChatPanel
              workflowName={activeWorkflow?.name ?? 'Untitled workflow'}
              hasWorkflow={activeWorkflowId !== null}
              activeWorkflowId={activeWorkflowId}
              executions={executions}
              liveTokens={liveTokens}
              lastExecution={lastExecution}
              runEnabled={runEnabled}
              runDisabledReason={runDisabledReason}
              loading={loading}
              nodeMetaByNodeId={nodeMetaByNodeId}
              onRun={handleRun}
            />
          ) : (
            <ActivityLog
              workflowName={activeWorkflow?.name ?? 'Untitled workflow'}
              hasWorkflow={activeWorkflowId !== null}
              executions={activityLogExecutions}
              loading={activityLogLoading}
              nodeMetaByNodeId={nodeMetaByNodeId}
            />
          )}
        </HistoryOverlay>
      ) : null}

      <CreateNodeDialog
        key={
          nodeCreateDraft
            ? `${nodeCreateDraft.type}:${nodeCreateDraft.position.x}:${nodeCreateDraft.position.y}`
            : 'no-draft'
        }
        nodeSpec={createNodeSpec}
        initialData={createNodeInitialData}
        onCancel={() => setNodeCreateDraft(null)}
        onConfirm={confirmCreateNode}
      />

      {showNewFromTemplate ? (
        <NewFromTemplateDialog
          onCancel={() => setShowNewFromTemplate(false)}
          onConfirm={async (templateKey) => {
            await handleInstantiateTemplate(templateKey)
            setShowNewFromTemplate(false)
          }}
        />
      ) : null}
    </>
  )
}
