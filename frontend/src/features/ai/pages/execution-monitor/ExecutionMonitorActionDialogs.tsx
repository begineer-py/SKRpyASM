import { useRef } from 'react'
import { Archive, MoreHorizontal, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

import type { ExecutionGraphDetail } from '../../services/aiApi'

export type GraphMutation = 'archive' | 'delete'

export type PendingGraphMutation = {
  readonly action: GraphMutation
  readonly graph: ExecutionGraphDetail
}

type ExecutionMonitorActionDialogsProps = {
  readonly graph: ExecutionGraphDetail | null
  readonly actionsOpen: boolean
  readonly pendingMutation: PendingGraphMutation | null
  readonly mutationError: string | null
  readonly mutationLoading: boolean
  readonly onActionsOpenChange: (open: boolean) => void
  readonly onMutationRequest: (action: GraphMutation) => void
  readonly onMutationOpenChange: (open: boolean) => void
  readonly onConfirmMutation: () => void
}

export function ExecutionMonitorActionDialogs({
  graph,
  actionsOpen,
  pendingMutation,
  mutationError,
  mutationLoading,
  onActionsOpenChange,
  onMutationRequest,
  onMutationOpenChange,
  onConfirmMutation,
}: ExecutionMonitorActionDialogsProps) {
  const actionsTriggerRef = useRef<HTMLButtonElement>(null)
  const actionLabel = pendingMutation?.action === 'archive' ? '封存' : '刪除'

  return (
    <>
      <Button
        ref={actionsTriggerRef}
        type="button"
        variant="outline"
        size="sm"
        aria-label="開啟執行圖更多操作"
        onClick={() => onActionsOpenChange(true)}
        disabled={graph === null}
      >
        <MoreHorizontal aria-hidden="true" />
        更多操作
      </Button>

      <Dialog open={actionsOpen} onOpenChange={onActionsOpenChange}>
        <DialogContent
          className="border-border-subtle bg-bg-elevated text-text-primary"
          onCloseAutoFocus={(event) => {
            event.preventDefault()
            actionsTriggerRef.current?.focus()
          }}
        >
          <DialogHeader>
            <DialogTitle>執行圖操作</DialogTitle>
            <DialogDescription className="text-text-secondary">
              Graph #{graph?.id ?? '-'} 的低頻操作需要確認後才會執行。
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <Button
              type="button"
              variant="outline"
              className="justify-start"
              disabled={graph === null}
              onClick={() => onMutationRequest('archive')}
            >
              <Archive aria-hidden="true" />
              封存執行圖
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="justify-start"
              disabled={graph === null}
              onClick={() => onMutationRequest('delete')}
            >
              <Trash2 aria-hidden="true" />
              刪除執行圖
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog
        open={pendingMutation !== null}
        onOpenChange={onMutationOpenChange}
      >
        <DialogContent
          className="border-border-subtle bg-bg-elevated text-text-primary"
          showCloseButton={!mutationLoading}
        >
          <DialogHeader>
            <DialogTitle className={pendingMutation?.action === 'delete' ? 'text-red' : undefined}>
              確認{actionLabel}
            </DialogTitle>
            <DialogDescription className="text-text-secondary">
              {pendingMutation?.action === 'delete'
                ? '刪除後無法復原。'
                : '封存後將從目前的執行清單移除。'}
            </DialogDescription>
          </DialogHeader>
          <p className="rounded-xl border border-border-subtle bg-bg-surface p-4 font-mono text-sm text-text-primary">
            Graph #{pendingMutation?.graph.id ?? '-'}
          </p>
          {mutationError && <p role="alert" className="rounded-xl border border-red/30 bg-red/10 p-3 text-sm text-red">{mutationError}</p>}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={mutationLoading}
              onClick={() => onMutationOpenChange(false)}
            >
              取消
            </Button>
            <Button
              type="button"
              variant={pendingMutation?.action === 'delete' ? 'destructive' : 'default'}
              disabled={mutationLoading}
              onClick={onConfirmMutation}
            >
              {mutationLoading ? `${actionLabel}中` : `確認${actionLabel}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
