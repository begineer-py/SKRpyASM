import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { skillApi } from '../../../services/skillApi';
import type { SkillTestResult, SkillTemplate } from '../../../services/skillApi';

interface Props {
  skillId: number | null;
}

function generateStubFromSchema(skill: SkillTemplate | null): string {
  if (!skill || !skill.input_schema) return '{\n  \n}';
  const schema = skill.input_schema as Record<string, any>;
  const props = schema?.properties || {};
  const required: string[] = schema?.required || [];
  if (Object.keys(props).length === 0) return '{\n  \n}';
  const lines: string[] = ['{'];
  for (const [key, def] of Object.entries(props)) {
    const type = (def as any)?.type || 'string';
    const isRequired = required.includes(key);
    const desc = (def as any)?.description ? ` // ${(def as any).description}` : '';
    let sample = '';
    if (type === 'string') sample = def && (def as any).pattern ? '"https://example.com"' : '""';
    else if (type === 'integer' || type === 'number') sample = '0';
    else if (type === 'boolean') sample = 'false';
    else if (type === 'array') sample = '[]';
    else if (type === 'object') sample = '{}';
    const comment = isRequired ? ' // required' : ' // optional';
    lines.push(`  "${key}": ${sample}${comment}${desc}`);
  }
  lines.push('}');
  return lines.join('\n');
}

const VERDICT_EXPLANATION: Record<string, string> = {
  PASSED: 'Script executed successfully and output matched the schema',
  FAILED: 'Script crashed or output didn\'t match the output schema',
  INCONCLUSIVE: 'Script ran but the LLM couldn\'t determine if output is correct',
};

const VERDICT_COLOR: Record<string, string> = {
  PASSED: '#22C55E',
  FAILED: '#ef4444',
  INCONCLUSIVE: '#a78bfa',
};

