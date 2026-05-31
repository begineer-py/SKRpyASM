# Technical Implementation Details - Message Loading & Scroll

## Scroll Handler Deep Dive

### Location
`/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/pages/AICenterPage/AICenterPage.tsx:246-260`

### Implementation Pattern: Top-Loading Infinite Scroll

The implementation loads older messages when scrolling to the TOP (not bottom), which is unconventional. This is achieved through:

1. **Display Limiting (Client-side)**
   - All messages fetched at once: `const msgArray = await assistantApi.getMessages(threadId)`
   - Only last N displayed: `const displayedMessages = messages.slice(-displayLimit)`
   - Older messages remain in state but hidden from view

2. **Scroll Detection**
   ```typescript
   if (e.currentTarget.scrollTop === 0) {
     // User has scrolled to top
   }
   ```
   - `scrollTop === 0` means container is at top
   - Triggers when user scrolls UP to reveal older messages

3. **Dynamic Loading**
   ```typescript
   setDisplayLimit(prev => prev + 50);
   ```
   - Increments by 50 on each top-scroll
   - Reveals 50 more messages above current view
   - No additional API calls (messages already in memory)

4. **Scroll Position Preservation**
   ```typescript
   const prevScrollHeight = container.scrollHeight;
   setDisplayLimit(prev => prev + 50);
   
   requestAnimationFrame(() => {
     container.scrollTop = container.scrollHeight - prevScrollHeight;
   });
   ```
   
   **Why this is needed:**
   - When displaying more messages above, container height increases
   - This would auto-scroll user to top
   - Math: `new scrollTop = new height - old height` keeps user at same visual position

   **Timeline:**
   1. `prevScrollHeight`: Store old height before update
   2. `setDisplayLimit()`: Triggers re-render
   3. React renders new messages
   4. `requestAnimationFrame()`: Waits for render to complete
   5. Calculates new scroll position: `container.scrollHeight - prevScrollHeight`
   6. Sets scroll position to maintain visual continuity

### Why NOT Bottom-Loading?

This approach (top-loading older when scrolling up) is used instead of the typical bottom-loading because:
- Messages represent a conversation thread with natural chronological order
- Users naturally read from top (oldest) to bottom (newest)
- New messages always appear at bottom (auto-scroll)
- Loading older context at top is UX-friendly for reviewing conversation history

---

## Message Fetching: `loadMessagesForThread()`

### Location
`/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/pages/AICenterPage/AICenterPage.tsx:88-122`

### Function Signature
```typescript
const loadMessagesForThread = async (threadId: string) => {
```

### Execution Flow

1. **API Call**
   ```typescript
   const msgArray: any[] = await assistantApi.getMessages(threadId);
   ```
   - Makes GET request to `/threads/{threadId}/messages/`
   - Receives array of all messages for thread
   - No pagination, no filtering at API level

2. **Content Parsing**
   ```typescript
   let textContent = "";
   let role = m.type === "human" ? "user" : "assistant";
   
   if (typeof m.content === "string") 
     textContent = m.content;
   else if (Array.isArray(m.content)) 
     textContent = m.content
       .map((c: any) => c.text || JSON.stringify(c))
       .join("\n");
   ```
   
   **Handles multiple content formats:**
   - String: Direct text
   - Array of objects: Extract `.text` property or serialize
   - Tool calls: `[Tool Call: tool1, tool2, ...]`
   - Empty messages: `[Empty Message]` placeholder
   - Tool execution: `[Tool Execution Completed]`

3. **Transformation**
   ```typescript
   return {
     id: m.id,
     role: role,
     textContent: textContent,
   };
   ```
   - Normalizes to consistent format for rendering
   - Role: Either "user" or "assistant"
   - Text content: Always string, never null/undefined

4. **State Update**
   ```typescript
   setDisplayLimit(50);
   setMessages(parsed);
   ```
   - Resets pagination to show last 50
   - Replaces entire messages array
   - Triggers re-render

### Error Handling
```typescript
catch (err) {
  console.error("Failed to load messages", err);
  setMessages([]);
}
```
- Logs error to console
- Sets empty messages array (prevents crash)
- No user-facing error UI (silent failure)

---

## Streaming Implementation: Server-Sent Events (SSE)

### Location
`/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/services/assistantApi.ts:50-109`

