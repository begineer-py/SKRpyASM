/**
 * WaveformChart Component
 * 
 * Canvas-based visualization of step execution timing as a bar chart.
 * Shows duration of each step with color-coding based on status.
 * Used in AICenterPage right panel to visualize performance.
 */

import { useEffect, useRef, useMemo } from 'react';

interface StepTiming {
  id: number;
  name: string;
  duration_ms: number;
  status: 'COMPLETED' | 'FAILED' | 'RUNNING' | 'PENDING';
}

interface WaveformChartProps {
  /** Array of step timings to visualize */
  steps: StepTiming[];
  
  /** Chart height in pixels */
  height?: number;
  
  /** Maximum duration to use for scaling (auto-detect if not provided) */
  maxDuration?: number;
  
  /** Whether to animate bars as they enter */
  animate?: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: '#10B981',  // green
  FAILED: '#ef4444',     // red
  RUNNING: '#fbbf24',    // amber
  PENDING: '#6b7280',    // gray
};

export function WaveformChart({
  steps,
  height = 120,
  maxDuration,
  animate = true,
}: WaveformChartProps) {
  // Keep prop for API compatibility even if animation is currently not implemented.
  void animate;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Auto-detect max duration from steps
  const effectiveMaxDuration = useMemo(() => {
    if (maxDuration !== undefined) return maxDuration;
    if (steps.length === 0) return 5000;
    const max = Math.max(...steps.map(s => s.duration_ms));
    return Math.max(max, 100); // At least 100ms to avoid division issues
  }, [steps, maxDuration]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Get actual rendered dimensions
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const chartHeight = rect.height;
    const padding = { top: 16, bottom: 24, left: 12, right: 12 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = chartHeight - padding.top - padding.bottom;

    // Clear canvas
    ctx.fillStyle = 'rgba(15, 23, 42, 0.5)';
    ctx.fillRect(0, 0, width, chartHeight);

    // Draw grid lines (every 1 second)
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.1)';
    ctx.lineWidth = 1;
    ctx.font = '11px monospace';
    ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    
    const secondGrids = Math.ceil(effectiveMaxDuration / 1000);
    for (let i = 1; i < secondGrids; i++) {
      const x = padding.left + (plotWidth * i) / secondGrids;
      ctx.beginPath();
      ctx.moveTo(x, padding.top);
      ctx.lineTo(x, padding.top + plotHeight);
      ctx.stroke();
      
      // Grid label
      ctx.textAlign = 'center';
      ctx.fillText(`${i}s`, x, chartHeight - 6);
    }

    // Y-axis label
    ctx.textAlign = 'right';
    ctx.fillText('duration', padding.left - 4, padding.top + 10);

    // Draw bars for each step
    const barWidth = Math.max(2, Math.floor(plotWidth / Math.max(steps.length, 1)));
    const barGap = 2;

    steps.forEach((step, index) => {
      const barHeight = (step.duration_ms / effectiveMaxDuration) * plotHeight;
      const x = padding.left + index * (barWidth + barGap);
      const y = padding.top + plotHeight - barHeight;

      // Draw bar
      const color = STATUS_COLORS[step.status] || STATUS_COLORS.PENDING;
      ctx.fillStyle = color;
      ctx.fillRect(x, y, barWidth, barHeight);

      // Add glow for running steps
      if (step.status === 'RUNNING') {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.5;
        ctx.strokeRect(x - 1, y - 1, barWidth + 2, barHeight + 2);
        ctx.globalAlpha = 1;
      }

      // Draw status indicator
      ctx.fillStyle = color;
      ctx.font = 'bold 9px monospace';
      ctx.textAlign = 'center';
      const label = step.status[0]; // First letter
      ctx.fillText(label, x + barWidth / 2, y - 4);
    });

    // Draw axis
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + plotHeight);
    ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight);
    ctx.stroke();

  }, [steps, effectiveMaxDuration]);

  if (steps.length === 0) {
    return (
      <div
        style={{
          height: `${height}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(15, 23, 42, 0.3)',
          borderRadius: '4px',
          color: '#4b5563',
          fontSize: '0.8rem',
          fontFamily: 'monospace',
          border: '1px dashed rgba(148, 163, 184, 0.2)',
        }}
      >
        No step data
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: `${height}px`,
        border: '1px solid rgba(148, 163, 184, 0.1)',
        borderRadius: '4px',
        background: 'transparent',
      }}
    />
  );
}
