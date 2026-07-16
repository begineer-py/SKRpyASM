import { Activity, Bot, Eye, PanelLeftOpen } from 'lucide-react';
import type { RefObject } from 'react';

interface ChatHeaderProps {
  label: string | null;
  graphCount: number;
  showEvents: boolean;
  showTree: boolean;
  treeAgentCount: number;
  hasTree: boolean;
  selectedGraphId: number | null;
  onOpenGraph: (graphId: number) => void;
  onToggleEvents: () => void;
  onToggleTree: () => void;
  agentTriggerRef: RefObject<HTMLButtonElement | null>;
  eventsTriggerRef: RefObject<HTMLButtonElement | null>;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  label,
  graphCount,
  showEvents,
  showTree,
  treeAgentCount,
  hasTree,
  selectedGraphId,
  onOpenGraph,
  onToggleEvents,
  onToggleTree,
  agentTriggerRef,
  eventsTriggerRef,
}) => {
  return (
    <header className="ai-chat-header">
      <div className="ai-chat-header__context">
        <span className="ai-chat-header__icon"><Bot size={17} /></span>
        <div>
          <h2>{label || 'Untitled conversation'}</h2>
        </div>
      </div>
      <div className="ai-chat-header__actions">
        {graphCount > 0 && selectedGraphId != null && (
          <button
            className="ai-toolbar-button"
            onClick={() => onOpenGraph(selectedGraphId)}
            title="Open execution monitor"
          >
            <Activity size={15} /> <span>{graphCount} graph{graphCount > 1 ? 's' : ''}</span>
          </button>
        )}
          <button
            ref={eventsTriggerRef}
            className={`ai-toolbar-button ${showEvents ? 'is-active' : ''}`}
            onClick={onToggleEvents}
            title="Open thread events"
            aria-expanded={showEvents}
            aria-controls="ai-thread-events-drawer"
        >
          <Eye size={15} /> <span>Events</span>
        </button>
        {hasTree && (
          <button
            ref={agentTriggerRef}
            className={`ai-toolbar-button ai-toolbar-button--agent ${showTree ? 'is-active' : ''}`}
            onClick={onToggleTree}
            title="Open agent context"
            aria-expanded={showTree}
            aria-controls="ai-agent-context-drawer"
          >
            <PanelLeftOpen size={15} /> <span>{treeAgentCount > 1 ? `${treeAgentCount - 1} agent${treeAgentCount > 2 ? 's' : ''}` : 'Agents'}</span>
          </button>
        )}
      </div>
    </header>
  );
};

export default ChatHeader;