### Why SSE Instead of WebSocket?

- **EventSource API**: Browser built-in, no library needed
- **Server-sent events**: Unidirectional (server → client)
- **Stateless**: HTTP-based, no persistent connection issues
- **Auto-reconnect**: Browser handles reconnection automatically
- **Simple**: Ideal for streaming responses

### Setup Phase

```typescript
const params = new URLSearchParams({
  assistant_id: assistantId,
  content,
});
const url = `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant/threads/${threadId}/messages/stream/?${params.toString()}`;
const es = new EventSource(url);
```

**Key Points:**
- Query params, not body (EventSource only supports GET)
- Assistant ID: Usually 'hacker_assistant_agent'
- Content: The user's message text
- EventSource opens persistent GET connection

### Event Handlers

#### 1. Message Events (Token Streaming)
```typescript
es.onmessage = (e) => {
  if (e.data && e.data !== '[DONE]') {
    onChunk(e.data);
  }
};
```
- Default event name: `message`
- Called for each token chunk from backend
- Accumulates in `streamingText` state
- Displayed in UI in real-time
- Check prevents processing end sentinel

#### 2. Custom Events
```typescript
es.addEventListener('start', () => { /* streaming started */ });

es.addEventListener('stats', (e: MessageEvent) => {
  try {
    const payload = JSON.parse(e.data);
    if (payload.elapsed_ms !== undefined && onStats) {
      onStats(payload.elapsed_ms);
    }
  } catch { /* ignore */ }
});

es.addEventListener('done', () => {
  es.close();
  onDone();
});

es.addEventListener('error', (e: MessageEvent) => {
  es.close();
  try {
    const payload = JSON.parse(e.data);
    onError(payload.error || 'Unknown streaming error');
  } catch {
    onError('Stream error (unparseable)');
  }
});
```

**Event Types:**
- `start`: Signals streaming began
- `stats`: Performance metrics (JSON: `{ elapsed_ms: number }`)
- `done`: Streaming complete (normal termination)
- `error`: Server-side error (JSON: `{ error: string }`)

#### 3. Network Errors
```typescript
es.onerror = () => {
  es.close();
  onError('Connection lost — the server may have crashed or timed out.');
  onDone();
};
```
- Browser-level connection failure
- Examples: Server crash, timeout, network disconnect
- Calls both `onError()` and `onDone()`

### Cleanup
```typescript
return () => es.close();
```
- Returns abort function
- Called to terminate stream early (e.g., user cancels)
- Can be stored in ref to cancel previous stream if new message sent

---

## State Management: React Hooks Pattern

### Display Limit (Pagination State)

**File:** `AICenterPage.tsx:15`
```typescript
const [displayLimit, setDisplayLimit] = useState(50);
```

**Usage:**
1. **Initial render**: Shows last 50 messages
2. **On top-scroll**: Increment by 50
3. **On thread change**: Reset to 50
4. **On new message**: Not affected (slice always uses latest)

**Formula:**
```typescript
const displayedMessages = messages.slice(-displayLimit);
```
- Negative index: Count from end
- `slice(-50)`: Last 50 elements
- `slice(-100)`: Last 100 elements
- Memory efficient: No new array copy, just view

### Streaming Text (Real-time Accumulation)

**File:** `AICenterPage.tsx:14`
```typescript
const [streamingText, setStreamingText] = useState<string | null>(null);
```

**On each chunk:**
```typescript
setStreamingText(prev => (prev ?? "") + chunk);
```
- Accumulates tokens into single string
- `prev ?? ""`: Handles null/undefined initial value
- Set to `null` when complete

**Effects:**
- Re-render on every chunk (causes animation)
- Auto-scroll triggered via useEffect: `[messages, streamingText]`
- Displayed in temporary message bubble

### Messages Array (Full Conversation)

**File:** `AICenterPage.tsx:11`
```typescript
const [messages, setMessages] = useState<any[]>([]);
```

**Updates:**
1. **Load from API**: `setMessages(parsed)` - Replace entire array
2. **User message**: `setMessages(prev => [...prev, { role: "user", ... }])` - Append
3. **Streaming done**: `await loadMessagesForThread()` - Reload all
4. **Thread change**: `setMessages([])` - Clear

### Cleanup Stream Ref