function formatDuration(ms: number | null): string {
  if (ms === null || ms === undefined) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function TestTab({ skillId }: Props) {
  const [testInput, setTestInput] = useState<string>('{\n  \n}');
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<SkillTestResult | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [showRawOutput, setShowRawOutput] = useState(false);
  const [showAgentNotes, setShowAgentNotes] = useState(false);

  useEffect(() => {
    if (!skillId) return;
    skillApi.get(skillId).then(skill => {
      setTestInput(generateStubFromSchema(skill));
    }).catch(() => {});
  }, [skillId]);

  const handleTest = async () => {
    if (!skillId) return;
    setParseError(null);
    setResult(null);

    let payload: { test_input: Record<string, unknown> | null };

    const trimmed = testInput.trim();
    if (trimmed === '' || trimmed === '{}') {
      payload = { test_input: null };
    } else {
      try {
        const parsed = JSON.parse(trimmed);
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          setParseError('Invalid JSON: test input must be a JSON object');
          return;
        }
        payload = { test_input: parsed as Record<string, unknown> };
      } catch {
        setParseError('Invalid JSON: could not parse test input');
        return;
      }
    }

    setTesting(true);
    try {
      const res = await skillApi.test(skillId, payload);
      setResult(res);
    } catch (e: any) {
      setResult({
        ok: false,
        verification_id: null,
        verdict: null,
        confidence: null,
        error: e?.message || 'Test request failed',
        exit_code: null,
        duration_ms: null,
        raw_output: null,
        agent_notes: null,
      });
    } finally {
      setTesting(false);
    }
  };

  if (!skillId) {
    return (
      <div className="test-tab">
        <div
          style={{
            padding: '16px 20px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 6,
            color: '#fca5a5',
            fontSize: 14,
          }}
        >
          ⚠ Save the skill first before testing.
        </div>
      </div>
    );
  }

  return (
    <div className="test-tab">
      {/* Info banner */}
      <div
        style={{
          padding: '14px 16px',
          marginBottom: 16,
          background: 'rgba(167, 139, 250, 0.06)',
          border: '1px solid rgba(167, 139, 250, 0.22)',
          borderRadius: 6,
          color: '#cbd5e1',
          fontSize: 12.5,
          lineHeight: 1.6,
        }}
      >
        <div style={{ color: '#a78bfa', fontWeight: 600, marginBottom: 6 }}>
          ℹ How testing works
        </div>
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          <li>
            The fields below are auto-filled from your <strong>input schema</strong>. Fill in real
            values (e.g. <code style={{ color: '#22C55E' }}>{"\"https://target.com\""}</code>).
          </li>
          <li>
            These values are passed <strong>directly</strong> to the script as{' '}
            <code style={{ color: '#22C55E' }}>inputs.field_name</code>.
          </li>
          <li>
            If you clear everything to <code style={{ color: '#a78bfa' }}>{'{}'}</code>, the AI
            auto-generates test input from your schema.
          </li>
          <li>
            The script runs in the <code style={{ color: '#22C55E' }}>c2_kali_sandbox</code> Docker
            container — ensure it's running.
          </li>
          <li>An LLM evaluates the output against your output schema to produce a verdict.</li>
        </ul>
      </div>

      <div>
        <div className="test-input-label">Test Input Example (JSON)</div>
        <div className="test-editor-wrapper" style={{ height: 200 }}>
          <Editor
            height="100%"
            language="json"
            value={testInput}
            onChange={val => setTestInput(val || '')}
            theme="vs-dark"
            options={{
              fontSize: 12,
              fontFamily: "'JetBrains Mono', monospace",
              minimap: { enabled: false },
              lineNumbers: 'off',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
            }}
          />
        </div>
        {parseError && (
          <div
            style={{
              marginTop: 8,
              padding: '8px 12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 4,
              color: '#fca5a5',
              fontSize: 12.5,
            }}
          >
            {parseError}
          </div>
        )}
      </div>

      <button className="test-run-btn" onClick={handleTest} disabled={testing || !skillId}>
        {testing ? '⏳ RUNNING...' : '▶ TEST RUN'}
      </button>

      {result && (
        <div className={`test-result-box ${result.ok ? 'ok' : 'fail'}`}>
          {/* Error block (priority) */}
          {result.error && (
            <div
              style={{
                padding: '10px 12px',
                marginBottom: 12,
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                borderRadius: 4,
                color: '#fca5a5',
                fontSize: 12.5,
              }}
            >
              <strong>Error:</strong> {result.error}
            </div>
          )}

          {/* Verdict */}
          {result.verdict && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span
                style={{
                  display: 'inline-block',
                  padding: '3px 10px',
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: 0.5,
                  color: '#0b0f1a',
                  background: VERDICT_COLOR[result.verdict] || '#667085',
                }}
              >
                {result.verdict}
              </span>
              <span style={{ color: '#667085', fontSize: 12.5 }}>
                {VERDICT_EXPLANATION[result.verdict] || ''}
              </span>
            </div>
          )}

          {/* Metrics row */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 18, marginTop: 8, fontSize: 12.5 }}>
            {result.confidence !== null && result.confidence !== undefined && (
              <div>
                <span style={{ color: '#667085' }}>Confidence: </span>
                <span style={{ color: '#e2e8f0', fontWeight: 600 }}>
                  {Math.round(result.confidence)}%
                </span>
              </div>
            )}
            <div>
              <span style={{ color: '#667085' }}>Duration: </span>
              <span style={{ color: '#e2e8f0' }}>{formatDuration(result.duration_ms)}</span>
            </div>
            <div>
              <span style={{ color: '#667085' }}>Exit code: </span>
              <span style={{ color: '#e2e8f0' }}>
                {result.exit_code !== null && result.exit_code !== undefined
                  ? result.exit_code
                  : '-'}
              </span>
            </div>
          </div>

          {/* Agent notes (collapsible) */}
          {result.agent_notes && (
            <div style={{ marginTop: 12 }}>
              <button
                onClick={() => setShowAgentNotes(s => !s)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(148,163,184,0.14)',
                  color: '#a78bfa',
                  padding: '4px 10px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontSize: 12,
                }}
              >
                {showAgentNotes ? '▼' : '▶'} LLM Evaluation Notes
              </button>
              {showAgentNotes && (
                <div
                  style={{
                    marginTop: 8,
                    padding: '10px 12px',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid rgba(148,163,184,0.14)',
                    borderRadius: 4,
                    color: '#667085',
                    fontSize: 12.5,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {result.agent_notes}
                </div>
              )}
            </div>
          )}

          {/* Raw output (collapsible) */}
          {result.raw_output && (
            <div style={{ marginTop: 12 }}>
              <button
                onClick={() => setShowRawOutput(s => !s)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(148,163,184,0.14)',
                  color: '#22C55E',
                  padding: '4px 10px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontSize: 12,
                }}
              >
                {showRawOutput ? '▼' : '▶'} Raw Output
              </button>
              {showRawOutput && (
                <pre
                  style={{
                    marginTop: 8,
                    padding: '10px 12px',
                    background: 'rgba(0,0,0,0.45)',
                    border: '1px solid rgba(148,163,184,0.14)',
                    borderRadius: 4,
                    color: '#cbd5e1',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 11.5,
                    maxHeight: 320,
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {result.raw_output}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
