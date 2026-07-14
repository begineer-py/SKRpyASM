import { useState } from 'react';
import type { DisplayMessage } from '../types/messages';

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
    <div className="rounded-lg p-2 px-2.5 bg-[#0f172a] border border-[#1e293b] border-l-[3px] border-l-sky-400">
      <div className="text-[0.72rem] font-semibold text-[#94a3b8] mb-1">🔧 Call: {names}</div>
      {argsPreview && <pre className="m-0 whitespace-pre-wrap break-words font-['Fira_Code',monospace] text-[0.7rem] text-[#e2e8f0] max-h-60 overflow-auto">{argsPreview}</pre>}
      {!argsPreview && msg.textContent && <pre className="m-0 whitespace-pre-wrap break-words font-['Fira_Code',monospace] text-[0.7rem] text-[#e2e8f0] max-h-60 overflow-auto">{msg.textContent}</pre>}
    </div>
  );
}

function ToolResultItem({ msg }: { msg: DisplayMessage }) {
  const preview =
    msg.textContent.length > 800 ? `${msg.textContent.slice(0, 800)}…` : msg.textContent;
  return (
    <div className="rounded-lg p-2 px-2.5 bg-[#0f172a] border border-[#1e293b] border-l-[3px] border-l-green-500">
      <div className="text-[0.72rem] font-semibold text-[#94a3b8] mb-1">↩ Result{msg.toolName ? `: ${msg.toolName}` : ''}</div>
      <pre className="m-0 whitespace-pre-wrap break-words font-['Fira_Code',monospace] text-[0.7rem] text-[#e2e8f0] max-h-60 overflow-auto">{preview}</pre>
    </div>
  );
}

export function ToolCallGroup({ calls, results, defaultOpen = false }: ToolCallGroupProps) {
  const [open, setOpen] = useState(defaultOpen);
  const names = calls
    .flatMap((c) => c.toolCalls?.map((tc) => tc.name) ?? (c.toolName ? [c.toolName] : []))
    .filter(Boolean);

  return (
    <div className="mx-3 my-2 border border-[#1e293b] rounded-[10px] bg-[rgba(30,41,59,0.55)] overflow-hidden" data-testid="tool-call-group">
      <button
        type="button"
        className="w-full flex items-center gap-2 px-3 py-2 bg-transparent border-none text-[#cbd5e1] text-[0.78rem] cursor-pointer text-left hover:bg-[rgba(51,65,85,0.4)]"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="shrink-0">🔧</span>
        <span>
          {calls.length} tool call{calls.length > 1 ? 's' : ''}
          {results.length > 0 ? ` · ${results.length} result${results.length > 1 ? 's' : ''}` : ''}
        </span>
        <span className="flex-1 min-w-0 text-[#64748b] overflow-hidden text-ellipsis whitespace-nowrap font-['Fira_Code',monospace] text-[0.72rem]">{names.join(', ')}</span>
        <span className="text-[#64748b] text-[0.7rem]">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="border-t border-[#1e293b] px-3 py-2 pb-3 flex flex-col gap-2">
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