**File:** `AICenterPage.tsx:27`
```typescript
const cleanupStreamRef = useRef<(() => void) | null>(null);
```

**Purpose:**
- Store cleanup function from `streamMessage()`
- Abort previous stream if new message sent while streaming
- Usage:
  ```typescript
  cleanupStreamRef.current?.();  // Abort previous
  cleanupStreamRef.current = cleanup;  // Store new
  ```

---

## Message Parsing Patterns

### Type Detection
```typescript
let role = m.type === "human" ? "user" : "assistant";
```
- Backend sends `type: "human"` for user messages
- Convert to `role: "user"` for consistency
- Everything else → `role: "assistant"`

### Content Extraction
```typescript
if (typeof m.content === "string") 
  textContent = m.content;
else if (Array.isArray(m.content)) {
  textContent = m.content
    .map((c: any) => c.text || JSON.stringify(c))
    .join("\n");
}
```

**Handles:**
- Direct string: Use as-is
- Array of objects: Extract `.text` from each
- Fallback: JSON-stringify if no `.text` property
- Join with newlines

### Tool Call Detection
```typescript
if (m.tool_calls && m.tool_calls.length > 0) {
  textContent = `[Tool Call: ${m.tool_calls
    .map((tc: any) => tc.name)
    .join(', ')}]`;
}
```
- Checks for `tool_calls` array
- Extracts tool names
- Formats as `[Tool Call: name1, name2, ...]`

### Fallback Handling
```typescript
if (!textContent.trim()) {
  if (m.tool_calls && m.tool_calls.length > 0) {
    textContent = `[Tool Call: ...]`;
  } else if (m.type === "tool") {
    textContent = `[Tool Execution Completed]`;
  } else {
    textContent = `[Empty Message]`;
  }
}
```
- Three-level fallback:
  1. Tool calls present → Show tool names
  2. Message type is "tool" → Show execution complete
  3. Otherwise → Show empty placeholder

---

## Rendering Patterns

### Markdown Support
```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

<ReactMarkdown remarkPlugins={[remarkGfm]}>
  {msg.textContent}
</ReactMarkdown>
```

**Features:**
- Parses markdown in assistant messages
- GitHub Flavored Markdown: Tables, strikethrough, etc.
- User messages: Plain text (no markdown parsing)

### Conditional Rendering
```typescript
{messages.length === 0 && !streamingText && (
  <div className="empty-chat">...</div>
)}
```
- Empty state only if:
  - No messages loaded
  - AND no streaming in progress

```typescript
{displayLimit < messages.length && (
  <div className="loading-older">Loading older messages...</div>
)}
```
- Shows when not all messages visible
- Pagination indicator

### Message Keys
```typescript
{displayedMessages.map((msg: any) => (
  <div key={msg.id || Math.random()}>
```
- Prefer message ID (stable)
- Fallback: `Math.random()` (anti-pattern, but okay for streaming chat)
- Avoids React key warnings

---

## Performance Characteristics

### Memory Usage
- **Stores ALL messages**: No pagination cleanup
- **Risk for long conversations**: Large arrays consume memory
- **Display limit only hides**: Doesn't remove from state
- **Solution needed**: Implement server-side pagination or windowing

### Re-render Triggers
1. **Message load**: Full re-render
2. **On scroll**: Minimal (display slicing only)
3. **Each stream chunk**: Full component re-render
   - Streaming causes 10-50 renders per response
   - Could be optimized with separate component or memo

### Network Calls
- **Load messages**: 1 GET per thread change
- **Streaming**: 1 GET (persistent) per send
- **Auto-rename**: 1 PATCH (only for new threads)
- **Reload after stream**: 1 GET
- **Total per message**: 2-3 requests

---

## Configuration

### API Base URL
**File:** `/home/hacker/Desktop/share/C2_Django_AI_git/frontend/src/config.ts:5`
```typescript
DJANGO_API_BASE: 'http://127.0.0.1:8000/api',
```
- Axios instance: `baseURL: ${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant`
- Final: `http://127.0.0.1:8000/api/assistant`

### Assistant ID
**Default:** `'hacker_assistant_agent'`
- Thread creation: Line 12
- Message streaming: Line 53 (parameter)

### Pagination Defaults
- **Initial display**: 50 messages (Line 15)
- **Increment**: 50 per scroll (Line 251)

