/**
 * TutorialPanel Component
 * 
 * Shows keyboard shortcuts, tips, and guidance when no data is available.
 * Displayed in AICenterPage right panel empty state.
 */

// React import not needed with react-jsx runtime

interface TutorialPanelProps {
  /** View mode to show relevant shortcuts */
  viewMode?: 'MAIN' | 'AUTO';
}

export function TutorialPanel({ viewMode = 'MAIN' }: TutorialPanelProps) {
  return (
    <div
      className="p-4 text-text-secondary font-mono text-[0.8rem] leading-[1.6]"
    >
      {/* Header */}
      <div
        className="mb-5 pb-3 border-b border-dashed border-border-subtle"
      >
        <div className="text-purple font-bold mb-1">
          ⌨️ KEYBOARD SHORTCUTS
        </div>
        <div className="text-[#4b5563] text-xs">
          Quick reference guide for power users
        </div>
      </div>

      {/* Navigation Shortcuts */}
      <div className="mb-4">
        <div className="text-amber text-xs font-bold mb-2">
          NAVIGATION
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between">
            <span><kbd className="bg-black/40 px-1.5 py-0.5 rounded">Tab</kbd></span>
            <span className="text-text-muted">Switch between MAIN/AUTO views</span>
          </div>
          <div className="flex justify-between">
            <span><kbd className="bg-black/40 px-1.5 py-0.5 rounded">Ctrl+1</kbd></span>
            <span className="text-text-muted">Focus Hacker Assistant</span>
          </div>
          <div className="flex justify-between">
            <span><kbd className="bg-black/40 px-1.5 py-0.5 rounded">Ctrl+2</kbd></span>
            <span className="text-text-muted">Focus Automation Agent</span>
          </div>
        </div>
      </div>

      {/* Message Shortcuts */}
      <div className="mb-4">
        <div className="text-amber text-xs font-bold mb-2">
          MESSAGE ACTIONS
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between">
            <span><kbd className="bg-black/40 px-1.5 py-0.5 rounded">Enter</kbd></span>
            <span className="text-text-muted">Send command</span>
          </div>
          <div className="flex justify-between">
            <span><kbd className="bg-black/40 px-1.5 py-0.5 rounded">Shift+Enter</kbd></span>
            <span className="text-text-muted">New line (multi-line)</span>
          </div>
          <div className="flex justify-between">
            <span><kbd className="bg-black/40 px-1.5 py-0.5 rounded">Ctrl+↑/↓</kbd></span>
            <span className="text-text-muted">Navigate message history</span>
          </div>
        </div>
      </div>

      {/* Getting Started Tips */}
      <div className="mb-4">
        <div className="text-amber text-xs font-bold mb-2">
          💡 GETTING STARTED
        </div>
        <div className="flex flex-col gap-2">
          {viewMode === 'MAIN' ? (
            <>
              <div>
                <div className="text-green mb-0.5">&gt; bind to target [ID]</div>
                <div className="text-text-muted text-xs">Lock an IP or target for focused operations</div>
              </div>
              <div>
                <div className="text-green mb-0.5">&gt; start automation</div>
                <div className="text-text-muted text-xs">Launch background Automation Agent</div>
              </div>
              <div>
                <div className="text-green mb-0.5">&gt; show progress</div>
                <div className="text-text-muted text-xs">Monitor active execution nodes and skill runs</div>
              </div>
            </>
          ) : (
            <>
              <div>
                <div className="text-[#ec4899] mb-0.5">&gt; status</div>
                <div className="text-text-muted text-xs">Check current execution progress</div>
              </div>
              <div>
                <div className="text-[#ec4899] mb-0.5">&gt; pause</div>
                <div className="text-text-muted text-xs">Temporarily halt Automation Agent</div>
              </div>
              <div>
                <div className="text-[#ec4899] mb-0.5">&gt; log</div>
                <div className="text-text-muted text-xs">View detailed execution logs</div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Pro Tips */}
      <div
        className="p-3 bg-purple/5 border border-purple/20 rounded mb-3"
      >
        <div className="text-purple text-xs font-bold mb-1.5">
          🚀 PRO TIPS
        </div>
        <ul
          className="m-0 pl-4 text-text-muted text-xs list-none"
        >
          <li className="mb-1">
            <span className="mr-1">→</span>
            Switch to Execution Monitor to see real-time execution events and performance
          </li>
          <li className="mb-1">
            <span className="mr-1">→</span>
            Use [EDIT] button on previous commands to modify and re-run them
          </li>
          <li>
            <span className="mr-1">→</span>
            Keep an eye on Response Time in the telemetry sidebar — higher latency = slower agent
          </li>
        </ul>
      </div>
    </div>
  );
}
