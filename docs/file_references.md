# Quick File Reference Guide

## Main Files (Absolute Paths)

### 1. AI Center Main Page
**File:** `/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/pages/AICenterPage/AICenterPage.tsx`
- **Lines 1-50:** Imports & State Initialization
- **Lines 31-32:** `scrollToBottom()` function
- **Lines 35-37:** Auto-scroll effect
- **Lines 40-42:** Load threads on mount
- **Lines 45-49:** Load messages on thread select
- **Lines 51-86:** `loadThreads()` function
- **Lines 88-122:** `loadMessagesForThread()` function - MAIN MESSAGE LOADING
- **Lines 124-132:** `createNewThread()` function
- **Lines 134-147:** `handleDeleteThread()` function
- **Lines 149-240:** `handleSend()` function - MESSAGE SENDING & STREAMING
- **Lines 246-260:** `handleScroll()` function - SCROLL HANDLER
- **Lines 262:** `displayedMessages` calculation - PAGINATION
- **Lines 363:** Messages area with onScroll handler
- **Lines 371-375:** Loading indicator for older messages
- **Lines 377-389:** Message rendering loop
- **Lines 391-399:** Streaming message display

### 2. API Service
**File:** `/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/services/assistantApi.ts`
- **Lines 1-6:** Axios configuration
- **Lines 8-16:** `createThread()` - Create new conversation
- **Lines 18-22:** `updateThread()` - Rename thread
- **Lines 24-28:** `getMessages()` - GET MESSAGES ENDPOINT
- **Lines 30-37:** `postMessage()` - Send message (blocking)
- **Lines 39-109:** `streamMessage()` - STREAM ENDPOINT (SSE)
  - **Lines 67-71:** Message event handler
  - **Lines 76-83:** Stats event handler
  - **Lines 85-88:** Done event handler
  - **Lines 90-98:** Error event handler
  - **Lines 101-105:** Network error handler
- **Lines 111-115:** `getThreads()` - Get all conversations
- **Lines 117-121:** `deleteThread()` - Delete conversation
- **Lines 123-127:** `deleteMessage()` - Delete message
- **Lines 129-133:** `bindTarget()` - Bind target to thread
- **Lines 135-139:** `unbindTarget()` - Remove target binding

### 3. Styling
**File:** `/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/pages/AICenterPage/AICenter.css`
- **Lines 243-250:** `.messages-area` - Main container
- **Lines 274-290:** `.message` - Individual message styling
- **Lines 293-302:** `.message-user` - User message styling
- **Lines 304-314:** `.message-assistant` - Assistant message styling
- **Lines 372-374:** `.loading-older` - Pagination indicator

### 4. Configuration
**File:** `/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/config.ts`
- **Line 5:** Django API base URL

### 5. Routing
**File:** `/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/App.tsx`
- **Line 7:** Import AICenterPage
- **Line 27:** Route definition: `/aicenter`

---

## Key Code Snippets by Feature

### Message Fetching (Lines 88-90 in AICenterPage.tsx)
```typescript
const loadMessagesForThread = async (threadId: string) => {
  try {
    const msgArray: any[] = await assistantApi.getMessages(threadId);
    // ...
```

### Scroll Event Handler (Lines 246-260 in AICenterPage.tsx)
```typescript
const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
  if (e.currentTarget.scrollTop === 0) {
    if (displayLimit < messages.length) {
      // Load more messages...
```

### Auto-Scroll (Lines 31-32 in AICenterPage.tsx)
```typescript
const scrollToBottom = () => {
  messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
};
```

### Streaming (Lines 186-237 in AICenterPage.tsx)
```typescript
const cleanup = assistantApi.streamMessage(
  selectedThreadId,
  userMsg,
  'hacker_assistant_agent',
  (chunk: string) => { setStreamingText(...) },
  // ... onDone, onError
);
```

### Pagination Display (Line 262 in AICenterPage.tsx)
```typescript
const displayedMessages = messages.slice(-displayLimit);
```

---

## API Endpoints Summary

| Feature | HTTP | Endpoint | Function |
|---------|------|----------|----------|
| Load Messages | GET | `/threads/{threadId}/messages/` | `getMessages()` |
| Stream Message | GET | `/threads/{threadId}/messages/stream/` | `streamMessage()` |
| Get Threads | GET | `/threads/` | `getThreads()` |
| Create Thread | POST | `/threads/` | `createThread()` |
| Update Thread | PATCH | `/threads/{threadId}/` | `updateThread()` |
| Delete Thread | DELETE | `/threads/{threadId}/` | `deleteThread()` |
| Delete Message | DELETE | `/threads/{threadId}/messages/{messageId}/` | `deleteMessage()` |
| Bind Target | PATCH | `/threads/{threadId}/bind_target/` | `bindTarget()` |
| Unbind Target | DELETE | `/threads/{threadId}/bind_target/` | `unbindTarget()` |

---

## State Variables (Lines 8-28 in AICenterPage.tsx)

```typescript
// Main chat state
const [allThreads, setAllThreads] = useState<any[]>([]);                    // Line 9
const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null); // Line 10
const [messages, setMessages] = useState<any[]>([]);                        // Line 11
const [inputVal, setInputVal] = useState("");                               // Line 12
const [isSending, setIsSending] = useState(false);                          // Line 13
const [streamingText, setStreamingText] = useState<string | null>(null));   // Line 14
const [displayLimit, setDisplayLimit] = useState(50);                       // Line 15 - PAGINATION KEY

// UI state
const [threadsLoading, setThreadsLoading] = useState(true);                // Line 18
const [threadsError, setThreadsError] = useState<string | null>(null));    // Line 19
const [sidebarOpen, setSidebarOpen] = useState(true);                      // Line 20

// Target binding
const [boundTargetId, setBoundTargetId] = useState<number | null>(null));  // Line 23

// Refs
const messagesEndRef = useRef<HTMLDivElement>(null);                       // Line 26
const cleanupStreamRef = useRef<(() => void) | null>(null));               // Line 27
const threadNameById = useRef<Record<string, string>>({});                 // Line 28
```

---

## Component Dependencies

```
AICenterPage.tsx
├── imports: react-markdown, remarkGfm
├── imports: assistantApi from ./services/assistantApi.ts
├── imports: AICenter.css
└── renders:
    ├── Sidebar (thread list)
    ├── Messages area (with onScroll={handleScroll})
    ├── Input area (message input)
    └── Uses: messagesEndRef for auto-scroll
```

---

## Message Flow Diagram

```
1. Component Mount
   ↓
2. loadThreads() → GET /threads/
   ↓
3. User selects thread → setState(selectedThreadId)
   ↓
4. useEffect triggers → loadMessagesForThread()
   ↓
5. getMessages() → GET /threads/{id}/messages/
   ↓
6. Parse & display messages
   ↓
7. User scrolls to top → handleScroll() → increase displayLimit
   ↓
8. Slice messages → display last N messages
   ↓
9. User sends message → handleSend()
   ↓
10. streamMessage() → SSE GET /threads/{id}/messages/stream/
    ↓
11. onChunk → accumulate in streamingText
    ↓
12. onDone → reload all messages
    ↓
13. scrollToBottom() via useEffect
```

