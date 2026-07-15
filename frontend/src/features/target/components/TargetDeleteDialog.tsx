import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { Target } from '../types';

interface TargetDeleteDialogProps {
  readonly target: Target | null;
  readonly onOpenChange: (open: boolean) => void;
  readonly onDelete: (targetId: number) => Promise<void>;
}

export function TargetDeleteDialog({ target, onOpenChange, onDelete }: TargetDeleteDialogProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!target) return;
    setSubmitting(true);
    setError(null);
    try {
      await onDelete(target.id);
      onOpenChange(false);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : '無法刪除 Target，請稍後再試。');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={target !== null} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>刪除 Target</DialogTitle>
          <DialogDescription>將永久移除「{target?.name}」及其關聯資料。此操作無法復原。</DialogDescription>
        </DialogHeader>
        {error ? <p className="text-sm text-red" role="alert">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>取消</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={submitting}>
            {submitting ? '刪除中' : '刪除 Target'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
