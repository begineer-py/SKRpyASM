import './MessageFilterBar.css';

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
    <div className="msg-filter-bar" data-testid="message-filter-bar">
      <div className="filter-presets">
        <button type="button" className="filter-preset-btn" onClick={() => onChange({ ...FILTER_ALL_ON })}>
          全部
        </button>
        <button type="button" className="filter-preset-btn" onClick={() => onChange({ ...FILTER_USER_ONLY })}>
          僅對話
        </button>
        <button type="button" className="filter-preset-btn" onClick={() => onChange({ ...FILTER_AUTO_PENTEST })}>
          Auto Pentest
        </button>
      </div>

      <div className="filter-toggles">
        {TOGGLES.map(({ key, label }) => {
          const active = filter[key];
          return (
            <button
              key={key}
              type="button"
              className={`filter-chip ${active ? 'active' : ''}`}
              onClick={() => onChange({ ...filter, [key]: !active })}
            >
              {label}
            </button>
          );
        })}
      </div>

      {availableAgents.length > 0 && (
        <div className="filter-agents">
          <span className="filter-agents-label">Agents:</span>
          {availableAgents.map((agentId) => (
            <label key={agentId} className="filter-agent-item">
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
