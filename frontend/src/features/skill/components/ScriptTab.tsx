import { useRef, useCallback } from 'react';
import type { ChangeEvent } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import { exportScript, exportSkillJson, readTextFile, extractScriptBody, detectLanguage } from '../../../utils/skillFileIo';
import type { SkillTemplate } from '../services/skillApi';
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

const codeClasses =
  'bg-[rgba(0,255,200,0.08)] border border-[rgba(0,255,200,0.18)] rounded-[3px] px-[5px] py-[1px] text-cyan font-mono text-[11.5px]';

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
    } catch (err: unknown) {
      alert(`Import error: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
    } catch (err: unknown) {
      alert(`Import error: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
        className="hidden"
        onChange={handleImportScript}
      />
      <input
        ref={jsonInputRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={handleImportJson}
      />

      {/* Template Gallery */}
      <div className="template-gallery flex gap-2.5 overflow-x-auto pb-2 mb-3">
        <div className="flex-none flex items-center px-[10px] text-cyan font-mono text-xs uppercase tracking-[1px] whitespace-nowrap">
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
              className="flex-none min-w-[180px] max-w-[240px] rounded-md px-3 py-[10px] cursor-pointer text-left text-[#cfe8e0] font-mono transition-all duration-150"
              style={{
                background: active
                  ? 'linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,255,200,0.06))'
                  : 'rgba(15,25,35,0.85)',
                border: active
                  ? '1px solid rgba(0,255,136,0.55)'
                  : '1px solid rgba(0,255,200,0.18)',
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
              <div className="text-[13px] mb-1 text-text-primary">
                <span className="mr-1.5">{tpl.icon}</span>
                <strong>{tpl.name}</strong>
              </div>
              <div className="text-[11px] text-text-muted leading-[1.35] overflow-hidden line-clamp-2">
                {tpl.description}
              </div>
            </button>
          );
        })}
      </div>

      {/* Bash warning banner */}
      {isBash && (
        <div className="bash-warning bg-[rgba(255,180,0,0.10)] border border-[rgba(255,180,0,0.45)] border-l-4 border-l-[#ffb400] rounded px-[14px] py-[10px] mb-3 text-amber font-mono text-[12.5px] leading-normal">
          <strong>⚠ Bash skills do NOT get Pydantic I/O validation.</strong>{' '}
          Schemas defined in the I/O SCHEMA tab will be ignored. Use <code className={codeClasses}>$1</code> for
          JSON input and <code className={codeClasses}>echo</code>/<code className={codeClasses}>printf</code> for output.
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

      <div className="script-editor-wrapper h-[calc(100vh-320px)] min-h-[400px]">
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
      <div className="script-hint mt-3 bg-[rgba(10,18,26,0.9)] border border-[rgba(0,255,200,0.18)] border-l-4 border-l-[#00ffae] rounded px-4 py-[14px] text-text-muted font-mono text-xs leading-[1.6]">
        {isBash ? (
          <>
            <div className="text-amber font-bold mb-2 text-[13px]">
              ⚠ BASH SKILLS — I/O CONTRACT BYPASSED
            </div>
            <ul className="m-0 pl-[18px]">
              <li>
                <strong className="text-text-primary">No Pydantic validation</strong> — the
                auto-prepended <code className={codeClasses}>SkillInput</code> /{' '}
                <code className={codeClasses}>SkillOutput</code> /{' '}
                <code className={codeClasses}>_emit_output()</code> do NOT apply.
              </li>
              <li>
                <strong className="text-text-primary">Input:</strong> arrives as a JSON string in{' '}
                <code className={codeClasses}>$1</code>. Parse with{' '}
                <code className={codeClasses}>jq</code> or manual tools.
              </li>
              <li>
                <strong className="text-text-primary">Output:</strong> write to stdout via{' '}
                <code className={codeClasses}>echo</code> / <code className={codeClasses}>printf</code>.
              </li>
              <li>
                <strong className="text-text-primary">Schemas</strong> (if defined in the I/O SCHEMA tab)
                are <strong>ignored</strong> for Bash skills.
              </li>
              <li>
                <strong className="text-text-primary">No function wrapper</strong> — your script runs
                top-to-bottom as a raw shell program.
              </li>
            </ul>
          </>
        ) : (
          <>
            <div className="text-green font-bold mb-2 text-[13px]">
              🐍 PYTHON SKILLS — I/O CONTRACT
            </div>
            <ul className="m-0 pl-[18px]">
              <li>
                <strong className="text-text-primary">Function signature</strong> (required):
                <br />
                <code className={codeClasses}>def main(inputs: SkillInput) -&gt; None:</code> — if you have
                an input_schema
                <br />
                <code className={codeClasses}>def main() -&gt; None:</code> — if NO input_schema is defined
              </li>
              <li>
                <strong className="text-text-primary">Accessing inputs:</strong>{' '}
                <code className={codeClasses}>inputs.target_url</code> — fields come from your INPUT SCHEMA,
                already validated as a <code className={codeClasses}>SkillInput</code> Pydantic model.
              </li>
              <li>
                <strong className="text-text-primary">Emitting output</strong> (the ONLY valid channel):
                <br />
                <code className={codeClasses}>_emit_output({'{ "key": value }'})</code> — keys MUST match your
                OUTPUT SCHEMA. <code className={codeClasses}>print()</code> is hijacked and will NOT work.
              </li>
              <li>
                <strong className="text-text-primary">Available in scope (auto-injected):</strong>{' '}
                <code className={codeClasses}>SkillInput</code>, <code className={codeClasses}>SkillOutput</code>,{' '}
                <code className={codeClasses}>_emit_output()</code>,{' '}
                <code className={codeClasses}>_parse_and_validate_input()</code>.
              </li>
              <li>
                <strong className="text-text-primary">Imports allowed at top:</strong>{' '}
                <code className={codeClasses}>requests</code>, <code className={codeClasses}>bs4</code>,{' '}
                <code className={codeClasses}>json</code>, <code className={codeClasses}>sys</code>, etc.
              </li>
              <li>
                <strong className="text-text-primary">Do NOT use:</strong>{' '}
                <code className={codeClasses}>print()</code>, <code className={codeClasses}>sys.argv</code>,{' '}
                <code className={codeClasses}>argparse</code> — the system handles all I/O.
              </li>
              <li>
                <strong className="text-text-primary">Helper functions</strong> may be defined before or
                after <code className={codeClasses}>main()</code> — only{' '}
                <code className={codeClasses}>main()</code> is the entrypoint.
              </li>
              <li>
                <strong className="text-text-primary">On save:</strong> the backend's{' '}
                <code className={codeClasses}>assemble_full_script()</code> auto-prepends the Pydantic models +
                a generated entrypoint that calls <code className={codeClasses}>main()</code>.
              </li>
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
