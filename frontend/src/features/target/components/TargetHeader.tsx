import type { Target, Seed } from '../types';

interface TargetHeaderProps {
  target: Target;
  seeds: Seed[];
  onBack: () => void;
}

const TargetHeader: React.FC<TargetHeaderProps> = ({ target, seeds, onBack }) => {
  return (
    <header
      className="grid grid-cols-[minmax(0,1fr)_auto] gap-[22px] items-stretch mb-[22px] p-[26px] border border-border-subtle rounded-3xl shadow-soft flex-wrap"
      style={{
        background: `linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(5, 8, 20, 0.58)),
          radial-gradient(circle at 16% 10%, rgba(6, 182, 212, 0.14), transparent 28rem)`,
      }}
    >
      <div className="flex items-start gap-4 min-w-0 max-md:flex-col">
        <button onClick={onBack} className="c2-btn c2-btn--ghost mt-0.5 shrink-0">
          Back
        </button>
        <div>
          <div className="mb-[7px] text-cyan font-mono text-[0.68rem] font-bold tracking-[0.15em] uppercase">
            Target Mission Control
          </div>
          <h1 className="text-[clamp(1.75rem,3vw,3rem)] font-extrabold text-text-primary flex items-center gap-3 flex-wrap leading-none">
            {target.name}
            <span className="px-[9px] py-1 border border-[rgba(34,197,94,0.22)] rounded-full bg-[rgba(34,197,94,0.08)] text-[#86efac] font-mono text-[0.62rem] font-bold tracking-[0.08em] uppercase">
              Authorized operation
            </span>
          </h1>
          <p className="mt-3 text-text-secondary text-[0.85rem] max-w-[640px]">
            {target.description || "No description provided"}
          </p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2.5 items-stretch shrink-0 p-2.5 border border-border-subtle rounded-[18px] bg-[rgba(5,8,20,0.46)] max-md:w-full [&_.c2-stat]:min-w-[96px] [&_.c2-stat]:p-3 [&_.c2-stat]:border [&_.c2-stat]:border-[rgba(148,163,184,0.10)] [&_.c2-stat]:rounded-[14px] [&_.c2-stat]:bg-[rgba(15,23,42,0.58)] max-[560px]:grid-cols-1">
        <div className="c2-stat">
          <div className="c2-stat__label">Seeds</div>
          <div className="c2-stat__value">{seeds.length}</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__label">Target ID</div>
          <div className="c2-stat__value--cyan c2-stat__value">#{target.id}</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__label">Active Seeds</div>
          <div className="c2-stat__value">{seeds.filter(s => s.is_active).length}</div>
        </div>
      </div>
    </header>
  );
};

export default TargetHeader;
