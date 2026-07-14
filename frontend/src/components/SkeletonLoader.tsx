const WIDTHS = [70, 55, 80, 45, 65, 75, 50, 60];

const SkeletonRow = ({ cols }: { cols: number }) => (
  <tr>
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i}>
        <div
          className="skeleton-bar"
          style={{ width: `${WIDTHS[(i * 3 + i) % WIDTHS.length]}%` }}
        />
      </td>
    ))}
  </tr>
);

export const SkeletonTable = ({ rows = 8, cols = 5 }: { rows?: number; cols?: number }) => (
  <div className="c2-card overflow-hidden">
    <table className="c2-table">
      <tbody>
        {Array.from({ length: rows }).map((_, i) => (
          <SkeletonRow key={i} cols={cols} />
        ))}
      </tbody>
    </table>
  </div>
);

export const SkeletonCard = ({ height = 56 }: { height?: number }) => (
  <div className="c2-card skeleton-card" style={{ height }} />
);

export const SkeletonCards = ({ count = 5, height = 56 }: { count?: number; height?: number }) => (
  <div className="flex flex-col gap-2">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} height={height} />
    ))}
  </div>
);
