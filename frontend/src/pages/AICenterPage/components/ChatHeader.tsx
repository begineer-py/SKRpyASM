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
    <div className="chat-header-bar">
      <div className="chat-header-label">{label}</div>
      <div className="chat-header-actions">
        {graphCount > 0 && (
          <button
            className={`tool-log-toggle-btn ${showLogs ? 'active' : ''}`}
            onClick={onToggleLogs}
            title="Toggle execution timeline"
          >
            {graphCount} graph{graphCount > 1 ? 's' : ''}
          </button>
        )}
        <button
          className={`tool-log-toggle-btn ${showEvents ? 'active' : ''}`}
          onClick={onToggleEvents}
          title="Toggle thread events"
        >
          Events
        </button>
        {hasTree && (
          <button
            className={`tree-toggle-btn ${showTree ? 'active' : ''}`}
            onClick={onToggleTree}
            title="Toggle Agent Tree"
          >
            {treeAgentCount > 1 ? `${treeAgentCount - 1} agent${treeAgentCount > 2 ? 's' : ''}` : 'Tree'}
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatHeader;
