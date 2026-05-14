/**
 * TutorialPanel Component
 * 
 * Shows keyboard shortcuts, tips, and guidance when no data is available.
 * Displayed in AICenterPage right panel empty state.
 */

import React from 'react';

interface TutorialPanelProps {
  /** View mode to show relevant shortcuts */
  viewMode?: 'MAIN' | 'AUTO';
}

export function TutorialPanel({ viewMode = 'MAIN' }: TutorialPanelProps) {
  return (
    <div
      style={{
        padding: '16px',
        color: '#94a3b8',
        fontFamily: 'monospace',
        fontSize: '0.8rem',
        lineHeight: '1.6',
      }}
    >
      {/* Header */}
      <div
        style={{
          marginBottom: '20px',
          paddingBottom: '12px',
          borderBottom: '1px dashed rgba(148, 163, 184, 0.2)',
        }}
      >
        <div style={{ color: '#a78bfa', fontWeight: 700, marginBottom: '4px' }}>
          ⌨️ KEYBOARD SHORTCUTS
        </div>
        <div style={{ color: '#4b5563', fontSize: '0.75rem' }}>
          Quick reference guide for power users
        </div>
      </div>

      {/* Navigation Shortcuts */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ color: '#fbbf24', fontSize: '0.75rem', fontWeight: 700, marginBottom: '8px' }}>
          NAVIGATION
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span><kbd style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '3px' }}>Tab</kbd></span>
            <span style={{ color: '#6b7280' }}>Switch between MAIN/AUTO views</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span><kbd style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '3px' }}>Ctrl+1</kbd></span>
            <span style={{ color: '#6b7280' }}>Focus Hacker Assistant</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span><kbd style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '3px' }}>Ctrl+2</kbd></span>
            <span style={{ color: '#6b7280' }}>Focus Automation Agent</span>
          </div>
        </div>
      </div>

      {/* Message Shortcuts */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ color: '#fbbf24', fontSize: '0.75rem', fontWeight: 700, marginBottom: '8px' }}>
          MESSAGE ACTIONS
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span><kbd style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '3px' }}>Enter</kbd></span>
            <span style={{ color: '#6b7280' }}>Send command</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span><kbd style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '3px' }}>Shift+Enter</kbd></span>
            <span style={{ color: '#6b7280' }}>New line (multi-line)</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span><kbd style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '3px' }}>Ctrl+↑/↓</kbd></span>
            <span style={{ color: '#6b7280' }}>Navigate message history</span>
          </div>
        </div>
      </div>

      {/* Getting Started Tips */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ color: '#fbbf24', fontSize: '0.75rem', fontWeight: 700, marginBottom: '8px' }}>
          💡 GETTING STARTED
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {viewMode === 'MAIN' ? (
            <>
              <div>
                <div style={{ color: '#22c55e', marginBottom: '2px' }}>&gt; bind to target [ID]</div>
                <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>Lock an IP or target for focused operations</div>
              </div>
              <div>
                <div style={{ color: '#22c55e', marginBottom: '2px' }}>&gt; start automation</div>
                <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>Launch background Automation Agent</div>
              </div>
              <div>
                <div style={{ color: '#22c55e', marginBottom: '2px' }}>&gt; show progress</div>
                <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>Monitor active steps and skill execution</div>
              </div>
            </>
          ) : (
            <>
              <div>
                <div style={{ color: '#ec4899', marginBottom: '2px' }}>&gt; status</div>
                <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>Check current execution progress</div>
              </div>
              <div>
                <div style={{ color: '#ec4899', marginBottom: '2px' }}>&gt; pause</div>
                <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>Temporarily halt Automation Agent</div>
              </div>
              <div>
                <div style={{ color: '#ec4899', marginBottom: '2px' }}>&gt; log</div>
                <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>View detailed execution logs</div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Pro Tips */}
      <div
        style={{
          padding: '12px',
          background: 'rgba(167, 139, 250, 0.05)',
          border: '1px solid rgba(167, 139, 250, 0.2)',
          borderRadius: '4px',
          marginBottom: '12px',
        }}
      >
        <div style={{ color: '#a78bfa', fontSize: '0.75rem', fontWeight: 700, marginBottom: '6px' }}>
          🚀 PRO TIPS
        </div>
        <ul
          style={{
            margin: 0,
            paddingLeft: '16px',
            color: '#6b7280',
            fontSize: '0.75rem',
            listStyle: 'none',
          }}
        >
          <li style={{ marginBottom: '4px' }}>
            <span style={{ marginRight: '4px' }}>→</span>
            Switch to Execution Monitor to see real-time step logs and performance
          </li>
          <li style={{ marginBottom: '4px' }}>
            <span style={{ marginRight: '4px' }}>→</span>
            Use [EDIT] button on previous commands to modify and re-run them
          </li>
          <li>
            <span style={{ marginRight: '4px' }}>→</span>
            Keep an eye on Response Time in the telemetry sidebar — higher latency = slower agent
          </li>
        </ul>
      </div>
    </div>
  );
}
