import { useEffect, useState, type FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerDismiss,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';
import { Input } from '@/components/ui/input';
import type { Target } from '../types';

type TargetUpdateInput = {
  readonly name: string;
  readonly description: string | null;
};

interface TargetEditDrawerProps {
  readonly target: Target | null;
  readonly onOpenChange: (open: boolean) => void;
  readonly onUpdate: (targetId: number, input: TargetUpdateInput) => Promise<void>;
}

export function TargetEditDrawer({ target, onOpenChange, onUpdate }: TargetEditDrawerProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setName(target?.name ?? '');
    setDescription(target?.description ?? '');
    setNameError(null);
    setRequestError(null);
  }, [target]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = name.trim();
    const trimmedDescription = description.trim();

    if (!target || !trimmedName) {
      setNameError('請輸入 Target 名稱。');
      return;
    }

    setNameError(null);
    setRequestError(null);
    setSubmitting(true);
    try {
      await onUpdate(target.id, {
        name: trimmedName,
        description: trimmedDescription || null,
      });
      onOpenChange(false);
    } catch (error: unknown) {
      setRequestError(error instanceof Error ? error.message : '無法儲存 Target，請稍後再試。');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Drawer open={target !== null} onOpenChange={onOpenChange}>
      <DrawerContent>
        <DrawerHeader>
          <div className="flex flex-col gap-2">
            <DrawerTitle>編輯 Target</DrawerTitle>
            <DrawerDescription>更新 Target 名稱或說明。</DrawerDescription>
          </div>
          <DrawerDismiss />
        </DrawerHeader>

        <form className="mt-6 flex flex-1 flex-col gap-6" onSubmit={handleSubmit} noValidate>
          <div className="flex flex-col gap-3">
            <label className="text-base font-medium" htmlFor="edit-target-name">Target 名稱</label>
            <Input
              id="edit-target-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              aria-invalid={Boolean(nameError)}
              aria-describedby={nameError ? 'edit-target-name-error' : undefined}
              className="h-14 rounded-xl text-lg"
            />
            {nameError ? <p id="edit-target-name-error" className="text-sm text-red" role="alert">{nameError}</p> : null}
          </div>
          <div className="flex flex-col gap-3">
            <label className="text-base font-medium" htmlFor="edit-target-description">說明</label>
            <textarea
              id="edit-target-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="min-h-28 w-full rounded-xl border border-border-normal bg-bg-surface px-3 py-3 text-lg text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-cyan focus-visible:ring-2 focus-visible:ring-cyan/60"
            />
          </div>
          <div className="mt-auto flex flex-col gap-3 border-t border-border-subtle pt-6">
            {requestError ? <p className="text-sm text-red" role="alert">{requestError}</p> : null}
            <Button type="submit" size="lg" className="h-14 rounded-xl" disabled={submitting}>
              {submitting ? '儲存中' : '儲存變更'}
            </Button>
          </div>
        </form>
      </DrawerContent>
    </Drawer>
  );
}

export type { TargetUpdateInput };
