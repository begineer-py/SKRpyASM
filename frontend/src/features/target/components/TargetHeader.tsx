import type { Target, Seed } from '../types';

interface TargetHeaderProps {
  target: Target;
  seeds: Seed[];
  onBack: () => void;
}

const TargetHeader: React.FC<TargetHeaderProps> = ({ target, seeds, onBack }) => {
  return (
    <header className="mb-6 grid items-start gap-6 rounded-2xl border border-border-subtle bg-bg-card p-6 shadow-soft md:grid-cols-[minmax(0,1fr)_auto]">
      <div className="flex min-w-0 items-start gap-4 max-md:flex-col">
        <button onClick={onBack} className="c2-btn c2-btn--ghost shrink-0">
          返回 Targets
        </button>
        <div>
          <h1 className="text-2xl font-bold text-text-primary md:text-3xl">{target.name}</h1>
          {target.description ? <p className="mt-3 max-w-prose text-base text-text-secondary">{target.description}</p> : null}
        </div>
      </div>
      <dl className="grid grid-cols-2 gap-3 max-md:w-full">
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-4">
          <dt className="text-sm text-text-secondary">Seeds</dt>
          <dd className="mt-2 font-mono text-xl font-semibold text-text-primary">{seeds.length}</dd>
        </div>
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-4">
          <dt className="text-sm text-text-secondary">Active Seeds</dt>
          <dd className="mt-2 font-mono text-xl font-semibold text-cyan">{seeds.filter((seed) => seed.is_active).length}</dd>
        </div>
      </dl>
    </header>
  );
};

export default TargetHeader;
