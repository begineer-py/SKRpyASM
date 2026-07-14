import ThreadEventTimeline from '../../../components/ThreadEventTimeline';

interface ThreadEventsPanelProps {
  threadId: string;
  onClose: () => void;
}

const ThreadEventsPanel: React.FC<ThreadEventsPanelProps> = ({ threadId, onClose }) => {
  return (
    <div className="logs-panel">
      <div className="logs-panel-header">
        <div className="logs-panel-title">
          <span>THREAD EVENTS</span>
        </div>
        <div className="logs-panel-controls">
          <button
            className="logs-close-btn"
            onClick={onClose}
            title="Close events panel"
          >✕</button>
        </div>
      </div>
      <div className="logs-panel-body">
        <ThreadEventTimeline threadId={threadId} autoScroll />
      </div>
    </div>
  );
};

export default ThreadEventsPanel;
