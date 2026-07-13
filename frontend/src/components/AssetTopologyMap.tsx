import { useMemo, useState } from 'react';
import type { TargetTopology, TopologyNode } from '../services/executionApi';
import './AssetTopologyMap.css';

interface AssetTopologyMapProps {
  topology: TargetTopology | null;
  onSelectNode?: (node: TopologyNode) => void;
  selectedNodeId?: string | null;
}

const TYPE_COLOR: Record<string, string> = {
  target: '#a78bfa',
  seed: '#60a5fa',
  subdomain: '#34d399',
  ip: '#fbbf24',
  url: '#94a3b8',
  vulnerability: '#ef4444',
  port: '#f59e0b',
  endpoint: '#8b5cf6',
};

const TYPE_LAYER: Record<string, number> = {
  target: 0,
  seed: 1,
  subdomain: 1,
  ip: 2,
  port: 3,
  url: 3,
  endpoint: 3,
  vulnerability: 4,
};

function layoutNodes(nodes: TopologyNode[]): Map<string, { x: number; y: number }> {
  const byLayer = new Map<number, TopologyNode[]>();
  for (const n of nodes) {
    const layer = TYPE_LAYER[n.type] ?? 2;
    if (!byLayer.has(layer)) byLayer.set(layer, []);
    byLayer.get(layer)!.push(n);
  }

  const pos = new Map<string, { x: number; y: number }>();
  const layers = [...byLayer.keys()].sort((a, b) => a - b);
  const width = 720;
  const yGap = 90;
  const topPad = 40;

  for (const layer of layers) {
    const items = byLayer.get(layer)!;
    const step = width / (items.length + 1);
    items.forEach((n, i) => {
      pos.set(n.id, {
        x: step * (i + 1),
        y: topPad + layer * yGap,
      });
    });
  }
  return pos;
}

export function AssetTopologyMap({ topology, onSelectNode, selectedNodeId }: AssetTopologyMapProps) {
  const [hoverId, setHoverId] = useState<string | null>(null);

  const { positions, width, height } = useMemo(() => {
    if (!topology) return { positions: new Map(), width: 720, height: 280 };
    const positions = layoutNodes(topology.nodes);
    let maxY = 200;
    positions.forEach((p) => {
      maxY = Math.max(maxY, p.y + 40);
    });
    return { positions, width: 720, height: maxY + 40 };
  }, [topology]);

  if (!topology) {
    return <div className="atm-empty">Select a target-bound thread to view topology</div>;
  }

  if (topology.nodes.length === 0) {
    return <div className="atm-empty">No assets for {topology.target_name}</div>;
  }

  return (
    <div className="asset-topology-map" data-testid="asset-topology-map">
      <div className="atm-header">
        <span className="atm-title">Topology · {topology.target_name}</span>
        <span className="atm-stats">
          {topology.nodes.length} nodes · {topology.edges.length} edges
          {topology.active_attacks?.length
            ? ` · 🤖 ${topology.active_attacks.length} active`
            : ''}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={Math.min(height, 420)}>
        {topology.edges.map((e) => {
          const s = positions.get(e.source);
          const t = positions.get(e.target);
          if (!s || !t) return null;
          const active =
            hoverId === e.source ||
            hoverId === e.target ||
            selectedNodeId === e.source ||
            selectedNodeId === e.target;
          return (
            <line
              key={e.id}
              x1={s.x}
              y1={s.y}
              x2={t.x}
              y2={t.y}
              className={`atm-edge ${active ? 'atm-edge--active' : ''}`}
            />
          );
        })}

        {topology.nodes.map((n) => {
          const p = positions.get(n.id);
          if (!p) return null;
          const color = TYPE_COLOR[n.type] || '#94a3b8';
          const selected = selectedNodeId === n.id;
          const attacking = Boolean(n.is_active_attack);
          return (
            <g
              key={n.id}
              transform={`translate(${p.x}, ${p.y})`}
              className={`atm-node ${selected ? 'atm-node--selected' : ''} ${attacking ? 'atm-node--attack' : ''}`}
              onClick={() => onSelectNode?.(n)}
              onMouseEnter={() => setHoverId(n.id)}
              onMouseLeave={() => setHoverId(null)}
              style={{ cursor: 'pointer' }}
            >
              {attacking && <circle r={18} className="atm-attack-ring" />}
              <circle r={12} fill={color} className="atm-dot" />
              <text y={28} textAnchor="middle" className="atm-label">
                {n.label.length > 18 ? `${n.label.slice(0, 16)}…` : n.label}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="atm-legend">
        {Object.entries(TYPE_COLOR).map(([type, color]) => (
          <span key={type} className="atm-legend-item">
            <i style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}

export default AssetTopologyMap;
