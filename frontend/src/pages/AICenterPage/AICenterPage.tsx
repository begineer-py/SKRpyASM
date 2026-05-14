import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import { GET_LIVE_MISSIONS, GET_RECENT_STEPS_UPDATES } from '../../queries';
import { assistantApi } from '../../services/assistantApi';
import { TelemetryPanel } from '../../components/TelemetryPanel';
import { StepsMainArea } from '../../components/StepsMainArea';
import './AICenter.css';

const AICenterPage: React.FC = () => {
  const { data } = useHasuraSubscription(GET_LIVE_MISSIONS);
  // 📍 P1 FIX: 訂閱實時 Step 更新，顯示 Automation 執行進度
  const { data: stepsData } = useHasuraSubscription(GET_RECENT_STEPS_UPDATES);

  // --- Chat State ---
  const [allThreads, setAllThreads] = useState<any[]>([]);
  const [selectedMainThreadId, setSelectedMainThreadId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"MAIN" | "AUTO">("MAIN");

  const [messages, setMessages] = useState<any[]>([]);
  const [inputVal, setInputVal] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamingText, setStreamingText] = useState<string | null>(null); // live streaming bubble
  const [editingMsgId, setEditingMsgId] = useState<string | null>(null);
  const [editVal, setEditVal] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cleanupStreamRef = useRef<(() => void) | null>(null); // abort SSE on unmount

  // Target binding
  const [boundTargetId, setBoundTargetId] = useState<number | null>(null);

  // Performance monitoring
  const [lastElapsedMs, setLastElapsedMs] = useState<number | null>(null);

  // P11: Right panel state
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);
  const [rightPanelWidth, setRightPanelWidth] = useState(280); // Sidebar width
  const [rightPanelDragging, setRightPanelDragging] = useState(false);

  const [leftWidth, setLeftWidth] = useState(500);
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseDown = () => setIsDragging(true);

  useEffect(() => {
    const handleMouseUp = () => setIsDragging(false);
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const newWidth = e.clientX - 20; 
        if (newWidth > 350 && newWidth < window.innerWidth - 10) {
          setLeftWidth(newWidth);
        }
      }
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    } else {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

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

  // When viewMode or selectedMainThreadId changes, reload messages
  useEffect(() => {
    if (selectedMainThreadId) {
        reloadMessagesForCurrentView(selectedMainThreadId, viewMode, allThreads);
    }
  }, [selectedMainThreadId, viewMode, allThreads]);

  // 📍 P1 FIX: 當 Automation Agent 運行時，定期輪詢新消息
  useEffect(() => {
    if (viewMode !== "AUTO" || !selectedMainThreadId) return;
    
    const subId = getSubThreadId(selectedMainThreadId, allThreads);
    if (!subId) return;

    // 每 2 秒檢查一次新消息
    const pollInterval = setInterval(async () => {
      try {
        const allMsgsRaw: any[] = await assistantApi.getMessages(subId);
        // 簡單比對：如果新消息數不同，更新
        if (allMsgsRaw.length !== messages.length) {
          const parsed = allMsgsRaw.map((m: any) => {
            let role = m.type === "human" ? "user" : "assistant";
            return {
              id: m.id,
              role: role,
              textContent: m.text?.content || "",
            };
          });
          setMessages(parsed);
        }
      } catch (err) {
        // 靜默失敗，不中斷輪詢
        console.debug("Auto-poll background messages failed (silent):", err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [viewMode, selectedMainThreadId, allThreads, messages.length]);

  const loadThreads = async () => {
    try {
      const res: any[] = await assistantApi.getThreads() as any[];
      setAllThreads(res);
      const mainThreads = res.filter((t: any) => !t.name?.startsWith('subagent_'));
      
      if (mainThreads.length > 0) {
        setSelectedMainThreadId(prev => {
          if (!prev || !mainThreads.find((t: any) => t.id === prev)) {
             const first = mainThreads[0];
             // sync bound target from first thread
             setBoundTargetId(first.bound_target_id ?? null);
             return first.id;
          }
          return prev;
        });
      } else {
        setSelectedMainThreadId(null);
        setBoundTargetId(null);
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
      setSelectedMainThreadId(res.id);
      setViewMode("MAIN");
    } catch (err) {
      console.error("Failed to create thread", err);
    }
  };

  const handleDeleteThread = async (id: string | null) => {
    if (!id) return;
    if (!window.confirm("確定要刪除這個對話階段嗎？")) return;
    try {
      await assistantApi.deleteThread(id);
      setSelectedMainThreadId(null);
      setMessages([]);
      await loadThreads();
    } catch (err) {
      console.error("Failed to delete thread", err);
    }
  };

  const getSubThreadId = (mainId: string, threads: any[]) => {
      const subName = `subagent_automation_agent_for_thread_${mainId}`;
      const sub = threads.find(t => t.name === subName);
      return sub ? sub.id : null;
  };

  const reloadMessagesForCurrentView = async (mainId: string, mode: "MAIN" | "AUTO", threads: any[]) => {
      let targetIdToLoad = mainId;
      if (mode === "AUTO") {
          const subId = getSubThreadId(mainId, threads);
          if (!subId) {
              setMessages([{ role: "assistant", textContent: "⚠️ 尚未啟動任何 Automation Agent 背景作業（該階段目前不存在探員記憶體）。"}]);
              return;
          }
          targetIdToLoad = subId;
      }

      try {
        const allMsgsRaw: any[] = await assistantApi.getMessages(targetIdToLoad) as any;
        const parsed = allMsgsRaw.map((m: any) => {
          let textContent = "";
          let role = m.type === "human" ? "user" : "assistant";
          let isToolLog = false;
          let isSystemReport = false;
          let isAgentDelegation = false;
          
          if (typeof m.content === "string") textContent = m.content;
          else if (Array.isArray(m.content)) {
              textContent = m.content.map((c: any) => c.text || JSON.stringify(c)).join("\n");
          }

          if (role === "user" && textContent.startsWith("[System Context:")) {
              role = "system_report";
              isSystemReport = true;
          }

          if (role === "user" && textContent.startsWith("[SYSTEM:")) {
              role = "system_report";
              isSystemReport = true;
          }

          // Normalize tool_calls: LangChain message_to_dict may store them at different paths
          const rawToolCalls = m.tool_calls?.length > 0 ? m.tool_calls 
              : m.additional_kwargs?.tool_calls?.length > 0 ? m.additional_kwargs.tool_calls 
              : null;

          if (rawToolCalls && rawToolCalls.length > 0) {
            isToolLog = true;
            const firstCall = rawToolCalls[0];
            // Handle both langchain format {name, args} and openai format {function: {name, arguments}}
            const toolName: string = firstCall.name || firstCall.function?.name || 'unknown_tool';
            let args: any;
            try {
                args = firstCall.args ?? (firstCall.function?.arguments ? JSON.parse(firstCall.function.arguments) : {});
            } catch { args = firstCall.function?.arguments || {}; }
            
            if (toolName === "automation_agent") {
                isAgentDelegation = true;
                textContent = `🚀 [AGENT DELEGATION] 將指揮權移交給 執行探員 (Automation Agent) 處理\n\n【傳達任務指令】:\n${args.message || JSON.stringify(args, null, 2)}`;
                if (m.content && m.content.trim()) {
                    textContent = `[總指揮官計畫: ${m.content}]\n\n${textContent}`;
                }
            } else {
                textContent = `⚙️ [命令調用] ${toolName}\n參數: ${JSON.stringify(args, null, 2)}`;
                if (m.content && m.content.trim()) {
                    textContent = `[思考: ${m.content}]\n\n${textContent}`;
                }
            }
          } else if (m.type === "tool") {
            isToolLog = true;
            let truncContent = textContent;
            if (truncContent.length > 500) truncContent = truncContent.substring(0, 500) + '... (已截斷)';
            textContent = `✔️ [工具回傳] ${m.name || 'Tool'}\n狀態: 執行成功\n結果:\n${truncContent}`;
          }

          return { id: m.id, role, textContent, isToolLog, isSystemReport, isAgentDelegation };
        });
        
        let welcomeText = mode === "MAIN" 
          ? "長官您好，C2 戰略階段已切換。請下達新指令。"
          : "【LAYER 3 探員視角】您正在連線 Automation Agent 的子系統內存。正在監視底層推理...";
        setMessages([{ role: "assistant", textContent: welcomeText }, ...parsed]);
      } catch (err) {
        console.error("Failed to load messages", err);
      }
  };

  // Cleanup SSE if component unmounts mid-stream
  useEffect(() => {
    return () => { cleanupStreamRef.current?.(); };
  }, []);

  const handleSend = useCallback(async () => {
    if (!inputVal.trim() || !selectedMainThreadId) return;
    const userMsg = inputVal;
    setInputVal("");
    setIsSending(true);
    setStreamingText(""); // open streaming bubble

    const actualThreadId = viewMode === "MAIN"
      ? selectedMainThreadId
      : getSubThreadId(selectedMainThreadId, allThreads);

    // Optimistic: show user message immediately
    setMessages(prev => [...prev, { role: "user", textContent: userMsg }]);

    if (!actualThreadId) {
      setStreamingText(null);
      setIsSending(false);
      return;
    }

    // Abort any previous stream
    cleanupStreamRef.current?.();

    const cleanup = assistantApi.streamMessage(
      actualThreadId,
      userMsg,
      'hacker_assistant_agent',
      // onChunk — append each token to the live bubble
      (chunk: string) => {
        setStreamingText(prev => (prev ?? "") + chunk);
        scrollToBottom();
      },
      // onDone — stream finished; reload from DB to get authoritative messages with IDs
      async () => {
        setStreamingText(null);
        setIsSending(false);
        cleanupStreamRef.current = null;
        // Refresh thread to pick up any binding changes made by the agent
        const threads = await assistantApi.getThreads() as any[];
        setAllThreads(threads);
        const t = threads.find((th: any) => th.id == selectedMainThreadId);
        if (t) setBoundTargetId(t.bound_target_id ?? null);
        await reloadMessagesForCurrentView(selectedMainThreadId, viewMode, threads);
      },
      // onError — keep existing messages, append error notice, then reload DB messages
      async (errMsg: string) => {
        console.error('[SSE error]', errMsg);
        setStreamingText(null);
        setIsSending(false);
        cleanupStreamRef.current = null;
        // Add an error bubble WITHOUT clearing what's already there
        setMessages(prev => [...prev, {
          role: "assistant",
          textContent: `⚠️ **執行中發生錯誤** (已保留已完成的步驟記錄)\n\n\`${errMsg}\``,
          isError: true,
        }]);
        // Reload from DB to restore any tool-call messages that were already saved
        await reloadMessagesForCurrentView(selectedMainThreadId, viewMode, allThreads);
      },
      // onStats — record LLM response time
      (elapsedMs: number) => {
        setLastElapsedMs(elapsedMs);
      },
    );
    cleanupStreamRef.current = cleanup;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputVal, selectedMainThreadId, viewMode, allThreads]);

  const saveAndResend = async (msg: any) => {
    if (!selectedMainThreadId || !msg.id) return;
    const actualThreadId = viewMode === "MAIN" ? selectedMainThreadId : getSubThreadId(selectedMainThreadId, allThreads);
    if (!actualThreadId) return;

    const newContent = editVal;
    setEditingMsgId(null);
    setEditVal("");
    setIsSending(true);

    try {
      const idx = messages.findIndex(m => m.id === msg.id);
      if (idx !== -1) {
        setMessages(messages.slice(0, idx));
        const msgsToDelete = messages.slice(idx);
        for (const m of msgsToDelete) {
          if (m.id) {
            await assistantApi.deleteMessage(actualThreadId, m.id).catch(err => console.warn(err));
          }
        }
      }
      
      await assistantApi.postMessage(actualThreadId, newContent);
      await reloadMessagesForCurrentView(selectedMainThreadId, viewMode, allThreads);
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
      <div className="glass-panel chat-panel" style={{ width: leftWidth }}>
        <div className="panel-header">
          <h2>SYS_TERMINAL_01</h2>
          <span className="status-badge connected">ONLINE</span>
        </div>
        
        <div className="thread-controls" style={{ padding: '10px 20px', display: 'flex', gap: '10px', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <select 
            value={selectedMainThreadId || ""} 
            onChange={(e) => {
              const selected = allThreads.find((t: any) => t.id == e.target.value);
              setSelectedMainThreadId(e.target.value);
              setBoundTargetId(selected?.bound_target_id ?? null);
            }}
            style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'rgba(0,0,0,0.5)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}
          >
            <option value="" disabled>-- 選擇對話階段 --</option>
            {allThreads.filter((t: any) => !t.name?.startsWith('subagent_')).map((t: any) => {
              const d = new Date(t.updated_at || t.created_at);
              return <option key={t.id} value={t.id}>{t.name || '對話'} ({d.getMonth()+1}/{d.getDate()} {d.getHours().toString().padStart(2, '0')}:{d.getMinutes().toString().padStart(2, '0')})</option>;
            })}
          </select>
          <button 
            onClick={createNewThread} 
            className="btn-primary" 
            style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
            [NEW_SESSION]
          </button>
          <button 
            onClick={() => handleDeleteThread(selectedMainThreadId)} 
            disabled={!selectedMainThreadId}
            style={{ padding: '6px 12px', fontSize: '0.85rem', background: '#0f172a', color: '#ef4444', border: '1px solid #ef4444', cursor: selectedMainThreadId ? 'pointer' : 'not-allowed', opacity: selectedMainThreadId ? 1 : 0.5 }}>
            [KILL_PROCESS]
          </button>
        </div>

        {/* Bound Target Badge */}
        <div style={{ padding: '6px 20px', background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8rem', fontFamily: 'monospace' }}>
          {boundTargetId ? (
            <>
              <span style={{ color: '#10B981', fontWeight: 700 }}>🎯 TARGET LOCKED:</span>
              <span style={{ color: '#34d399', background: 'rgba(16,185,129,0.1)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(16,185,129,0.3)' }}>
                ID: {boundTargetId}
              </span>
              <button
                onClick={async () => {
                  if (!selectedMainThreadId) return;
                  await assistantApi.unbindTarget(selectedMainThreadId);
                  setBoundTargetId(null);
                }}
                style={{ marginLeft: 'auto', padding: '2px 8px', background: 'transparent', color: '#ef4444', border: '1px solid #ef4444', borderRadius: '4px', cursor: 'pointer', fontSize: '0.75rem' }}
              >
                [RELEASE]
              </button>
            </>
          ) : (
            <span style={{ color: '#4b5563', fontStyle: 'italic' }}>🔓 NO TARGET BOUND — Tell the agent: "bind to target [ID]"</span>
          )}
        </div>

        {/* View Mode Toggle */}
        <div style={{ display: 'flex', background: '#0f172a', borderBottom: '1px solid #1e293b' }}>
            <button 
                onClick={() => setViewMode("MAIN")}
                style={{ flex: 1, padding: '8px 0', cursor: 'pointer', background: viewMode === 'MAIN' ? 'rgba(34, 197, 94, 0.1)' : 'transparent', border: 'none', borderBottom: viewMode === 'MAIN' ? '2px solid #22c55e' : '2px solid transparent', color: viewMode === 'MAIN' ? '#22c55e' : '#94a3b8', fontWeight: viewMode === 'MAIN' ? 700 : 400, fontFamily: 'inherit' }}>
                &gt; HACKER ASSISTANT (主控台)
            </button>
            <button 
                onClick={() => setViewMode("AUTO")}
                style={{ flex: 1, padding: '8px 0', cursor: 'pointer', background: viewMode === 'AUTO' ? 'rgba(236, 72, 153, 0.1)' : 'transparent', border: 'none', borderBottom: viewMode === 'AUTO' ? '2px solid #ec4899' : '2px solid transparent', color: viewMode === 'AUTO' ? '#ec4899' : '#94a3b8', fontWeight: viewMode === 'AUTO' ? 700 : 400, fontFamily: 'inherit' }}>
                &gt; AUTOMATION AGENT (執行視角)
            </button>
        </div>

        <div className="chat-history">
          {messages.length > 50 && (
            <div className="system-report" style={{ textAlign: 'center', opacity: 0.5, fontStyle: 'italic', marginBottom: '10px' }}>
              ...已隱藏上方 {messages.length - 50} 條較舊的對話紀錄以維持效能...
            </div>
          )}
          {messages.slice(-50).map((m, idx) => (
            <div className={`message ${m.role === 'user' ? 'user' : (m.role === 'system_report' ? 'system-report ai' : 'ai')} ${m.isToolLog ? 'tool-log' : ''} ${m.isAgentDelegation ? 'agent-delegation' : ''}`} key={m.id || idx}>
              <div className="terminal-prefix">
                {m.role === 'user' ? 'root@c2:~#' : (m.role === 'system_report' ? '[L3_AUTOMATION]' : (m.isAgentDelegation ? '[L2_DIRECTIVE]' : (m.isToolLog ? '[sys_kernel]' : '[agent_out]')))}
              </div>
              <div className="terminal-block">
                {editingMsgId === m.id && m.role === 'user' ? (
                  <div className="edit-area">
                    <textarea 
                      value={editVal} 
                      onChange={e => setEditVal(e.target.value)} 
                      rows={3} 
                      style={{ width: "100%", padding: "8px" }}
                    />
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px', justifyContent: 'flex-end' }}>
                      <button onClick={() => { setEditingMsgId(null); setEditVal(""); }} className="btn-secondary" style={{ padding: "4px 8px", fontSize: "0.8rem", background: "transparent", cursor: "pointer" }}>[CANCEL]</button>
                      <button onClick={() => saveAndResend(m)} className="btn-primary" style={{ padding: "4px 8px", fontSize: "0.8rem" }}>[RESEND_CMD]</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="markdown-body">
                      {m.role === 'user' ? (
                        m.textContent 
                      ) : (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {m.textContent}
                        </ReactMarkdown>
                      )}
                    </div>
                    {m.role === 'user' && m.id && (
                      <button 
                        onClick={() => { setEditingMsgId(m.id); setEditVal(m.textContent); }}
                        className="edit-btn"
                        title="Modify Command"
                      >
                        [EDIT]
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          {/* Live streaming bubble — shows tokens as they arrive */}
          {streamingText !== null && (
            <div className="message ai">
              <div className="terminal-prefix">[agent_out]</div>
              <div className="terminal-block">
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingText || ""}
                  </ReactMarkdown>
                </div>
                <span className="pulse" style={{ marginLeft: '4px' }}>▌</span>
              </div>
            </div>
          )}
          {/* Fallback spinner when stream hasn't started yet */}
          {isSending && streamingText === null && (
            <div className="message ai">
               <div className="terminal-prefix">[agent_out]</div>
               <div className="terminal-block">
                 <span className="pulse">_</span> CONNECTING_TO_AGENT...
               </div>
            </div>
          )}
           <div ref={messagesEndRef} />
         </div>

         {/* 📍 P1 FIX: 實時 Step 執行進度提示 */}
         {stepsData?.core_overview && stepsData.core_overview.length > 0 && (
           <div style={{
             padding: '10px 16px',
             background: 'rgba(34, 197, 94, 0.05)',
             borderTop: '1px dashed #22c55e',
             fontSize: '0.75rem',
             fontFamily: 'monospace',
             maxHeight: '80px',
             overflowY: 'auto'
           }}>
             <div style={{ color: '#22c55e', fontWeight: 700, marginBottom: '4px' }}>📍 REAL-TIME STEP UPDATES:</div>
             {stepsData.core_overview.slice(0, 2).map((overview: any) => {
               const recentSteps = (overview.core_steps || []).slice(0, 5);
               const runningSteps = recentSteps.filter((s: any) => s.status === 'RUNNING').length;
               const completedSteps = recentSteps.filter((s: any) => s.status === 'COMPLETED').length;
               const failedSteps = recentSteps.filter((s: any) => s.status === 'FAILED').length;
               
               return (
                 <div key={overview.id} style={{ marginBottom: '6px', color: '#94a3b8' }}>
                   <span style={{ color: overview.status === 'EXECUTING' ? '#fbbf24' : '#22c55e' }}>
                     {overview.core_target?.name || `Target#${overview.id}`}:
                   </span>
                   {' '}
                   {runningSteps > 0 && <span style={{ color: '#fbbf24' }}>🔄 {runningSteps} running</span>}
                   {completedSteps > 0 && <span style={{ color: '#22c55e', marginLeft: '6px' }}>✓ {completedSteps} done</span>}
                   {failedSteps > 0 && <span style={{ color: '#ef4444', marginLeft: '6px' }}>✗ {failedSteps} failed</span>}
                 </div>
               );
             })}
           </div>
         )}

         <div className="chat-input-area">
          <textarea 
            placeholder={viewMode === "MAIN" ? "ENTER COMMAND..." : "⚠️ [唯讀視角] 這邊可以寫下備註給 Automation Agent 注意，但建議切換回 MAIN 視角下達戰略。"} 
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
          <button className="btn-primary send-btn" onClick={handleSend} disabled={isSending || !selectedMainThreadId || (viewMode === "AUTO" && !getSubThreadId(selectedMainThreadId, allThreads))}>
            {isSending ? '[EXECUTING...]' : '[EXECUTE]'}
          </button>
        </div>
      </div>

      {/* --- Resizer Handle --- */}
      <div 
        className={`resizer ${isDragging ? 'dragging' : ''}`} 
        onMouseDown={handleMouseDown} 
        title="拖曳以調整寬度"
      />

      {/* 
        ========================================
        Right Panel (P11): Sidebar + Main Layout
        ========================================
      */}
      <div className="glass-panel live-panel" style={{ display: 'flex' }}>
        {/* Telemetry Sidebar */}
        <div style={{ width: `${rightPanelWidth}px`, minWidth: '200px', maxWidth: '400px' }}>
          <TelemetryPanel
            lastElapsedMs={lastElapsedMs}
            steps={data?.core_overview?.flatMap((ov: any) => ov.core_steps || []) || []}
            boundTargetId={boundTargetId}
            viewMode={viewMode}
            hasData={messages.length > 0}
          />
        </div>

        {/* Resizer for sidebar */}
        <div
          style={{
            width: '4px',
            cursor: 'col-resize',
            background: '#1e293b',
            transition: rightPanelDragging ? 'none' : 'all 0.2s ease',
            flexShrink: 0,
            userSelect: 'none',
          }}
          onMouseDown={(e) => {
            e.preventDefault();
            setRightPanelDragging(true);
          }}
          onMouseUp={() => setRightPanelDragging(false)}
          title="拖曳以調整側邊欄寬度"
        />

        {/* Steps Main Area */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <StepsMainArea
            selectedStepId={selectedStepId}
            steps={data?.core_overview?.flatMap((ov: any) => ov.core_steps || []) || []}
            showLogs={true}
            onStepSelect={setSelectedStepId}
          />
        </div>
      </div>

      {/* Sidebar resize handler */}
      {rightPanelDragging && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 999,
            cursor: 'col-resize',
          }}
          onMouseMove={(e) => {
            const newWidth = e.clientX - (window.innerWidth - window.innerWidth + 20); // Approximate position
            if (newWidth > 200 && newWidth < 400) {
              setRightPanelWidth(newWidth);
            }
          }}
          onMouseUp={() => setRightPanelDragging(false)}
          onMouseLeave={() => setRightPanelDragging(false)}
        />
      )}
    </div>
  );
};

export default AICenterPage;
