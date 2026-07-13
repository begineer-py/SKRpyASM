import { useState } from 'react';
import type { DisplayMessage } from '../types/messages';
import './ToolCallGroup.css';

interface ToolCallGroupProps {
  calls: DisplayMessage[];
  results: DisplayMessage[];
  defaultOpen?: boolean;
}

function ToolCallItem({ msg }: { msg: DisplayMessage }) {
  const names = msg.toolCalls?.map((tc) => tc.name).join(', ') || msg.toolName || 'tool';
  const argsPreview = msg.toolCalls
    ?.map((tc) => {
      try {
        return `${tc.name}(${JSON.stringify(tc.args ?? {}).slice(0, 120)})`;
      } catch {
        return tc.name;
      }
    })
    .join('\n');

  return (
    <div className="tcg-item tcg-item--call">
      <div className="tcg-item-label">🔧 Call: {names}</div>
      {argsPreview && <pre className="tcg-item-body">{argsPreview}</pre>}
      {!argsPreview && msg.textContent && <pre className="tcg-item-body">{msg.textContent}</pre>}
    </div>
  );
}

function ToolResultItem({ msg }: { msg: DisplayMessage }) {
  const preview =
    msg.textContent.length > 800 ? `${msg.textContent.slice(0, 800)}…` : msg.textContent;
  return (
    <div className="tcg-item tcg-item--result">
      <div className="tcg-item-label">↩ Result{msg.toolName ? `: ${msg.toolName}` : ''}</div>
      <pre className="tcg-item-body">{preview}</pre>
    </div>
  );
}

export function ToolCallGroup({ calls, results, defaultOpen = false }: ToolCallGroupProps) {
  const [open, setOpen] = useState(defaultOpen);
  const names = calls
    .flatMap((c) => c.toolCalls?.map((tc) => tc.name) ?? (c.toolName ? [c.toolName] : []))
    .filter(Boolean);

  return (
    <div className="tool-call-group" data-testid="tool-call-group">
      <button type="button" className="tcg-header" onClick={() => setOpen((v) => !v)}>
        <span className="tcg-icon">🔧</span>
        <span>
          {calls.length} tool call{calls.length > 1 ? 's' : ''}
          {results.length > 0 ? ` · ${results.length} result${results.length > 1 ? 's' : ''}` : ''}
        </span>
        <span className="tcg-names">{names.join(', ')}</span>
        <span className="tcg-toggle">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="tcg-body">
          {calls.map((c) => (
            <ToolCallItem key={c.id} msg={c} />
          ))}
          {results.map((r) => (
            <ToolResultItem key={r.id} msg={r} />
          ))}
        </div>
      )}
    </div>
  );
}

export default ToolCallGroup;
