import ThreadEventTimeline from '../../../components/ThreadEventTimeline';
import type { RefObject } from 'react';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerDismiss,
  DrawerHeader,
  DrawerTitle,
} from '../../../components/ui/drawer';

interface ThreadEventsPanelProps {
  open: boolean;
  threadId: string;
  onOpenChange: (open: boolean) => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
}

const ThreadEventsPanel: React.FC<ThreadEventsPanelProps> = ({ open, threadId, onOpenChange, triggerRef }) => {
  return (
    <Drawer open={open} onOpenChange={(nextOpen) => {
      onOpenChange(nextOpen);
      if (!nextOpen) {
        window.requestAnimationFrame(() => triggerRef.current?.focus());
      }
    }}>
      <DrawerContent
        id="ai-thread-events-drawer"
        aria-describedby="ai-thread-events-description"
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          triggerRef.current?.focus();
        }}
      >
        <DrawerHeader>
          <div>
            <DrawerTitle>Thread events</DrawerTitle>
            <DrawerDescription id="ai-thread-events-description">
              Review thread-scoped activity without mixing it with execution graph events.
            </DrawerDescription>
          </div>
          <DrawerDismiss />
        </DrawerHeader>
        <div className="mt-6 min-h-0 flex-1 overflow-hidden">
          <ThreadEventTimeline threadId={threadId} autoScroll />
        </div>
      </DrawerContent>
    </Drawer>
  );
};

export default ThreadEventsPanel;
