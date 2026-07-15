import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Crosshair, MoreHorizontal, Plus, RefreshCw } from 'lucide-react';
import { DropdownMenu } from 'radix-ui';
import { TargetCreateDrawer, type TargetCreationInput } from '../components/TargetCreateDrawer';
import { TargetDeleteDialog } from '../components/TargetDeleteDialog';
import { TargetEditDrawer, type TargetUpdateInput } from '../components/TargetEditDrawer';
import { TargetService, gqlFetcher, GET_TARGETS_QUERY } from '../services/targetApi';
import type { Target } from '../types';

export default function TargetListPage() {
  const navigate = useNavigate();
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creationOpen, setCreationOpen] = useState(false);
  const createTargetButtonRef = useRef<HTMLButtonElement>(null);
  const [editingTarget, setEditingTarget] = useState<Target | null>(null);
  const [deletingTarget, setDeletingTarget] = useState<Target | null>(null);

  const fetchTargets = async () => {
    setLoading(true);
    try {
      const data = await gqlFetcher<{ core_target: Target[] }>(GET_TARGETS_QUERY);
      setTargets(data.core_target);
      setError(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : '無法連接至 Hasura API，請確認 Docker 服務狀態。');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchTargets();
  }, []);

  const handleCreate = async (input: TargetCreationInput) => {
    await TargetService.create(input);
    await fetchTargets();
  };

  const handleUpdate = async (targetId: number, input: TargetUpdateInput) => {
    await TargetService.update(targetId, input);
    await fetchTargets();
  };

  const handleDelete = async (targetId: number) => {
    await TargetService.delete(targetId);
    await fetchTargets();
  };

  const handleCreationOpenChange = (open: boolean) => {
    setCreationOpen(open);
    if (!open) {
      requestAnimationFrame(() => createTargetButtonRef.current?.focus());
    }
  };

  return (
    <div className="c2-page p-6 md:p-8">
      <section className="rounded-2xl border border-border-subtle bg-bg-card p-5 shadow-soft">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle pb-5">
          <div className="flex flex-col gap-2">
            <h1 className="text-xl font-semibold text-text-primary">Targets</h1>
            <p className="text-sm text-text-secondary">選擇 Target 以管理資產、計畫與執行記錄。</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button className="c2-btn c2-btn--ghost" type="button" onClick={() => void fetchTargets()} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              {loading ? '更新中' : '重新整理'}
            </button>
            <button ref={createTargetButtonRef} className="c2-btn c2-btn--primary" type="button" onClick={() => setCreationOpen(true)}>
              <Plus size={18} />建立 Target
            </button>
          </div>
        </header>

        {error ? <p className="mt-5 rounded-xl border border-red bg-bg-surface p-4 text-sm text-red" role="alert">{error}</p> : null}

        {targets.length === 0 && !loading ? (
          <div className="c2-empty mt-6">
            <Crosshair size={28} aria-hidden="true" />
            <h2>尚無 Target</h2>
            <p>建立 Target 後即可開始管理資產與作業。</p>
          </div>
        ) : (
          <ul className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {targets.map((target) => (
              <li key={target.id} className="flex min-h-52 flex-col rounded-xl border border-border-subtle bg-bg-surface p-5">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-lg font-semibold text-text-primary">{target.name}</h2>
                  <DropdownMenu.Root>
                    <DropdownMenu.Trigger asChild>
                      <button className="c2-btn c2-btn--icon" type="button" aria-label={`${target.name} 的更多操作`}>
                        <MoreHorizontal size={18} aria-hidden="true" />
                      </button>
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Portal>
                      <DropdownMenu.Content className="z-50 min-w-36 rounded-xl border border-border-subtle bg-bg-elevated p-1 shadow-soft" sideOffset={8}>
                        <DropdownMenu.Item className="cursor-pointer rounded-lg px-3 py-2 text-sm outline-none hover:bg-bg-surface focus:bg-bg-surface" onSelect={() => setEditingTarget(target)}>
                          編輯 Target
                        </DropdownMenu.Item>
                        <DropdownMenu.Item className="cursor-pointer rounded-lg px-3 py-2 text-sm text-red outline-none hover:bg-bg-surface focus:bg-bg-surface" onSelect={() => setDeletingTarget(target)}>
                          刪除 Target
                        </DropdownMenu.Item>
                      </DropdownMenu.Content>
                    </DropdownMenu.Portal>
                  </DropdownMenu.Root>
                </div>
                {target.description ? <p className="mt-3 text-sm leading-6 text-text-secondary">{target.description}</p> : null}
                <div className="mt-auto pt-5">
                  <button className="c2-btn c2-btn--primary w-full" type="button" onClick={() => navigate(`/target/${target.id}`)}>
                    開啟目標 <ArrowUpRight size={16} aria-hidden="true" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <TargetCreateDrawer open={creationOpen} onOpenChange={handleCreationOpenChange} onCreate={handleCreate} />
      <TargetEditDrawer target={editingTarget} onOpenChange={(open) => !open && setEditingTarget(null)} onUpdate={handleUpdate} />
      <TargetDeleteDialog target={deletingTarget} onOpenChange={(open) => !open && setDeletingTarget(null)} onDelete={handleDelete} />
    </div>
  );
}
