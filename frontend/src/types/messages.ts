/** LangChain-serialized message shape from GET /assistant/threads/{id}/messages/ */

export interface RawToolCall {
  id?: string;
  name: string;
  args?: Record<string, unknown>;
  type?: string;
}

export interface RawMessage {
  id?: string | number;
  type: 'human' | 'ai' | 'tool' | 'system' | 'generic' | 'function' | string;
  content?: string | Array<{ type?: string; text?: string; [key: string]: unknown }> | Record<string, unknown> | null;
  tool_calls?: RawToolCall[];
  tool_call_id?: string;
  name?: string;
  additional_kwargs?: Record<string, unknown>;
  response_metadata?: Record<string, unknown>;
}

export type MessageCategory =
  | 'user'
  | 'ai_response'
  | 'tool_call'
  | 'tool_result'
  | 'subagent_dispatch'
  | 'system';

/** Sub-agent tool names that should render as SubAgentContainerBlock */
export const SUBAGENT_TOOL_NAMES = new Set([
  'automation_agent',
  'spawn_recon_agent',
  'spawn_post_exploit_agent',
  'spawn_reporting_agent',
  'recon_agent',
  'post_exploit_agent',
  'reporting_agent',
]);

export interface DisplayMessage {
  id: string | number;
  role: 'user' | 'assistant' | 'tool' | 'system';
  category: MessageCategory;
  textContent: string;
  toolCalls?: RawToolCall[];
  toolCallId?: string;
  toolName?: string;
  assistantId?: string;
  isError?: boolean;
  raw?: RawMessage;
}

export function extractTextContent(content: RawMessage['content']): string {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .map((c) => {
        if (typeof c === 'string') return c;
        if (c && typeof c === 'object' && 'text' in c) return String(c.text ?? '');
        return JSON.stringify(c);
      })
      .join('\n');
  }
  if (content && typeof content === 'object') return JSON.stringify(content);
  return '';
}

export function hasTextContent(m: RawMessage): boolean {
  return extractTextContent(m.content).trim().length > 0;
}

export function categorizeMessage(m: RawMessage): MessageCategory {
  if (m.type === 'human') return 'user';
  if (m.type === 'tool') return 'tool_result';
  if (m.type === 'system') return 'system';
  const toolCalls = m.tool_calls ?? [];
  if (toolCalls.some((tc) => SUBAGENT_TOOL_NAMES.has(tc.name))) return 'subagent_dispatch';
  if (toolCalls.length > 0) return 'tool_call';
  if (m.type === 'ai' && hasTextContent(m)) return 'ai_response';
  return 'system';
}

export function parseRawMessages(msgArray: RawMessage[]): DisplayMessage[] {
  return msgArray.map((m, index) => {
    const category = categorizeMessage(m);
    let textContent = extractTextContent(m.content);
    if (!textContent.trim()) {
      if (m.tool_calls && m.tool_calls.length > 0) {
        textContent = `[Tool Call: ${m.tool_calls.map((tc) => tc.name).join(', ')}]`;
      } else if (m.type === 'tool') {
        textContent = '[Tool Execution Completed]';
      } else {
        textContent = '[Empty Message]';
      }
    }

    const role: DisplayMessage['role'] =
      category === 'user'
        ? 'user'
        : category === 'tool_result'
          ? 'tool'
          : category === 'system'
            ? 'system'
            : 'assistant';

    return {
      id: m.id ?? `msg-${index}`,
      role,
      category,
      textContent,
      toolCalls: m.tool_calls,
      toolCallId: m.tool_call_id,
      toolName: m.name || m.tool_calls?.[0]?.name,
      raw: m,
    };
  });
}

/** Group consecutive tool_call + tool_result messages for collapsible rendering */
export type MessageRenderItem =
  | { kind: 'message'; message: DisplayMessage }
  | { kind: 'tool_group'; calls: DisplayMessage[]; results: DisplayMessage[] }
  | { kind: 'subagent'; message: DisplayMessage };

export function groupMessagesForRender(messages: DisplayMessage[]): MessageRenderItem[] {
  const items: MessageRenderItem[] = [];
  let i = 0;
  while (i < messages.length) {
    const msg = messages[i];
    if (msg.category === 'subagent_dispatch') {
      items.push({ kind: 'subagent', message: msg });
      i += 1;
      continue;
    }
    if (msg.category === 'tool_call') {
      const calls: DisplayMessage[] = [];
      const results: DisplayMessage[] = [];
      while (i < messages.length && messages[i].category === 'tool_call') {
        calls.push(messages[i]);
        i += 1;
      }
      while (i < messages.length && messages[i].category === 'tool_result') {
        results.push(messages[i]);
        i += 1;
      }
      items.push({ kind: 'tool_group', calls, results });
      continue;
    }
    items.push({ kind: 'message', message: msg });
    i += 1;
  }
  return items;
}
