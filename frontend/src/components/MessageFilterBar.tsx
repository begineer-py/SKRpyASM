import { cn } from '@/lib/utils';

export interface MessageFilterState {
  showUserConv: boolean;
  showAiResponse: boolean;
  showToolCalls: boolean;
  showSubagent: boolean;
  showSystem: boolean;
  agentFilter: string[];
}

export const DEFAULT_MSG_FILTER: MessageFilterState = {
  showUserConv: true,
  showAiResponse: true,
  showToolCalls: false,
  showSubagent: true,
  showSystem: false,
  agentFilter: [],
};

export const FILTER_ALL_ON: MessageFilterState = {
  showUserConv: true,
  showAiResponse: true,
  showToolCalls: true,
  showSubagent: true,
  showSystem: true,
  agentFilter: [],
};

export const FILTER_USER_ONLY: MessageFilterState = {
  showUserConv: true,
  showAiResponse: true,
  showToolCalls: false,
  showSubagent: false,
  showSystem: false,
  agentFilter: [],
};

export const FILTER_AUTO_PENTEST: MessageFilterState = {
  showUserConv: true,
  showAiResponse: true,
  showToolCalls: false,
  showSubagent: true,
  showSystem: false,
  agentFilter: [],
};

interface MessageFilterBarProps {
  filter: MessageFilterState;
  onChange: (next: MessageFilterState) => void;
  availableAgents?: string[];
}

const TOGGLES: Array<{
  key: keyof Pick<MessageFilterState, 'showUserConv' | 'showAiResponse' | 'showToolCalls' | 'showSubagent' | 'showSystem'>;
  label: string;
}> = [
  { key: 'showUserConv', label: '👤 User' },
  { key: 'showAiResponse', label: '🤖 AI' },
  { key: 'showToolCalls', label: '🔧 Tools' },
  { key: 'showSubagent', label: '🕸 Sub-agent' },
  { key: 'showSystem', label: '⚙ System' },
];

export function MessageFilterBar({ filter, onChange, availableAgents = [] }: MessageFilterBarProps) {
  const toggleAgent = (agentId: string) => {
    const has = filter.agentFilter.includes(agentId);
    onChange({
      ...filter,
      agentFilter: has
        ? filter.agentFilter.filter((a) => a !== agentId)
        : [...filter.agentFilter, agentId],
    });
  };

  return (
    <div
      className="flex flex-wrap gap-2 items-center px-3 py-2 border-b border-[#1e293b] bg-[rgba(15,23,42,0.85)] shrink-0"
      data-testid="message-filter-bar"
    >
      <div className="flex flex-wrap gap-1.5 items-center">
        <button
          type="button"
          className="bg-[#1e293b] border border-[#334155] text-[#94a3b8] rounded-md px-2.5 py-0.5 text-[0.7rem] cursor-pointer transition-all duration-150 hover:border-green-500 hover:text-[#e2e8f0]"
          onClick={() => onChange({ ...FILTER_ALL_ON })}
        >
          全部
        </button>
        <button
          type="button"
          className="bg-[#1e293b] border border-[#334155] text-[#94a3b8] rounded-md px-2.5 py-0.5 text-[0.7rem] cursor-pointer transition-all duration-150 hover:border-green-500 hover:text-[#e2e8f0]"
          onClick={() => onChange({ ...FILTER_USER_ONLY })}
        >
          僅對話
        </button>
        <button
          type="button"
          className="bg-[#1e293b] border border-[#334155] text-[#94a3b8] rounded-md px-2.5 py-0.5 text-[0.7rem] cursor-pointer transition-all duration-150 hover:border-green-500 hover:text-[#e2e8f0]"
          onClick={() => onChange({ ...FILTER_AUTO_PENTEST })}
        >
          Auto Pentest
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 items-center">
        {TOGGLES.map(({ key, label }) => {
          const active = filter[key];
          return (
            <button
              key={key}
              type="button"
              className={cn(
                'bg-transparent border border-[#334155] text-[#64748b] rounded-full px-2.5 py-0.5 text-[0.7rem] cursor-pointer transition-all duration-150 hover:border-[#64748b] hover:text-[#cbd5e1]',
                active && 'bg-[rgba(34,197,94,0.12)] border-green-500 text-[#86efac]',
              )}
              onClick={() => onChange({ ...filter, [key]: !active })}
            >
              {label}
            </button>
          );
        })}
      </div>

      {availableAgents.length > 0 && (
        <div className="flex flex-wrap gap-2 items-center ml-auto text-[0.7rem] text-[#94a3b8]">
          <span className="text-[#64748b]">Agents:</span>
          {availableAgents.map((agentId) => (
            <label key={agentId} className="inline-flex items-center gap-1 cursor-pointer text-[#94a3b8] [&_input]:accent-green-500">
              <input
                type="checkbox"
                checked={filter.agentFilter.length === 0 || filter.agentFilter.includes(agentId)}
                onChange={() => toggleAgent(agentId)}
              />
              {agentId}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export function messagePassesFilter(
  category: string,
  filter: MessageFilterState,
  assistantId?: string,
): boolean {
  const byCategory: Record<string, boolean> = {
    user: filter.showUserConv,
    ai_response: filter.showAiResponse,
    tool_call: filter.showToolCalls,
    tool_result: filter.showToolCalls,
    subagent_dispatch: filter.showSubagent,
    system: filter.showSystem,
  };
  if (!byCategory[category]) return false;
  if (filter.agentFilter.length > 0 && assistantId && !filter.agentFilter.includes(assistantId)) {
    return false;
  }
  return true;
}

export default MessageFilterBar;
