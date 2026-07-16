import { useCallback, useEffect, useMemo, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import ExecutionTimelineViewer from '../../../components/ExecutionTimelineViewer'
import { executionApi, type ExecutionGraph, type ExecutionGraphDetail } from '../services/aiApi'
import { Button } from '@/components/ui/button'
import { ExecutionMonitorActionDialogs, type GraphMutation, type PendingGraphMutation } from './execution-monitor/ExecutionMonitorActionDialogs'
import { ExecutionMonitorControlsDialog, type MonitorFilters } from './execution-monitor/ExecutionMonitorControlsDialog'
import { ExecutionMonitorGraphDetail } from './execution-monitor/ExecutionMonitorGraphDetail'
import { type GraphQuery, parseGraphQuery } from './execution-monitor/executionMonitorRoute'

type GraphDetailState =
  | { readonly kind: 'idle' }
  | { readonly kind: 'loading'; readonly graphId: number }
  | { readonly kind: 'ready'; readonly graph: ExecutionGraphDetail }
  | { readonly kind: 'unavailable'; readonly graphId: number; readonly message: string }

const EMPTY_FILTERS: MonitorFilters = {
  status: '',
  assistant: '',
  thread: '',
  target: '',
  search: '',
}

function positiveInteger(value: string): number | null {
  const parsed = Number(value.trim())
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null
}

export default function ExecutionMonitorPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [graphs, setGraphs] = useState<readonly ExecutionGraph[]>([])
  const [detailState, setDetailState] = useState<GraphDetailState>({ kind: 'idle' })
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)
  const [filters, setFilters] = useState<MonitorFilters>(EMPTY_FILTERS)
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState<string | null>(null)
  const [controlsOpen, setControlsOpen] = useState(false)
  const [actionsOpen, setActionsOpen] = useState(false)
  const [pendingMutation, setPendingMutation] = useState<PendingGraphMutation | null>(null)
  const [mutationLoading, setMutationLoading] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const graphParam = searchParams.get('graph')
  const graphQuery = useMemo(() => parseGraphQuery(graphParam), [graphParam])
  const selectedGraphId = graphQuery.kind === 'valid' ? graphQuery.graphId : null
  const selectedGraph = detailState.kind === 'ready' && selectedGraphId === detailState.graph.id
    ? detailState.graph
    : null

  const selectGraph = useCallback((graphId: number, replace = false) => {
    setFeedback(null)
    setSearchParams((current) => {
      const next = new URLSearchParams(current)
      next.set('graph', String(graphId))
      next.delete('node')
      return next
    }, { replace })
  }, [setSearchParams])

  const loadGraphs = useCallback(async () => {
    setListLoading(true)
    setListError(null)
    try {
      const params: { status?: string; thread_id?: number; target_id?: number; limit: number } = { limit: 100 }
      const threadId = positiveInteger(filters.thread)
      const targetId = positiveInteger(filters.target)
      if (filters.status) params.status = filters.status
      if (threadId !== null) params.thread_id = threadId
      if (targetId !== null) params.target_id = targetId
      setGraphs(await executionApi.listGraphs(params))
    } catch (error: unknown) {
      setListError(error instanceof Error ? error.message : '無法載入執行清單。')
    } finally {
      setListLoading(false)
    }
  }, [filters.status, filters.target, filters.thread])

  useEffect(() => {
    void loadGraphs()
  }, [loadGraphs])

  useEffect(() => {
    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') void loadGraphs()
    }
    window.addEventListener('focus', refreshWhenVisible)
    document.addEventListener('visibilitychange', refreshWhenVisible)
    return () => {
      window.removeEventListener('focus', refreshWhenVisible)
      document.removeEventListener('visibilitychange', refreshWhenVisible)
    }
  }, [loadGraphs])

  useEffect(() => {
    if (graphQuery.kind === 'missing' && graphs.length > 0) {
      selectGraph(graphs[0].id, true)
    }
  }, [graphQuery.kind, graphs, selectGraph])

  useEffect(() => {
    if (graphQuery.kind !== 'valid') {
      setDetailState({ kind: 'idle' })
      setSelectedNodeId(null)
      return
    }

    let cancelled = false
    setDetailState({ kind: 'loading', graphId: graphQuery.graphId })
    setSelectedNodeId(null)
    void executionApi.getGraph(graphQuery.graphId)
      .then((graph) => {
        if (cancelled) return
        setDetailState({ kind: 'ready', graph })
        setSelectedNodeId(graph.nodes.find((node) => node.status === 'RUNNING' || node.status === 'WAITING')?.id ?? graph.nodes[0]?.id ?? null)
      })
      .catch((error: unknown) => {
        if (cancelled) return
        const message = error instanceof Error ? error.message : '請求的執行圖無法使用。'
        setDetailState({ kind: 'unavailable', graphId: graphQuery.graphId, message })
      })
    return () => {
      cancelled = true
    }
  }, [graphQuery])

  const requestMutation = useCallback((action: GraphMutation) => {
    if (!selectedGraph) return
    setActionsOpen(false)
    setMutationError(null)
    setPendingMutation({ action, graph: selectedGraph })
  }, [selectedGraph])

  const closeMutation = useCallback((open: boolean) => {
    if (!open && !mutationLoading) {
      setPendingMutation(null)
      setMutationError(null)
    }
  }, [mutationLoading])

  const confirmMutation = useCallback(async () => {
    if (!pendingMutation) return
    setMutationLoading(true)
    setMutationError(null)
    try {
      if (pendingMutation.action === 'archive') {
        await executionApi.archiveGraph(pendingMutation.graph.id)
      } else {
        await executionApi.deleteGraph(pendingMutation.graph.id)
      }
      setGraphs((current) => current.filter((graph) => graph.id !== pendingMutation.graph.id))
      setFeedback(`Graph #${pendingMutation.graph.id} 已${pendingMutation.action === 'archive' ? '封存' : '刪除'}。`)
      setPendingMutation(null)
      setSearchParams((current) => {
        const next = new URLSearchParams(current)
        next.delete('graph')
        next.delete('node')
        return next
      })
    } catch (error: unknown) {
      setMutationError(error instanceof Error ? error.message : `無法${pendingMutation.action === 'archive' ? '封存' : '刪除'}執行圖。`)
    } finally {
      setMutationLoading(false)
    }
  }, [pendingMutation, setSearchParams])

  return (
    <div className="c2-workspace c2-workspace--monitor min-h-screen bg-bg-base p-6 font-body text-text-primary">
      <header className="flex flex-wrap items-center justify-end gap-3 pb-2">
        {feedback && <p role="status" className="text-sm text-green">{feedback}</p>}
        <ExecutionMonitorActionDialogs
          graph={selectedGraph}
          actionsOpen={actionsOpen}
          pendingMutation={pendingMutation}
          mutationError={mutationError}
          mutationLoading={mutationLoading}
          onActionsOpenChange={setActionsOpen}
          onMutationRequest={requestMutation}
          onMutationOpenChange={closeMutation}
          onConfirmMutation={() => void confirmMutation()}
        />
        <ExecutionMonitorControlsDialog
          open={controlsOpen}
          graphs={graphs}
          selectedGraphId={selectedGraphId}
          filters={filters}
          loading={listLoading}
          error={listError}
          onOpenChange={setControlsOpen}
          onFiltersChange={setFilters}
          onRefresh={() => void loadGraphs()}
          onSelectGraph={(graphId) => {
            selectGraph(graphId)
            setControlsOpen(false)
          }}
        />
      </header>

      <section className="mt-2 grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]" aria-label="執行監控工作區">
        {selectedGraph ? (
          <ExecutionMonitorGraphDetail graph={selectedGraph} selectedNodeId={selectedNodeId} onNodeSelect={setSelectedNodeId} />
        ) : (
          <GraphRouteState
            graphQuery={graphQuery}
            detailState={detailState}
            listError={listError}
            availableGraphId={graphs[0]?.id ?? null}
            onSelectGraph={selectGraph}
            onRefresh={() => void loadGraphs()}
          />
        )}
        <aside className="min-h-[560px] xl:min-h-[calc(100vh-292px)]">
          {selectedGraph ? <ExecutionTimelineViewer graphId={selectedGraph.id} autoScroll /> : <TimelinePlaceholder />}
        </aside>
      </section>
    </div>
  )
}

