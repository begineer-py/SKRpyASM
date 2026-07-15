import { Activity, Bot, ChevronDown, Eye, PanelLeftOpen, Radio } from 'lucide-react';

interface ChatHeaderProps {
  label: string | null;
  graphCount: number;
  showLogs: boolean;
  showEvents: boolean;
  showTree: boolean;
  treeAgentCount: number;
  hasTree: boolean;
  onToggleLogs: () => void;
  onToggleEvents: () => void;
  onToggleTree: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  label,
  graphCount,
  showLogs,
  showEvents,
  showTree,
  treeAgentCount,
  hasTree,
  onToggleLogs,
  onToggleEvents,
  onToggleTree,
}) => {
  return (
    <header className="ai-chat-header">
      <div className="ai-chat-header__context">
        <span className="ai-chat-header__icon"><Bot size={17} /></span>
        <div>
          <span className="ai-kicker">ACTIVE THREAD</span>
          <h2>{label || 'Untitled conversation'}</h2>
        </div>
        <ChevronDown size={15} className="ai-chat-header__chevron" aria-hidden="true" />
      </div>
      <div className="ai-chat-header__status"><Radio size={13} /><span>Live session</span></div>
      <div className="ai-chat-header__actions">
        {graphCount > 0 && (
          <button
            className={`ai-toolbar-button ${showLogs ? 'is-active' : ''}`}
            onClick={onToggleLogs}
            title="Toggle execution timeline"
            aria-pressed={showLogs}
          >
            <Activity size={15} /> <span>{graphCount} graph{graphCount > 1 ? 's' : ''}</span>
          </button>
        )}
        <button
          className={`ai-toolbar-button ${showEvents ? 'is-active' : ''}`}
          onClick={onToggleEvents}
          title="Toggle thread events"
          aria-pressed={showEvents}
        >
          <Eye size={15} /> <span>Events</span>
        </button>
        {hasTree && (
          <button
            className={`ai-toolbar-button ai-toolbar-button--agent ${showTree ? 'is-active' : ''}`}
            onClick={onToggleTree}
            title="Toggle Agent Tree"
            aria-pressed={showTree}
          >
            <PanelLeftOpen size={15} /> <span>{treeAgentCount > 1 ? `${treeAgentCount - 1} agent${treeAgentCount > 2 ? 's' : ''}` : 'Agents'}</span>
          </button>
        )}
      </div>
    </header>
  );
};

export default ChatHeader;
