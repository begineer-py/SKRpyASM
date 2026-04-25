import React, { useState, useEffect, useRef } from 'react';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import { GET_LIVE_MISSIONS } from '../../queries';
import { assistantApi } from '../../services/assistantApi';
import './AICenter.css';

const AICenterPage: React.FC = () => {
  const { data, loading, error } = useHasuraSubscription(GET_LIVE_MISSIONS);

  // --- Chat State ---
  const [threads, setThreads] = useState<any[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [editingMsgId, setEditingMsgId] = useState<string | null>(null);
  const [editVal, setEditVal] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadThreads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadThreads = async () => {
    try {
      const res: any[] = await assistantApi.getThreads() as any[];
      setThreads(res);
      if (res.length > 0) {
        setThreadId(prev => {
          if (!prev || !res.find((t: any) => t.id === prev)) {
             switchThread(res[0].id);
             return res[0].id;
          }
          return prev;
        });
      } else {
        setThreadId(null);
        setMessages([{ role: "assistant", textContent: "目前沒有任何對話階段，請按「+ 新對話」建立一個新的戰略階段。" }]);
      }
    } catch (err) {
      console.error("Failed to load threads", err);
    }
  };

  const createNewThread = async () => {
    try {
      const res: any = await assistantApi.createThread();
      await loadThreads();
      switchThread(res.id);
    } catch (err) {
      console.error("Failed to create thread", err);
    }
  };

  const handleDeleteThread = async (id: string | null) => {
    if (!id) return;
    if (!window.confirm("確定要刪除這個對話階段嗎？")) return;
    try {
      await assistantApi.deleteThread(id);
      setThreadId(null);
      setMessages([]);
      await loadThreads();
    } catch (err) {
      console.error("Failed to delete thread", err);
    }
  };

  const switchThread = async (id: string) => {
    if (!id) return;
    setThreadId(prevId => {
      // If we are actually switching threads, clear the messages
      if (prevId !== id) {
        setMessages([]);
      }
      return id;
    });

    try {
      const allMsgsRaw: any[] = await assistantApi.getMessages(id) as any;
      const parsed = allMsgsRaw.map((m: any) => {
        let textContent = "";
        let role = m.type === "human" ? "user" : "assistant";
        let isToolLog = false;

        if (typeof m.content === "string") textContent = m.content;
        else if (Array.isArray(m.content)) {
            textContent = m.content.map((c: any) => c.text || JSON.stringify(c)).join("\n");
        }

        if (m.tool_calls && m.tool_calls.length > 0) {
          isToolLog = true;
          textContent = `⚙️ [命令調用] ${m.tool_calls[0].name}\n參數: ${JSON.stringify(m.tool_calls[0].args, null, 2)}`;
          // If the AI also replied with some textual thought before calling a tool, prepend it
          if (m.content && m.content.trim()) {
              textContent = `[思考: ${m.content}]\n\n${textContent}`;
          }
        } else if (m.type === "tool") {
          isToolLog = true;
          let truncContent = textContent;
          if (truncContent.length > 500) truncContent = truncContent.substring(0, 500) + '... (已截斷)';
          textContent = `✔️ [工具回傳] ${m.name || 'Tool'}\n狀態: 執行成功\n結果:\n${truncContent}`;
        }

        return { id: m.id, role, textContent, isToolLog };
      });
      
      setMessages([{ role: "assistant", textContent: "長官您好，C2 戰略階段已切換。請下達新指令。" }, ...parsed]);
    } catch (err) {
      console.error("Failed to load messages", err);
    }
  };

  const handleSend = async () => {
    if (!inputVal.trim() || !threadId) return;
    const userMsg = inputVal;
    setInputVal("");
    setIsSending(true);

    // Optimistic append
    setMessages(prev => [...prev, { role: "user", textContent: userMsg }]);

    try {
      await assistantApi.postMessage(threadId, userMsg);
      await switchThread(threadId);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: "assistant", textContent: "⚠️ 無法聯繫後端系統，請檢查伺服器或認證狀態。" }]);
    }
    setIsSending(false);
  };

  const saveAndResend = async (msg: any) => {
    if (!threadId || !msg.id) return;
    const newContent = editVal;
    setEditingMsgId(null);
    setEditVal("");
    setIsSending(true);

    try {
      // Find the index of the message we are editing
      const idx = messages.findIndex(m => m.id === msg.id);
      if (idx !== -1) {
        // Optimistically slice UI
        setMessages(messages.slice(0, idx));
        // Delete this message and all subsequent messages from backend to prevent fork duplication in standard thread
        const msgsToDelete = messages.slice(idx);
        for (const m of msgsToDelete) {
          if (m.id) {
            await assistantApi.deleteMessage(threadId, m.id).catch(err => console.warn(err));
          }
        }
      }
      
      // Send the modified message
      await assistantApi.postMessage(threadId, newContent);
      await switchThread(threadId);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: "assistant", textContent: "⚠️ 無法聯繫後端系統，請檢查伺服器或認證狀態。" }]);
    }
    setIsSending(false);
  };

  return (
    <div className="aicenter-container">
      {/* 
        ========================================
        Left Panel: Main Agent Chat 
        ========================================
      */}
      <div className="glass-panel chat-panel">
        <div className="panel-header">
          <h2>Main Agent 終端</h2>
          <span className="status-badge connected">● 連線中</span>
        </div>
        
        <div className="thread-controls" style={{ padding: '10px 20px', display: 'flex', gap: '10px', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <select 
            value={threadId || ""} 
            onChange={(e) => switchThread(e.target.value)}
            style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'rgba(0,0,0,0.5)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}
          >
            <option value="" disabled>-- 選擇對話階段 --</option>
            {threads.map((t: any) => {
              const d = new Date(t.updated_at || t.created_at);
              return <option key={t.id} value={t.id}>{t.name || '對話'} ({d.getMonth()+1}/{d.getDate()} {d.getHours().toString().padStart(2, '0')}:{d.getMinutes().toString().padStart(2, '0')})</option>;
            })}
          </select>
          <button 
            onClick={createNewThread} 
            className="btn-primary" 
            style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
            + 新對話
          </button>
          <button 
            onClick={() => handleDeleteThread(threadId)} 
            disabled={!threadId}
            style={{ padding: '6px 12px', fontSize: '0.85rem', background: '#e74c3c', color: 'white', border: 'none', borderRadius: '4px', cursor: threadId ? 'pointer' : 'not-allowed', opacity: threadId ? 1 : 0.5 }}>
            刪除
          </button>
        </div>

        <div className="chat-history">
          {messages.map((m, idx) => (
            <div className={`message ${m.role === 'user' ? 'user' : 'ai'} ${m.isToolLog ? 'tool-log' : ''}`} key={m.id || idx}>
              <div className="avatar">{m.role === 'user' ? 'You' : (m.isToolLog ? 'SYS' : 'AI')}</div>
              <div className="bubble" style={{ whiteSpace: "pre-wrap", position: "relative" }}>
                {editingMsgId === m.id && m.role === 'user' ? (
                  <div className="edit-area">
                    <textarea 
                      value={editVal} 
                      onChange={e => setEditVal(e.target.value)} 
                      rows={3} 
                      style={{ width: "100%", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--accent-cyan)", padding: "8px", borderRadius: "4px" }}
                    />
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px', justifyContent: 'flex-end' }}>
                      <button onClick={() => { setEditingMsgId(null); setEditVal(""); }} className="btn-secondary" style={{ padding: "4px 8px", fontSize: "0.8rem", background: "transparent", border: "1px solid white", color: "white", borderRadius: "4px", cursor: "pointer" }}>取消</button>
                      <button onClick={() => saveAndResend(m)} className="btn-primary" style={{ padding: "4px 8px", fontSize: "0.8rem", cursor: "pointer" }}>儲存並重新發送</button>
                    </div>
                  </div>
                ) : (
                  <>
                    {m.textContent}
                    {m.role === 'user' && m.id && (
                      <button 
                        onClick={() => { setEditingMsgId(m.id); setEditVal(m.textContent); }}
                        className="edit-btn"
                        style={{ position: "absolute", top: "-10px", right: "-10px", background: "rgba(0,0,0,0.6)", border: "1px solid rgba(255,255,255,0.2)", cursor: "pointer", color: "white", borderRadius: "50%", padding: "4px", display: "flex", alignItems: "center", justifyContent: "center", width: "24px", height: "24px", fontSize: "12px", opacity: 0.7 }}
                        title="編輯訊息"
                      >
                        ✏️
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          {isSending && (
            <div className="message ai">
               <div className="avatar">AI</div>
               <div className="bubble">
                 <span className="pulse">●</span> 正在思考並調度命令中...
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <textarea 
            placeholder="指派新任務給 Main Agent..." 
            rows={2}
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          ></textarea>
          <button className="btn-primary send-btn" onClick={handleSend} disabled={isSending || !threadId}>
            {isSending ? '分析中...' : '發送指令'}
          </button>
        </div>
      </div>

      {/* 
        ========================================
        Right Panel: Live Mission Control 
        ========================================
      */}
      <div className="glass-panel live-panel">
        <div className="panel-header">
          <h2>即時戰況監控 (Hasura Hook)</h2>
          <span className="status-badge active">● Live</span>
        </div>
        
        <div className="missions-container">
          {loading && <div style={{textAlign: "center", color: "var(--text-muted)", marginTop: "20px"}}>載入任務情報中...</div>}
          {error && <div style={{color: "var(--accent-danger)", padding: "10px"}}>GraphQL 錯誤: {error.message}</div>}
          
          {data?.core_overview?.map((overview: any) => (
            <div className="mission-card" key={overview.id}>
              <div className="mission-header">
                <h3>Target: {overview.core_target?.name || `Target ID: ${overview.target_id || '未知'}`} [Overview #{overview.id}]</h3>
                <span className={`mission-status ${overview.status.toLowerCase()}`}>
                  {overview.status}
                </span>
              </div>
              
              <ul className="step-list">
                {(!overview.core_steps || overview.core_steps.length === 0) && (
                  <span style={{color: "var(--text-muted)", fontSize: "0.85rem"}}>等待 AI 生成執行步驟...</span>
                )}
                {overview.core_steps?.map((step: any) => {
                  const isActive = step.status === "RUNNING";
                  const isCompleted = step.status === "COMPLETED";
                  const stepName = step.core_attackvectors?.[0]?.name || step.core_stepnote?.content || `自動化探索步驟 #${step.id}`;
                  
                  return (
                    <li className={`step ${isCompleted ? 'completed' : isActive ? 'active' : 'pending'}`} key={step.id}>
                      <span className={`step-icon ${isActive ? 'pulse' : ''}`}>
                        {isCompleted ? '✓' : isActive ? '⟳' : '○'}
                      </span>
                      <span className="step-name">
                        {stepName}
                        <br/>
                        <span style={{fontSize: "0.75rem", opacity: 0.6}}>Status: {step.status}</span>
                      </span>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AICenterPage;
