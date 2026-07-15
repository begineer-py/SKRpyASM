import { useState, type FormEvent } from 'react';
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

type TargetCreationInput = {
  readonly name: string;
  readonly description?: string;
};

interface TargetCreateDrawerProps {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
  readonly onCreate: (input: TargetCreationInput) => Promise<void>;
}

export function TargetCreateDrawer({ open, onOpenChange, onCreate }: TargetCreateDrawerProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      setNameError(null);
      setRequestError(null);
    }
    onOpenChange(nextOpen);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = name.trim();
    const trimmedDescription = description.trim();

    if (!trimmedName) {
      setNameError('請輸入 Target 名稱。');
      return;
    }

    setNameError(null);
    setRequestError(null);
    setSubmitting(true);

    try {
      await onCreate({
        name: trimmedName,
        ...(trimmedDescription ? { description: trimmedDescription } : {}),
      });
      setName('');
      setDescription('');
      handleOpenChange(false);
    } catch (error: unknown) {
      setRequestError(error instanceof Error ? error.message : '無法建立 Target，請稍後再試。');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Drawer open={open} onOpenChange={handleOpenChange}>
      <DrawerContent>
        <DrawerHeader>
          <div className="flex flex-col gap-2">
            <DrawerTitle>建立 Target</DrawerTitle>
            <DrawerDescription>輸入目標的基本資訊後，即可從其工作區管理資產與後續作業。</DrawerDescription>
          </div>
          <DrawerDismiss />
        </DrawerHeader>

        <form className="mt-6 flex flex-1 flex-col gap-6" onSubmit={handleSubmit} noValidate>
          <div className="flex flex-col gap-3">
            <label className="text-base font-medium" htmlFor="target-name">
              Target 名稱
            </label>
            <Input
              id="target-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              aria-invalid={Boolean(nameError)}
              aria-describedby={nameError ? 'target-name-error' : undefined}
              className="h-14 rounded-xl text-lg"
              autoFocus
            />
            {nameError ? (
              <p id="target-name-error" className="text-sm text-red" role="alert">
                {nameError}
              </p>
            ) : null}
          </div>

          <div className="flex flex-col gap-3">
            <label className="text-base font-medium" htmlFor="target-description">
              說明
            </label>
            <textarea
              id="target-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="min-h-28 w-full rounded-xl border border-border-normal bg-bg-surface px-3 py-3 text-lg text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-cyan focus-visible:ring-2 focus-visible:ring-cyan/60"
            />
          </div>

          <div className="mt-auto flex flex-col gap-3 border-t border-border-subtle pt-6">
            {requestError ? <p className="text-sm text-red" role="alert">{requestError}</p> : null}
            <Button type="submit" size="lg" className="h-14 rounded-xl" disabled={submitting}>
              {submitting ? '建立中' : '建立 Target'}
            </Button>
          </div>
        </form>
      </DrawerContent>
    </Drawer>
  );
}

export type { TargetCreationInput };