function GraphRouteState({ graphQuery, detailState, listError, availableGraphId, onSelectGraph, onRefresh }: {
  readonly graphQuery: GraphQuery
  readonly detailState: GraphDetailState
  readonly listError: string | null
  readonly availableGraphId: number | null
  readonly onSelectGraph: (graphId: number) => void
  readonly onRefresh: () => void
}) {
  const state = graphQuery.kind === 'invalid'
    ? { title: '無效的執行圖連結', description: `graph=${graphQuery.value} 不是有效的正整數。請從執行清單選擇圖形。`, tone: 'error' }
    : detailState.kind === 'unavailable'
      ? { title: `Graph #${detailState.graphId} 無法使用`, description: `${detailState.message} 此執行圖可能已刪除、已封存或目前無法存取。請選擇其他可用圖形。`, tone: 'error' }
      : graphQuery.kind === 'valid' && detailState.kind === 'ready'
        ? { title: `正在載入 Graph #${graphQuery.graphId}`, description: '正在確認這個執行圖是否可用。', tone: 'loading' }
      : detailState.kind === 'loading'
        ? { title: `正在載入 Graph #${detailState.graphId}`, description: '正在確認這個執行圖是否可用。', tone: 'loading' }
        : listError
          ? { title: '無法載入執行清單', description: listError, tone: 'error' }
          : { title: '尚未選擇執行圖', description: '從執行控制開啟清單，選擇要檢視的執行圖。', tone: 'idle' }

  return (
    <main className="flex min-h-[560px] items-center justify-center rounded-2xl bg-bg-card p-6 text-center shadow-soft xl:min-h-[calc(100vh-292px)]">
      <div className="max-w-md">
        <h2 className="text-xl font-semibold text-text-primary" role={state.tone === 'error' ? 'alert' : undefined}>{state.title}</h2>
        <p className="mt-3 text-sm leading-6 text-text-secondary">{state.description}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {availableGraphId !== null && state.tone !== 'loading' && <Button type="button" onClick={() => onSelectGraph(availableGraphId)}>開啟可用執行圖</Button>}
          {state.tone === 'error' && <Button type="button" variant="outline" onClick={onRefresh}><RefreshCw aria-hidden="true" />重新整理清單</Button>}
        </div>
      </div>
    </main>
  )
}

function TimelinePlaceholder() {
  return (
    <section className="flex min-h-[560px] items-center justify-center rounded-2xl border border-border-subtle bg-bg-card p-6 text-center shadow-soft xl:min-h-[calc(100vh-292px)]" aria-label="執行時間軸狀態">
      <p className="max-w-xs text-sm leading-6 text-text-secondary">時間軸會在有效執行圖載入後顯示，避免將舊圖形資料誤認為目前連結的內容。</p>
    </section>
  )
}
