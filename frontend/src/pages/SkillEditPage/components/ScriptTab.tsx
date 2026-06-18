import { useRef, useCallback } from 'react';
import type { ChangeEvent } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import { exportScript, exportSkillJson, readTextFile, extractScriptBody, detectLanguage } from '../../../utils/skillFileIo';
import type { SkillTemplate } from '../../../services/skillApi';
import { SKILL_TEMPLATES } from '../skillTemplates';
import type { SkillTemplateDef } from '../skillTemplates';

interface Props {
  scriptBody: string;
  language: string;
  skillForExport?: SkillTemplate | null;
  onScriptBodyChange: (val: string) => void;
  onLanguageChange?: (lang: string) => void;
  /** For create mode — imported file can set language */
  onNameDetect?: (name: string) => void;
  /** Applies a full template (scriptBody, language, schemas) — parent handles persistence */
  onApplyTemplate: (template: SkillTemplateDef) => void;
}

export default function ScriptTab({
  scriptBody,
  language,
  skillForExport,
  onScriptBodyChange,
  onLanguageChange,
  onNameDetect,
  onApplyTemplate,
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const monacoRef = useRef<Parameters<OnMount>[0] | null>(null);

  const handleMount: OnMount = useCallback((editor) => {
    monacoRef.current = editor;
  }, []);

  const handleImportScript = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await readTextFile(file);
      const scriptBody = extractScriptBody(text);
      onScriptBodyChange(scriptBody);
      const lang = detectLanguage(file.name);
      if (onLanguageChange) onLanguageChange(lang);
      if (onNameDetect) {
        const name = file.name.replace(/\.(py|sh)$/i, '');
        if (/^[a-z0-9]+(-[a-z0-9]+)*$/.test(name)) onNameDetect(name);
      }
    } catch (err: any) {
      alert(`Import error: ${err.message}`);
    }
    e.target.value = '';
  };

  const handleImportJson = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await readTextFile(file);
      const data = JSON.parse(text);
      if (data.script_body !== undefined) onScriptBodyChange(data.script_body);
      if (data.language && onLanguageChange) onLanguageChange(data.language);
    } catch (err: any) {
      alert(`Import error: ${err.message}`);
    }
    e.target.value = '';
  };

  const handleExportScript = () => {
    if (!skillForExport) {
      const ext = language === 'bash' ? 'sh' : 'py';
      const content = scriptBody;
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `script.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    exportScript(skillForExport);
  };

  const handleExportJson = () => {
    if (skillForExport) exportSkillJson(skillForExport);
  };

  const isBash = language === 'bash';

  return (
    <div className="script-tab">
      <input
        ref={fileInputRef}
        type="file"
        accept=".py,.sh"
        style={{ display: 'none' }}
        onChange={handleImportScript}
      />
      <input
        ref={jsonInputRef}
        type="file"
        accept=".json"
        style={{ display: 'none' }}
        onChange={handleImportJson}
      />

      {/* Template Gallery */}
      <div
        className="template-gallery"
        style={{
          display: 'flex',
          gap: 10,
          overflowX: 'auto',
          paddingBottom: 8,
          marginBottom: 12,
        }}
      >
        <div
          style={{
            flex: '0 0 auto',
            display: 'flex',
            alignItems: 'center',
            padding: '0 10px',
            color: '#7df9ff',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            textTransform: 'uppercase',
            letterSpacing: 1,
            whiteSpace: 'nowrap',
          }}
        >
          Templates ▸
        </div>
        {SKILL_TEMPLATES.map((tpl) => {
          const active = tpl.language === language;
          return (
            <button
              key={tpl.id}
              type="button"
              onClick={() => onApplyTemplate(tpl)}
              title={tpl.description}
              style={{
                flex: '0 0 auto',
                minWidth: 180,
                maxWidth: 240,
                background: active
                  ? 'linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,255,200,0.06))'
                  : 'rgba(15,25,35,0.85)',
                border: active
                  ? '1px solid rgba(0,255,136,0.55)'
                  : '1px solid rgba(0,255,200,0.18)',
                borderRadius: 6,
                padding: '10px 12px',
                cursor: 'pointer',
                textAlign: 'left',
                color: '#cfe8e0',
                fontFamily: "'JetBrains Mono', monospace",
                transition: 'all 0.15s ease',
                boxShadow: active ? '0 0 12px rgba(0,255,136,0.18)' : 'none',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(0,255,200,0.6)';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = active
                  ? 'rgba(0,255,136,0.55)'
                  : 'rgba(0,255,200,0.18)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ fontSize: 13, marginBottom: 4, color: '#e8fff5' }}>
                <span style={{ marginRight: 6 }}>{tpl.icon}</span>
                <strong>{tpl.name}</strong>
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: '#8aa39b',
                  lineHeight: 1.35,
                  overflow: 'hidden',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                }}
              >
                {tpl.description}
              </div>
            </button>
          );
        })}
      </div>

      {/* Bash warning banner */}
      {isBash && (
        <div
          className="bash-warning"
          style={{
            background: 'rgba(255,180,0,0.10)',
            border: '1px solid rgba(255,180,0,0.45)',
            borderLeft: '4px solid #ffb400',
            borderRadius: 4,
            padding: '10px 14px',
            marginBottom: 12,
            color: '#ffd479',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12.5,
            lineHeight: 1.5,
          }}
        >
          <strong>⚠ Bash skills do NOT get Pydantic I/O validation.</strong>{' '}
          Schemas defined in the I/O SCHEMA tab will be ignored. Use <code>$1</code> for
          JSON input and <code>echo</code>/<code>printf</code> for output.
        </div>
      )}

      <div className="script-toolbar">
        <button className="btn btn-import" onClick={() => fileInputRef.current?.click()}>
          📥 IMPORT .PY / .SH
        </button>
        <button className="btn btn-import" onClick={() => jsonInputRef.current?.click()}>
          📥 IMPORT .JSON
        </button>
        <div className="toolbar-spacer" />
        <button className="btn btn-export" onClick={handleExportScript} disabled={!scriptBody}>
          📤 EXPORT {language === 'bash' ? '.SH' : '.PY'}
        </button>
        <button className="btn btn-export-json" onClick={handleExportJson} disabled={!skillForExport}>
          📤 EXPORT JSON
        </button>
        <span className="monaco-status">Monaco Editor • {language}</span>
      </div>

      <div className="script-editor-wrapper" style={{ height: 'calc(100vh - 320px)', minHeight: 400 }}>
        <Editor
          height="100%"
          language={language === 'bash' ? 'shell' : 'python'}
          value={scriptBody}
          onChange={val => onScriptBodyChange(val || '')}
          onMount={handleMount}
          theme="vs-dark"
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            lineNumbers: 'on',
            renderWhitespace: 'selection',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 12 },
            bracketPairColorization: { enabled: true },
            tabSize: 4,
            wordWrap: 'on',
          }}
        />
      </div>

      {/* Comprehensive I/O Contract hint */}
      <div
        className="script-hint"
        style={{
          marginTop: 12,
          background: 'rgba(10,18,26,0.9)',
          border: '1px solid rgba(0,255,200,0.18)',
          borderLeft: '4px solid #00ffae',
          borderRadius: 4,
          padding: '14px 16px',
          color: '#9fb8b0',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 12,
          lineHeight: 1.6,
        }}
      >
        {isBash ? (
          <>
            <div style={{ color: '#ffb400', fontWeight: 700, marginBottom: 8, fontSize: 13 }}>
              ⚠ BASH SKILLS — I/O CONTRACT BYPASSED
            </div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              <li>
                <strong style={{ color: '#e8fff5' }}>No Pydantic validation</strong> — the
                auto-prepended <code style={codeStyle}>SkillInput</code> /{' '}
                <code style={codeStyle}>SkillOutput</code> /{' '}
                <code style={codeStyle}>_emit_output()</code> do NOT apply.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Input:</strong> arrives as a JSON string in{' '}
                <code style={codeStyle}>$1</code>. Parse with{' '}
                <code style={codeStyle}>jq</code> or manual tools.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Output:</strong> write to stdout via{' '}
                <code style={codeStyle}>echo</code> / <code style={codeStyle}>printf</code>.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Schemas</strong> (if defined in the I/O SCHEMA tab)
                are <strong>ignored</strong> for Bash skills.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>No function wrapper</strong> — your script runs
                top-to-bottom as a raw shell program.
              </li>
            </ul>
          </>
        ) : (
          <>
            <div style={{ color: '#00ffae', fontWeight: 700, marginBottom: 8, fontSize: 13 }}>
              🐍 PYTHON SKILLS — I/O CONTRACT
            </div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              <li>
                <strong style={{ color: '#e8fff5' }}>Function signature</strong> (required):
                <br />
                <code style={codeStyle}>def main(inputs: SkillInput) -&gt; None:</code> — if you have
                an input_schema
                <br />
                <code style={codeStyle}>def main() -&gt; None:</code> — if NO input_schema is defined
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Accessing inputs:</strong>{' '}
                <code style={codeStyle}>inputs.target_url</code> — fields come from your INPUT SCHEMA,
                already validated as a <code style={codeStyle}>SkillInput</code> Pydantic model.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Emitting output</strong> (the ONLY valid channel):
                <br />
                <code style={codeStyle}>_emit_output({'{ "key": value }'})</code> — keys MUST match your
                OUTPUT SCHEMA. <code style={codeStyle}>print()</code> is hijacked and will NOT work.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Available in scope (auto-injected):</strong>{' '}
                <code style={codeStyle}>SkillInput</code>, <code style={codeStyle}>SkillOutput</code>,{' '}
                <code style={codeStyle}>_emit_output()</code>,{' '}
                <code style={codeStyle}>_parse_and_validate_input()</code>.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Imports allowed at top:</strong>{' '}
                <code style={codeStyle}>requests</code>, <code style={codeStyle}>bs4</code>,{' '}
                <code style={codeStyle}>json</code>, <code style={codeStyle}>sys</code>, etc.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Do NOT use:</strong>{' '}
                <code style={codeStyle}>print()</code>, <code style={codeStyle}>sys.argv</code>,{' '}
                <code style={codeStyle}>argparse</code> — the system handles all I/O.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>Helper functions</strong> may be defined before or
                after <code style={codeStyle}>main()</code> — only{' '}
                <code style={codeStyle}>main()</code> is the entrypoint.
              </li>
              <li>
                <strong style={{ color: '#e8fff5' }}>On save:</strong> the backend's{' '}
                <code style={codeStyle}>assemble_full_script()</code> auto-prepends the Pydantic models +
                a generated entrypoint that calls <code style={codeStyle}>main()</code>.
              </li>
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

const codeStyle: React.CSSProperties = {
  background: 'rgba(0,255,200,0.08)',
  border: '1px solid rgba(0,255,200,0.18)',
  borderRadius: 3,
  padding: '1px 5px',
  color: '#7df9ff',
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: 11.5,
};
