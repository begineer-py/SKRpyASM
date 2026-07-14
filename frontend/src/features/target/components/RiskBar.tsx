interface RiskBarProps {
  score: number;
}

const RiskBar: React.FC<RiskBarProps> = ({ score }) => {
  const color = score >= 70 ? "#ef4444" : score >= 40 ? "#f59e0b" : "#22C55E";
  const colorClass = score >= 70 ? "text-red" : score >= 40 ? "text-amber" : "text-green";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-[#1e293b] rounded-sm overflow-hidden">
        <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
      </div>
      <span className={`font-mono text-xs ${colorClass}`}>{score}</span>
    </div>
  );
};

export default RiskBar;
