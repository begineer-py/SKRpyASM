import { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { assistantApi } from '../../services/assistantApi';
import './AICenter.css';

const AICenterPage: React.FC = () => {
  // --- Chat State ---
  const [allThreads, setAllThreads] = useState<any[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [displayLimit, setDisplayLimit] = useState(50);

  // Sidebar state
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [threadsError, setThreadsError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [targetSearchId, setTargetSearchId] = useState<string>("");

  // Target binding
  const [boundTargetId, setBoundTargetId] = useState<number | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cleanupStreamRef = useRef<(() => void) | null>(null);
  const threadNameById = useRef<Record<string, string>>({});

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  // Load all threads on mount or filter change
  useEffect(() => {
    loadThreads();
  }, [targetSearchId]);

  // Load messages when thread changes
  useEffect(() => {
    if (selectedThreadId) {
      loadMessagesForThread(selectedThreadId);
    }
  }, [selectedThreadId]);

  const loadThreads = async () => {
    setThreadsLoading(true);
    setThreadsError(null);
    try {
      const params: any = { include_hidden: false };
      if (targetSearchId.trim()) {
        params.target_id = parseInt(targetSearchId);
      }
      const res: any[] = await assistantApi.getThreads(params) as any[];
      const filteredThreads = res
        .sort((a: any, b: any) => Number(b.id) - Number(a.id));
      setAllThreads(filteredThreads);

      // Build name mapping
      const map: Record<string, string> = {};
      for (const t of filteredThreads) {
        if (t?.id != null) {
          map[String(t.id)] = String(t.name || '').trim() || `Thread ${t.id}`;
        }
      }
      threadNameById.current = map;

      // Auto-select first thread if available
      if (filteredThreads.length > 0 && !selectedThreadId) {
        const firstThread = filteredThreads[0];
        setSelectedThreadId(String(firstThread.id));
        setBoundTargetId(firstThread.bound_target_id ?? null);
      } else if (filteredThreads.length === 0 && selectedThreadId) {
        setSelectedThreadId(null);
        setMessages([]);
      } else if (selectedThreadId) {
        // Update boundTargetId for the currently selected thread
        const currentThread = filteredThreads.find((t: any) => String(t.id) === selectedThreadId);
        if (currentThread) {
          setBoundTargetId(currentThread.bound_target_id ?? null);
        }
      }
    } catch (err) {
      console.error("Failed to load threads", err);
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      setThreadsError(`Failed to load: ${errorMsg}`);
    } finally {
      setThreadsLoading(false);
    }
  };

  const loadMessagesForThread = async (threadId: string) => {
    try {
      const msgArray: any[] = await assistantApi.getMessages(threadId);
      const parsed = msgArray.map((m: any) => {
        let textContent = "";
        let role = m.type === "human" ? "user" : "assistant";

        if (typeof m.content === "string") textContent = m.content;
        else if (Array.isArray(m.content)) {
          textContent = m.content.map((c: any) => c.text || JSON.stringify(c)).join("\n");
        }

        if (!textContent.trim()) {
          if (m.tool_calls && m.tool_calls.length > 0) {
            textContent = `[Tool Call: ${m.tool_calls.map((tc: any) => tc.name).join(', ')}]`;
          } else if (m.type === "tool") {
            textContent = `[Tool Execution Completed]`;
          } else {
            textContent = `[Empty Message]`;
          }
        }

        return {
          id: m.id,
          role: role,
          textContent: textContent,
        };
      });
      setDisplayLimit(50);
      setMessages(parsed);
    } catch (err) {
      console.error("Failed to load messages", err);
      setMessages([]);
    }
  };

  const createNewThread = async () => {
    try {
      const res: any = await assistantApi.createThread('New chat');
      await loadThreads();
      setSelectedThreadId(String(res.id));
    } catch (err) {
      console.error("Failed to create thread", err);
    }
  };

  const handleDeleteThread = async (threadId: string | null) => {
    if (!threadId) return;
    if (!window.confirm("確定要刪除這個對話嗎？")) return;
    try {
      await assistantApi.deleteThread(threadId);
      if (selectedThreadId === threadId) {
        setSelectedThreadId(null);
        setMessages([]);
      }
      await loadThreads();
    } catch (err) {
      console.error("Failed to delete thread", err);
    }
  };

  const handleSend = useCallback(async () => {
    // Validation
    if (!inputVal.trim()) {
      return;
    }

    if (!selectedThreadId) {
      alert("Please select or create a conversation");
      return;
    }

    const currentThread = allThreads.find((t: any) => String(t.id) === String(selectedThreadId));
    if (!currentThread) {
      alert("This conversation was deleted");
      setSelectedThreadId(null);
      return;
    }



    const userMsg = inputVal;
    setInputVal("");
    setIsSending(true);
    setStreamingText("");

    // Optimistic UI
    setMessages(prev => [...prev, { role: "user", textContent: userMsg }]);

    // Abort previous stream
    cleanupStreamRef.current?.();

    const shouldAutoRename = currentThread && (currentThread.name === 'New chat' || !currentThread.name);

    const cleanup = assistantApi.streamMessage(
      selectedThreadId,
      userMsg,
      'hacker_assistant_agent',
      // onChunk
      (chunk: string) => {
        setStreamingText(prev => (prev ?? "") + chunk);
        scrollToBottom();
      },
      // onDone
      async () => {
        setStreamingText(null);
        setIsSending(false);
        cleanupStreamRef.current = null;

        // Auto-rename
        if (shouldAutoRename && streamingText) {
          const firstLine = (streamingText.split('\n').find((l) => l.trim().length > 0) || '').trim();
          const title = firstLine.slice(0, 60) || 'New chat';
          try {
            await assistantApi.updateThread(selectedThreadId, { name: title });
          } catch {
            // Non-fatal
          }
        }

        // Refresh threads and messages
        await loadThreads();
        await loadMessagesForThread(selectedThreadId);
      },
      // onError
      async (errMsg: string) => {
        console.error('[SSE error]', errMsg);
        setStreamingText(null);
        setIsSending(false);
        cleanupStreamRef.current = null;
        setMessages(prev => [...prev, {
          role: "assistant",
          textContent: `⚠️ Error: ${errMsg}`,
          isError: true,
        }]);
        await loadMessagesForThread(selectedThreadId);
      },
      // onStats
      () => {}
    );

    cleanupStreamRef.current = cleanup;
  }, [inputVal, selectedThreadId, allThreads, streamingText]);

  const getThreadDisplayName = (thread: any) => {
    let prefix = "";
    if (thread.is_hidden) prefix = "🔒 ";
    if (thread.assistant_id === 'hacker_assistant_agent') prefix += "🎖️ ";
    if (thread.name?.startsWith('subagent_') || thread.assistant_id === 'automation_agent') prefix += "🤖 ";
    return `${prefix}[ID: ${thread.id}] ${thread.name || 'Untitled'}`;
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (e.currentTarget.scrollTop === 0) {
      if (displayLimit < messages.length) {
        const container = e.currentTarget;
        const prevScrollHeight = container.scrollHeight;
        setDisplayLimit(prev => prev + 50);
        
        requestAnimationFrame(() => {
          if (container) {
            container.scrollTop = container.scrollHeight - prevScrollHeight;
          }
        });
      }
    }
  };

  const displayedMessages = messages.slice(-displayLimit);

  return (
    <div className="aicenter-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h3>CONVERSATIONS</h3>
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title="Toggle sidebar"
          >
            ✕
          </button>
        </div>

        <button 
          className="new-chat-btn"
          onClick={createNewThread}
          disabled={threadsLoading}
        >
          + New Chat
        </button>

        <div className="sidebar-filter">
          <input 
            type="text" 
            placeholder="🔍 Filter by Target ID..." 
            value={targetSearchId}
            onChange={(e) => setTargetSearchId(e.target.value)}
          />
          {targetSearchId && (
            <button className="clear-filter" onClick={() => setTargetSearchId("")}>✕</button>
          )}
        </div>

        {threadsLoading && (
          <div className="sidebar-loading">
            <span className="pulse">●</span> Loading...
          </div>
        )}

        {threadsError && (
          <div className="sidebar-error">
            ⚠️ {threadsError}
          </div>
        )}

        <div className="threads-list">
          {allThreads.length === 0 && !threadsLoading && (
            <div className="empty-state">No conversations yet</div>
          )}
          {allThreads.map((thread: any) => (
            <div 
              key={thread.id}
              className={`thread-item ${selectedThreadId === String(thread.id) ? 'active' : ''}`}
              onClick={() => setSelectedThreadId(String(thread.id))}
            >
              <div className="thread-name">
                {getThreadDisplayName(thread)}
              </div>
              {selectedThreadId === String(thread.id) && (
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteThread(String(thread.id));
                  }}
                  title="Delete conversation"
                >
                  🗑️
                </button>
              )}
            </div>
          ))}
        </div>

        {boundTargetId && (
          <div className="sidebar-footer">
            <div className="target-badge">
              <span>🎯 Target: {boundTargetId}</span>
              <button
                onClick={async () => {
                  if (!selectedThreadId) return;
                  await assistantApi.unbindTarget(selectedThreadId);
                  setBoundTargetId(null);
                }}
                title="Release target"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* Main Chat Area */}
      <main className="chat-main">
        {!sidebarOpen && (
          <button 
            className="sidebar-toggle-main"
            onClick={() => setSidebarOpen(true)}
            title="Open sidebar"
          >
            ☰
          </button>
        )}

        <div className="chat-container">
          {selectedThreadId ? (
            <>
              {/* Messages */}
              <div className="messages-area" onScroll={handleScroll}>
                {messages.length === 0 && !streamingText && (
                  <div className="empty-chat">
                    <div className="empty-icon">💬</div>
                    <div className="empty-text">Start a conversation</div>
                  </div>
                )}

                {displayLimit < messages.length && (
                  <div className="loading-older" style={{ textAlign: 'center', padding: '10px', color: '#666', fontSize: '0.9em' }}>
                    Loading older messages...
                  </div>
                )}

                {displayedMessages.map((msg: any) => (
                  <div key={msg.id || Math.random()} className={`message message-${msg.role}`}>
                    <div className="message-content">
                      {msg.role === 'user' ? (
                        <div className="user-text">{msg.textContent}</div>
                      ) : (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.textContent}
                        </ReactMarkdown>
                      )}
                    </div>
                  </div>
                ))}

                {streamingText && (
                  <div className="message message-assistant">
                    <div className="message-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamingText}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="input-area">
                <div className="input-wrapper">
                  <textarea
                    placeholder="Type your message... (Shift+Enter for new line)"
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    disabled={isSending}
                    rows={3}
                  />
                  <button
                    className="send-btn"
                    onClick={handleSend}
                    disabled={isSending || !inputVal.trim() || !selectedThreadId}
                    title={isSending ? "Sending..." : "Send message (Enter)"}
                  >
                    {isSending ? "..." : "Send"}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="no-thread">
              <div className="no-thread-icon">🤖</div>
              <div className="no-thread-text">
                {allThreads.length === 0 
                  ? "Create a new conversation to get started"
                  : "Select a conversation"}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AICenterPage;
