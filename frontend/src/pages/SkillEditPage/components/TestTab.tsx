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
        <div className="px-5 py-4 bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.3)] rounded-md text-[#fca5a5] text-sm">
          ⚠ Save the skill first before testing.
        </div>
      </div>
    );
  }

  return (
    <div className="test-tab">
      {/* Info banner */}
      <div className="py-[14px] px-4 mb-4 bg-[rgba(167,139,250,0.06)] border border-[rgba(167,139,250,0.22)] rounded-md text-[#cbd5e1] text-[12.5px] leading-[1.6]">
        <div className="text-[#a78bfa] font-semibold mb-[6px]">
          ℹ How testing works
        </div>
        <ul className="m-0 pl-[18px]">
          <li>
            The fields below are auto-filled from your <strong>input schema</strong>. Fill in real
            values (e.g. <code className="text-green">{'"https://target.com"'}</code>).
          </li>
          <li>
            These values are passed <strong>directly</strong> to the script as{' '}
            <code className="text-green">inputs.field_name</code>.
          </li>
          <li>
            If you clear everything to <code className="text-[#a78bfa]">{'{}'}</code>, the AI
            auto-generates test input from your schema.
          </li>
          <li>
            The script runs in the <code className="text-green">c2_kali_sandbox</code> Docker
            container — ensure it's running.
          </li>
          <li>An LLM evaluates the output against your output schema to produce a verdict.</li>
        </ul>
      </div>

      <div>
        <div className="test-input-label">Test Input Example (JSON)</div>
        <div className="test-editor-wrapper h-[200px]">
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
          <div className="mt-2 px-3 py-2 bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.3)] rounded text-[#fca5a5] text-[12.5px]">
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
            <div className="px-3 py-[10px] mb-3 bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.35)] rounded text-[#fca5a5] text-[12.5px]">
              <strong>Error:</strong> {result.error}
            </div>
          )}

          {/* Verdict */}
          {result.verdict && (
            <div className="flex items-center gap-[10px] mb-2">
              <span
                className="inline-block px-[10px] py-[3px] rounded text-[12px] font-bold tracking-[0.5px] text-[#0b0f1a]"
                style={{ background: VERDICT_COLOR[result.verdict] || '#667085' }}
              >
                {result.verdict}
              </span>
              <span className="text-text-muted text-[12.5px]">
                {VERDICT_EXPLANATION[result.verdict] || ''}
              </span>
            </div>
          )}

          {/* Metrics row */}
          <div className="flex flex-wrap gap-[18px] mt-2 text-[12.5px]">
            {result.confidence !== null && result.confidence !== undefined && (
              <div>
                <span className="text-text-muted">Confidence: </span>
                <span className="text-[#e2e8f0] font-semibold">
                  {Math.round(result.confidence)}%
                </span>
              </div>
            )}
            <div>
              <span className="text-text-muted">Duration: </span>
              <span className="text-[#e2e8f0]">{formatDuration(result.duration_ms)}</span>
            </div>
            <div>
              <span className="text-text-muted">Exit code: </span>
              <span className="text-[#e2e8f0]">
                {result.exit_code !== null && result.exit_code !== undefined
                  ? result.exit_code
                  : '-'}
              </span>
            </div>
          </div>

          {/* Agent notes (collapsible) */}
          {result.agent_notes && (
            <div className="mt-3">
              <button
                onClick={() => setShowAgentNotes(s => !s)}
                className="bg-transparent border border-border-subtle text-[#a78bfa] px-[10px] py-[4px] rounded cursor-pointer text-[12px]"
              >
                {showAgentNotes ? '▼' : '▶'} LLM Evaluation Notes
              </button>
              {showAgentNotes && (
                <div className="mt-2 px-3 py-[10px] bg-[rgba(0,0,0,0.3)] border border-border-subtle rounded text-text-muted text-[12.5px] whitespace-pre-wrap">
                  {result.agent_notes}
                </div>
              )}
            </div>
          )}

          {/* Raw output (collapsible) */}
          {result.raw_output && (
            <div className="mt-3">
              <button
                onClick={() => setShowRawOutput(s => !s)}
                className="bg-transparent border border-border-subtle text-green px-[10px] py-[4px] rounded cursor-pointer text-[12px]"
              >
                {showRawOutput ? '▼' : '▶'} Raw Output
              </button>
              {showRawOutput && (
                <pre className="mt-2 px-3 py-[10px] bg-[rgba(0,0,0,0.45)] border border-border-subtle rounded text-[#cbd5e1] font-mono text-[11.5px] max-h-[320px] overflow-auto whitespace-pre-wrap break-words">
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
