import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHasuraQuery } from '../../hooks/useHasuraQuery';
import { GET_SKILLS } from '../../queries';
import { skillApi } from '../../services/skillApi';
import { cn } from '@/lib/utils';

interface SkillTemplate {
  id: number;
  name: string;
  description: string;
  language: string;
  tags: string[];
  usage_count: number;
  version: number;
  is_robust: boolean;
  is_deprecated: boolean;
  merged_from: number[] | null;
  created_at: string;
  updated_at: string;
  instructions: string;
  script_body: string | null;
  script_content: string | null;
  input_schema: any | null;
  output_schema: any | null;
  has_io_contract: boolean;
  last_verified_at: string | null;
  last_failure_reason: string | null;
  test_input_example: any | null;
}

const LANG_COLOR: Record<string, string> = {
  python: 'var(--text-cyan)',
  bash: 'var(--green)',
  sh: 'var(--green)',
  javascript: 'var(--amber)',
  ruby: 'var(--red)',
};

const renderSchemaProperties = (schema: any) => {
  if (!schema) return <div className="text-xs text-slate-600 italic p-2">No schema defined.</div>;
  
  let parsedSchema = schema;
  if (typeof schema === 'string') {
    try {
      parsedSchema = JSON.parse(schema);
    } catch (e) {
      return <pre className="m-0 p-3 bg-black/40 rounded text-xs text-slate-300 overflow-x-auto"><code>{schema}</code></pre>;
    }
  }

  if (!parsedSchema || typeof parsedSchema !== 'object') {
    return <div className="text-xs text-slate-600 italic p-2">Empty or invalid schema format.</div>;
  }

  if (!parsedSchema.properties || Object.keys(parsedSchema.properties).length === 0) {
    return (
      <div>
        <span className="text-xs text-slate-600 italic">No properties defined. Raw Schema:</span>
        <pre className="m-0 p-3 bg-black/40 rounded text-xs text-slate-300 overflow-x-auto"><code>{JSON.stringify(parsedSchema, null, 2)}</code></pre>
      </div>
    );
  }

  const properties = parsedSchema.properties;
  const requiredFields = parsedSchema.required || [];
  const propertyKeys = Object.keys(properties);

  return (
    <table className="w-full border-collapse text-xs text-left">
      <thead>
        <tr>
          <th className="px-3 py-2 text-slate-500 font-semibold border-b border-white/[0.08] uppercase text-[0.65rem] tracking-wide">Field</th>
          <th className="px-3 py-2 text-slate-500 font-semibold border-b border-white/[0.08] uppercase text-[0.65rem] tracking-wide">Type</th>
          <th className="px-3 py-2 text-slate-500 font-semibold border-b border-white/[0.08] uppercase text-[0.65rem] tracking-wide">Required</th>
          <th className="px-3 py-2 text-slate-500 font-semibold border-b border-white/[0.08] uppercase text-[0.65rem] tracking-wide">Description</th>
        </tr>
      </thead>
      <tbody>
        {propertyKeys.map((key) => {
          const prop = properties[key];
          return (
            <tr key={key}>
              <td className="px-3 py-2.5 border-b border-white/[0.04] align-middle"><code className="text-sky-400">{key}</code></td>
              <td className="px-3 py-2.5 border-b border-white/[0.04] align-middle"><span className="bg-sky-400/10 text-sky-400 px-1.5 py-0.5 rounded text-[0.65rem] font-semibold">{prop.type || 'any'}</span></td>
              <td className="px-3 py-2.5 border-b border-white/[0.04] align-middle">
                {requiredFields.includes(key) ? (
                  <span className="bg-red-500/10 text-red-400 px-1.5 py-0.5 rounded text-[0.65rem] font-bold">Yes</span>
                ) : (
                  <span className="bg-slate-600/20 text-slate-400 px-1.5 py-0.5 rounded text-[0.65rem] font-bold">No</span>
                )}
              </td>
              <td className="px-3 py-2.5 border-b border-white/[0.04] align-middle text-slate-400 leading-snug">{prop.description || prop.title || '-'}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

const SkillLibraryPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedSkill, setSelectedSkill] = useState<SkillTemplate | null>(null);
  const [activeTab, setActiveTab] = useState<'script_body' | 'instructions' | 'script_content' | 'io_layers'>('script_body');
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const navigate = useNavigate();

  const { data, loading, error, refetch } = useHasuraQuery(GET_SKILLS, {
    search: '%',
  });

  const handleSearch = (val: string) => {
    setSearch(val);
    clearTimeout((handleSearch as any)._timer);
    (handleSearch as any)._timer = setTimeout(() => {
      const pattern = val.trim() ? `%${val.trim()}%` : '%';
      refetch({ search: pattern });
    }, 350);
  };

  const skills: SkillTemplate[] = data?.core_skill_template ?? [];
  const totalCount: number = data?.core_skill_template_aggregate?.aggregate?.count ?? 0;

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1500);
  };

  const langStats = useMemo(() => {
    const map: Record<string, number> = {};
    skills.forEach(s => {
      const lang = s.language || 'other';
      map[lang] = (map[lang] || 0) + 1;
    });
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }, [skills]);

  return (
    <div className="flex flex-col h-[calc(100vh-var(--navbar-height))] mt-[var(--navbar-height)] bg-bg-base text-text-primary font-mono overflow-hidden">
      {/* ========== Header ========== */}
      <div className="flex items-center justify-between flex-wrap gap-4 px-8 py-5 border-b border-border-subtle bg-green-500/[0.02] shrink-0">
        <div>
          <h1 className="text-xl font-bold text-green [text-shadow:var(--glow-green)] tracking-[0.1em] m-0">
            <span className="text-[rgba(0,255,0,0.4)]">[</span>
            SKILL_LIBRARY
            <span className="text-[rgba(0,255,0,0.4)]">]</span>
          </h1>
          <span className="text-[0.7rem] text-text-secondary tracking-wide opacity-80">AI 自我進化知識庫 — 跨任務重用腳本系統</span>
        </div>

        <div className="flex gap-6 items-center flex-wrap">
          <div className="flex flex-col items-center min-w-[52px]">
            <span className="text-lg font-bold text-green [text-shadow:var(--glow-green)] leading-none">{totalCount}</span>
            <span className="text-[0.55rem] text-text-muted tracking-[0.1em] mt-1">TOTAL SKILLS</span>
          </div>
          {langStats.map(([lang, count]) => (
            <div className="flex flex-col items-center min-w-[52px]" key={lang}>
              <span className="text-lg font-bold leading-none" style={{ color: LANG_COLOR[lang] ?? '#94a3b8' }}>
                {count}
              </span>
              <span className="text-[0.55rem] text-text-muted tracking-[0.1em] mt-1">{lang.toUpperCase()}</span>
            </div>
          ))}
          <button
            className="ml-auto px-4 py-1.5 rounded bg-green/10 border border-green/30 text-[#00ff00] font-bold text-[0.7rem] tracking-[0.08em] cursor-pointer"
            onClick={() => navigate('/skills/new')}
          >
            + ADD SKILL
          </button>
        </div>
      </div>

      {/* ========== Search Bar ========== */}
      <div className="flex items-center gap-3 px-8 py-3 border-b border-border-subtle bg-slate-900/40 shrink-0">
        <span className="text-green text-sm opacity-80">&gt;_</span>
        <input
          className="flex-1 bg-transparent border-none outline-none text-text-primary font-mono text-[0.85rem] placeholder:text-[#334155]"
          type="text"
          placeholder="Search by name, description, or tag..."
          value={search}
          onChange={e => handleSearch(e.target.value)}
          autoFocus
        />
        {search && (
          <button className="bg-transparent border-none text-slate-500 cursor-pointer text-[0.85rem] px-1.5 py-0.5 rounded hover:text-red-500" onClick={() => handleSearch('')}>✕</button>
        )}
      </div>

      {/* ========== Main Split Layout ========== */}
      <div className="flex flex-1 overflow-hidden">
        {/* ---- Skill List ---- */}
        <div className="w-[350px] shrink-0 overflow-y-auto border-r border-border-subtle bg-slate-900/20">
          {loading && (
            <div className="p-[60px] text-center text-text-muted text-xs tracking-[0.1em] leading-relaxed">
              <span className="animate-pulse">_</span> LOADING FROM DB...
            </div>
          )}
          {error && (
            <div className="p-6 text-red text-[0.85rem] font-semibold text-center">
              ⚠ GraphQL Error: {error.message}
            </div>
          )}
          {!loading && !error && skills.length === 0 && (
            <div className="p-[60px] text-center text-text-muted text-xs tracking-[0.1em] leading-relaxed">
              NO SKILLS FOUND. AI HAS NOT LEARNED ANY TECHNIQUES YET.
            </div>
          )}
          {skills.map(skill => (
            <div
              key={skill.id}
              className={cn(
                "px-5 py-3 border-b border-white/[0.04] cursor-pointer transition-colors duration-150 border-l-3 border-l-transparent hover:bg-[rgba(0,255,0,0.04)] hover:border-l-[rgba(0,255,0,0.3)]",
                selectedSkill?.id === skill.id && "bg-[rgba(0,255,0,0.07)] border-l-[#00ff00]"
              )}
              onClick={() => { setSelectedSkill(skill); setActiveTab('script_body'); }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span
                  className="text-[0.6rem] font-bold px-1.5 py-0.5 rounded text-black tracking-[0.05em] shrink-0"
                  style={{ background: LANG_COLOR[skill.language] ?? 'var(--text-muted)' }}
                >
                  {skill.language}
                </span>
                <span className="text-[0.85rem] text-text-primary font-semibold flex-1 overflow-hidden text-ellipsis whitespace-nowrap">{skill.name}</span>
                <span className="text-[0.65rem] text-text-muted" title="Usage count">
                  ▶ {skill.usage_count}
                </span>
                {(skill.merged_from && skill.merged_from.length > 0) && (
                  <span className="text-[0.55rem] font-bold px-1.5 py-0.5 rounded text-amber-400 border border-amber-400 bg-amber-400/10 tracking-[0.05em] shrink-0" title={`Merged from IDs: ${skill.merged_from.join(', ')}`}>
                    ⚡ MERGED
                  </span>
                )}
              </div>
              <div className="text-[0.72rem] text-text-secondary leading-snug line-clamp-2 mb-1.5">{skill.description}</div>
              {Array.isArray(skill.tags) && skill.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {skill.tags.map(tag => (
                    <span
                      key={tag}
                      className="text-[0.62rem] px-1.5 py-0.5 rounded-full bg-blue-500/12 text-blue-400 border border-blue-500/20 cursor-pointer transition-colors duration-150 hover:bg-blue-500/25"
                      onClick={e => { e.stopPropagation(); handleSearch(tag); }}
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* ---- Detail Panel ---- */}
        <div className="flex-1 overflow-y-auto flex flex-col bg-bg-surface">
          {!selectedSkill ? (
            <div className="flex-1 flex flex-col items-center justify-center text-text-muted text-xs tracking-[0.1em] gap-3">
              <div className="text-[2.5rem] opacity-30">⚡</div>
              <div>SELECT A SKILL TO VIEW DETAILS</div>
              <div className="text-[0.75rem] opacity-50 mt-2">
                {totalCount} skills loaded from skill library
              </div>
            </div>
          ) : (
            <>
              {/* Detail Header */}
              <div className="px-7 pt-6 pb-4 border-b border-white/[0.06] bg-black/20">
                <div className="flex items-center gap-2.5 mb-2">
                  <span
                    className="text-[0.6rem] font-bold px-1.5 py-0.5 rounded text-black tracking-[0.05em] shrink-0"
                    style={{ background: LANG_COLOR[selectedSkill.language] ?? 'var(--text-muted)', fontSize: '0.8rem' }}
                  >
                    {selectedSkill.language}
                  </span>
                  <h2 className="text-lg font-bold text-slate-100 m-0 tracking-[0.04em]">{selectedSkill.name}</h2>
                </div>
                <div className="flex gap-5 text-[0.72rem] text-slate-500 mb-2.5">
                  <span>🔢 Used: <strong className="text-slate-400">{selectedSkill.usage_count}x</strong></span>
                  <span>📅 Updated: {new Date(selectedSkill.updated_at).toLocaleString()}</span>
                </div>
                <p className="text-[0.82rem] text-slate-400 leading-relaxed m-0">{selectedSkill.description}</p>
                {Array.isArray(selectedSkill.tags) && selectedSkill.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedSkill.tags.map(tag => (
                      <span key={tag} className="text-[0.62rem] px-1.5 py-0.5 rounded-full bg-blue-500/12 text-blue-400 border border-blue-500/20">#{tag}</span>
                    ))}
                  </div>
                )}

                {/* Merge Info */}
                {(selectedSkill.merged_from && selectedSkill.merged_from.length > 0) && (
                  <div className="flex items-center gap-1.5 mt-2.5 text-[0.75rem] text-amber-400 bg-amber-400/[0.08] px-2.5 py-1 rounded border border-amber-400/20">
                    <span className="text-[0.85rem]">⚡</span>
                    <span>Merged from IDs: </span>
                    {selectedSkill.merged_from?.map((id, i) => (
                      <span key={id}>
                        <span className="font-semibold text-amber-200">#{id}</span>
                        {(selectedSkill.merged_from && i < selectedSkill.merged_from.length - 1) && <span> + </span>}
                      </span>
                    ))}
                  </div>
                )}
                {selectedSkill.is_robust && (
                  <div className="inline-block mt-2 text-[0.7rem] font-bold px-2 py-0.5 rounded text-emerald-500 border border-emerald-500 bg-emerald-500/10">🛡️ ROBUST</div>
                )}
                {(selectedSkill.input_schema || selectedSkill.output_schema) && (
                  <div className="inline-block mt-2 ml-1.5 text-[0.7rem] font-bold px-2 py-0.5 rounded text-purple-500 border border-purple-500 bg-purple-500/10">📋 I/O CONTRACT</div>
                )}

              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mt-3 px-7">
                <button
                  className="px-3.5 py-1 rounded bg-green/[0.08] border border-green/25 text-[#00ff00] font-bold text-[0.65rem] tracking-[0.08em] cursor-pointer"
                  onClick={() => navigate(`/skills/${selectedSkill.id}/edit`)}
                >
                  EDIT
                </button>
                <button
                  className="px-3.5 py-1 rounded bg-red-500/[0.08] border border-red-500/25 text-red-400 font-bold text-[0.65rem] tracking-[0.08em] cursor-pointer"
                  onClick={async () => {
                    if (!selectedSkill) return;
                    if (!window.confirm(`Permanently delete skill "${selectedSkill.name}"?`)) return;
                    try {
                      await skillApi.delete(selectedSkill.id);
                      setSelectedSkill(null);
                      const pattern = search.trim() ? `%${search.trim()}%` : '%';
                      refetch({ search: pattern });
                    } catch (e: any) {
                      alert(e?.response?.data?.detail || e?.message || 'Delete failed');
                    }
                  }}
                >
                  DELETE
                </button>
              </div>

              {/* Tab Switcher */}
              <div className="flex border-b border-white/[0.06] bg-black/15 mt-3">
                {(['script_body', 'io_layers', 'instructions', 'script_content'] as const).map(tab => (
                  <button
                    key={tab}
                    className={cn(
                      "px-6 py-2.5 bg-transparent border-none border-b-2 border-transparent text-slate-600 font-mono text-[0.75rem] font-semibold tracking-[0.08em] cursor-pointer transition-all duration-150 hover:bg-[rgba(0,255,0,0.05)] hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:border-b-transparent",
                      activeTab === tab && "text-[#00ff00] border-b-[#00ff00] bg-[rgba(0,255,0,0.03)]"
                    )}
                    onClick={() => setActiveTab(tab)}
                    disabled={
                      (tab === 'script_body' && !selectedSkill.script_body) ||
                      (tab === 'script_content' && !selectedSkill.script_content)
                    }
                  >
                    {tab === 'script_body' && `CORE LOGIC ${!selectedSkill.script_body ? '(NONE)' : ''}`}
                    {tab === 'io_layers' && 'I/O DEFINITION'}
                    {tab === 'instructions' && 'USAGE GUIDE'}
                    {tab === 'script_content' && `FULL EXECUTABLE ${!selectedSkill.script_content ? '(NONE)' : ''}`}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden relative">
                {activeTab === 'script_body' && selectedSkill.script_body && (
                  <div className="relative h-full overflow-y-auto">
                    <div className="flex justify-between items-center mb-2 px-1">
                      <div className="flex items-center gap-3">
                        <span className="text-slate-500 text-xs uppercase tracking-[0.1em]">python</span>
                        <span className="text-[#00ff00] text-[0.65rem] opacity-80 tracking-wide font-semibold">ACTUAL EXECUTION LOGIC (script_body)</span>
                      </div>
                      <button
                        className="sticky top-3 float-right mr-5 mt-3 px-3 py-1 bg-[rgba(0,255,0,0.1)] border border-[rgba(0,255,0,0.25)] rounded text-[#00ff00] font-bold text-[0.65rem] tracking-[0.08em] cursor-pointer z-[2] hover:bg-[rgba(0,255,0,0.2)]"
                        onClick={() => handleCopy(selectedSkill.script_body!, 'script_body')}
                      >
                        {copiedField === 'script_body' ? '✓ COPIED' : 'COPY'}
                      </button>
                    </div>
                    <pre className="m-0 px-7 py-5 font-mono text-[0.78rem] leading-[1.7] text-slate-400 whitespace-pre-wrap break-words"><code className="text-[#a5f3a5]">{selectedSkill.script_body}</code></pre>
                  </div>
                )}
                {activeTab === 'io_layers' && (
                  <div className="p-7 h-full overflow-y-auto bg-[#09090b]">
                    <div className="bg-white/[0.02] border border-white/[0.05] rounded-md overflow-hidden">
                      <div className="text-[0.85rem] font-bold text-[#00ff00] mb-1 tracking-[0.05em] px-4 pt-4">📥 INPUT SCHEMA (SkillInput)</div>
                      <div className="text-[0.7rem] text-slate-500 mb-3 px-4">Parameters passed to the main() function</div>
                      <div className="p-4">
                        {renderSchemaProperties(selectedSkill.input_schema)}
                      </div>
                    </div>
                    <div className="bg-white/[0.02] border border-white/[0.05] rounded-md overflow-hidden mt-6">
                      <div className="text-[0.85rem] font-bold text-[#00ff00] mb-1 tracking-[0.05em] px-4 pt-4">📤 OUTPUT SCHEMA (SkillOutput)</div>
                      <div className="text-[0.7rem] text-slate-500 mb-3 px-4">Structured data emitted via _emit_output()</div>
                      <div className="p-4">
                        {renderSchemaProperties(selectedSkill.output_schema)}
                      </div>
                    </div>
                  </div>
                )}
                {activeTab === 'instructions' && (
                  <div className="relative h-full overflow-y-auto">
                    <button
                      className="sticky top-3 float-right mr-5 mt-3 px-3 py-1 bg-[rgba(0,255,0,0.1)] border border-[rgba(0,255,0,0.25)] rounded text-[#00ff00] font-bold text-[0.65rem] tracking-[0.08em] cursor-pointer z-[2] hover:bg-[rgba(0,255,0,0.2)]"
                      onClick={() => handleCopy(selectedSkill.instructions, 'instructions')}
                    >
                      {copiedField === 'instructions' ? '✓ COPIED' : 'COPY'}
                    </button>
                    <pre className="m-0 px-7 py-5 font-mono text-[0.78rem] leading-[1.7] text-slate-400 whitespace-pre-wrap break-words"><code className="text-[#a5f3a5]">{selectedSkill.instructions}</code></pre>
                  </div>
                )}
                {activeTab === 'script_content' && selectedSkill.script_content && (
                  <div className="relative h-full overflow-y-auto">
                    <div className="flex justify-between items-center mb-2 px-1">
                      <span className="text-slate-500 text-xs uppercase tracking-[0.1em]">{selectedSkill.language}</span>
                      <button
                        className="sticky top-3 float-right mr-5 mt-3 px-3 py-1 bg-[rgba(0,255,0,0.1)] border border-[rgba(0,255,0,0.25)] rounded text-[#00ff00] font-bold text-[0.65rem] tracking-[0.08em] cursor-pointer z-[2] hover:bg-[rgba(0,255,0,0.2)]"
                        onClick={() => handleCopy(selectedSkill.script_content!, 'script_content')}
                      >
                        {copiedField === 'script_content' ? '✓ COPIED' : 'COPY'}
                      </button>
                    </div>
                    <pre className="m-0 px-7 py-5 font-mono text-[0.78rem] leading-[1.7] text-slate-400 whitespace-pre-wrap break-words"><code className="text-[#a5f3a5]">{selectedSkill.script_content}</code></pre>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SkillLibraryPage;
