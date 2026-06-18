import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHasuraQuery } from '../../hooks/useHasuraQuery';
import { GET_SKILLS } from '../../queries';
import { skillApi } from '../../services/skillApi';
import './SkillLibrary.css';

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
  if (!schema) return <div className="no-schema">No schema defined.</div>;
  
  let parsedSchema = schema;
  if (typeof schema === 'string') {
    try {
      parsedSchema = JSON.parse(schema);
    } catch (e) {
      return <pre className="raw-json-schema"><code>{schema}</code></pre>;
    }
  }

  if (!parsedSchema || typeof parsedSchema !== 'object') {
    return <div className="no-schema">Empty or invalid schema format.</div>;
  }

  if (!parsedSchema.properties || Object.keys(parsedSchema.properties).length === 0) {
    return (
      <div className="no-schema-properties">
        <span className="no-schema-label">No properties defined. Raw Schema:</span>
        <pre className="raw-json-schema"><code>{JSON.stringify(parsedSchema, null, 2)}</code></pre>
      </div>
    );
  }

  const properties = parsedSchema.properties;
  const requiredFields = parsedSchema.required || [];
  const propertyKeys = Object.keys(properties);

  return (
    <table className="schema-table">
      <thead>
        <tr>
          <th>Field</th>
          <th>Type</th>
          <th>Required</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        {propertyKeys.map((key) => {
          const prop = properties[key];
          return (
            <tr key={key}>
              <td className="field-name"><code>{key}</code></td>
              <td className="field-type"><span className="type-badge">{prop.type || 'any'}</span></td>
              <td className="field-required">
                {requiredFields.includes(key) ? (
                  <span className="req-badge yes">Yes</span>
                ) : (
                  <span className="req-badge no">No</span>
                )}
              </td>
              <td className="field-desc">{prop.description || prop.title || '-'}</td>
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

  // Debounce search to avoid GQL overload
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
    <div className="skill-library-container">
      {/* ========== Header ========== */}
      <div className="skill-header">
        <div className="skill-header-left">
          <h1 className="skill-title">
            <span className="skill-title-bracket">[</span>
            SKILL_LIBRARY
            <span className="skill-title-bracket">]</span>
          </h1>
          <span className="skill-subtitle">AI 自我進化知識庫 — 跨任務重用腳本系統</span>
        </div>

        <div className="skill-stats-bar">
          <div className="skill-stat">
            <span className="skill-stat-val">{totalCount}</span>
            <span className="skill-stat-label">TOTAL SKILLS</span>
          </div>
          {langStats.map(([lang, count]) => (
            <div className="skill-stat" key={lang}>
              <span className="skill-stat-val" style={{ color: LANG_COLOR[lang] ?? '#94a3b8' }}>
                {count}
              </span>
              <span className="skill-stat-label">{lang.toUpperCase()}</span>
            </div>
          ))}
          <button
            className="btn"
            style={{
              marginLeft: 'auto', padding: '6px 16px', borderRadius: 4,
              background: 'rgba(0,255,0,0.1)', border: '1px solid rgba(0,255,0,0.3)',
              color: '#00ff00', fontFamily: 'inherit', fontSize: '0.7rem',
              fontWeight: 700, letterSpacing: '0.08em', cursor: 'pointer',
            }}
            onClick={() => navigate('/skills/new')}
          >
            + ADD SKILL
          </button>
        </div>
      </div>

      {/* ========== Search Bar ========== */}
      <div className="skill-search-bar">
        <span className="skill-search-icon">&gt;_</span>
        <input
          type="text"
          className="skill-search-input"
          placeholder="Search by name, description, or tag..."
          value={search}
          onChange={e => handleSearch(e.target.value)}
          autoFocus
        />
        {search && (
          <button className="skill-search-clear" onClick={() => handleSearch('')}>✕</button>
        )}
      </div>

      {/* ========== Main Split Layout ========== */}
      <div className="skill-layout">
        {/* ---- Skill List ---- */}
        <div className="skill-list">
          {loading && (
            <div className="skill-empty">
              <span className="pulse">_</span> LOADING FROM DB...
            </div>
          )}
          {error && (
            <div className="skill-error">
              ⚠ GraphQL Error: {error.message}
            </div>
          )}
          {!loading && !error && skills.length === 0 && (
            <div className="skill-empty">
              NO SKILLS FOUND. AI HAS NOT LEARNED ANY TECHNIQUES YET.
            </div>
          )}
          {skills.map(skill => (
            <div
              key={skill.id}
              className={`skill-card ${selectedSkill?.id === skill.id ? 'selected' : ''}`}
              onClick={() => { setSelectedSkill(skill); setActiveTab('script_body'); }}
            >
              <div className="skill-card-header">
                <span
                  className="skill-lang-badge"
                  style={{ background: LANG_COLOR[skill.language] ?? 'var(--text-muted)' }}
                >
                  {skill.language}
                </span>
                <span className="skill-card-name">{skill.name}</span>
                <span className="skill-usage-badge" title="Usage count">
                  ▶ {skill.usage_count}
                </span>
                {(skill.merged_from && skill.merged_from.length > 0) && (
                  <span className="skill-merge-badge" title={`Merged from IDs: ${skill.merged_from.join(', ')}`}>
                    ⚡ MERGED
                  </span>
                )}
              </div>
              <div className="skill-card-desc">{skill.description}</div>
              {Array.isArray(skill.tags) && skill.tags.length > 0 && (
                <div className="skill-tags">
                  {skill.tags.map(tag => (
                    <span
                      key={tag}
                      className="skill-tag"
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
        <div className="skill-detail-panel">
          {!selectedSkill ? (
            <div className="skill-detail-empty">
              <div className="skill-detail-empty-icon">⚡</div>
              <div>SELECT A SKILL TO VIEW DETAILS</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: 8 }}>
                {totalCount} skills loaded from skill library
              </div>
            </div>
          ) : (
            <>
              {/* Detail Header */}
              <div className="skill-detail-header">
                <div className="skill-detail-title-row">
                  <span
                    className="skill-lang-badge"
                    style={{ background: LANG_COLOR[selectedSkill.language] ?? 'var(--text-muted)', fontSize: '0.8rem' }}
                  >
                    {selectedSkill.language}
                  </span>
                  <h2 className="skill-detail-title">{selectedSkill.name}</h2>
                </div>
                <div className="skill-detail-meta">
                  <span>🔢 Used: <strong>{selectedSkill.usage_count}x</strong></span>
                  <span>📅 Updated: {new Date(selectedSkill.updated_at).toLocaleString()}</span>
                </div>
                <p className="skill-detail-desc">{selectedSkill.description}</p>
                {Array.isArray(selectedSkill.tags) && selectedSkill.tags.length > 0 && (
                  <div className="skill-tags" style={{ marginTop: 8 }}>
                    {selectedSkill.tags.map(tag => (
                      <span key={tag} className="skill-tag">#{tag}</span>
                    ))}
                  </div>
                )}

                {/* Merge Info */}
                {(selectedSkill.merged_from && selectedSkill.merged_from.length > 0) && (
                  <div className="skill-merge-info">
                    <span className="skill-merge-icon">⚡</span>
                    <span>Merged from IDs: </span>
                    {selectedSkill.merged_from?.map((id, i) => (
                      <span key={id}>
                        <span className="skill-merge-source">#{id}</span>
                        {(selectedSkill.merged_from && i < selectedSkill.merged_from.length - 1) && <span> + </span>}
                      </span>
                    ))}
                  </div>
                )}
                {selectedSkill.is_robust && (
                  <div className="skill-robust-badge">🛡️ ROBUST</div>
                )}
                {(selectedSkill.input_schema || selectedSkill.output_schema) && (
                  <div className="skill-io-badge">📋 I/O CONTRACT</div>
                )}

              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                  className="btn"
                  style={{
                    padding: '4px 14px', borderRadius: 4,
                    background: 'rgba(0,255,0,0.08)', border: '1px solid rgba(0,255,0,0.25)',
                    color: '#00ff00', fontFamily: 'inherit', fontSize: '0.65rem',
                    fontWeight: 700, letterSpacing: '0.08em', cursor: 'pointer',
                  }}
                  onClick={() => navigate(`/skills/${selectedSkill.id}/edit`)}
                >
                  EDIT
                </button>
                <button
                  className="btn"
                  style={{
                    padding: '4px 14px', borderRadius: 4,
                    background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
                    color: '#f87171', fontFamily: 'inherit', fontSize: '0.65rem',
                    fontWeight: 700, letterSpacing: '0.08em', cursor: 'pointer',
                  }}
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
              <div className="skill-tabs">
                <button
                  className={`skill-tab-btn ${activeTab === 'script_body' ? 'active' : ''}`}
                  onClick={() => setActiveTab('script_body')}
                  disabled={!selectedSkill.script_body}
                >
                  CORE LOGIC {!selectedSkill.script_body && '(NONE)'}
                </button>
                <button
                  className={`skill-tab-btn ${activeTab === 'io_layers' ? 'active' : ''}`}
                  onClick={() => setActiveTab('io_layers')}
                >
                  I/O DEFINITION
                </button>
                <button
                  className={`skill-tab-btn ${activeTab === 'instructions' ? 'active' : ''}`}
                  onClick={() => setActiveTab('instructions')}
                >
                  USAGE GUIDE
                </button>
                <button
                  className={`skill-tab-btn ${activeTab === 'script_content' ? 'active' : ''}`}
                  onClick={() => setActiveTab('script_content')}
                  disabled={!selectedSkill.script_content}
                >
                  FULL EXECUTABLE
                </button>
              </div>

              {/* Tab Content */}
              <div className="skill-tab-content">
                {activeTab === 'script_body' && selectedSkill.script_body && (
                  <div className="skill-code-block">
                    <div className="skill-code-header">
                      <div className="skill-code-info">
                        <span className="skill-code-lang">python</span>
                        <span className="skill-code-label">ACTUAL EXECUTION LOGIC (script_body)</span>
                      </div>
                      <button
                        className="skill-copy-btn"
                        onClick={() => handleCopy(selectedSkill.script_body!, 'script_body')}
                      >
                        {copiedField === 'script_body' ? '✓ COPIED' : 'COPY'}
                      </button>
                    </div>
                    <pre><code>{selectedSkill.script_body}</code></pre>
                  </div>
                )}
                {activeTab === 'io_layers' && (
                  <div className="skill-io-layers-panel">
                    <div className="io-layer-section">
                      <div className="io-layer-title">📥 INPUT SCHEMA (SkillInput)</div>
                      <div className="io-layer-subtitle">Parameters passed to the main() function</div>
                      <div className="io-layer-body">
                        {renderSchemaProperties(selectedSkill.input_schema)}
                      </div>
                    </div>
                    <div className="io-layer-section" style={{ marginTop: '24px' }}>
                      <div className="io-layer-title">📤 OUTPUT SCHEMA (SkillOutput)</div>
                      <div className="io-layer-subtitle">Structured data emitted via _emit_output()</div>
                      <div className="io-layer-body">
                        {renderSchemaProperties(selectedSkill.output_schema)}
                      </div>
                    </div>
                  </div>
                )}
                {activeTab === 'instructions' && (
                  <div className="skill-code-block">
                    <button
                      className="skill-copy-btn"
                      onClick={() => handleCopy(selectedSkill.instructions, 'instructions')}
                    >
                      {copiedField === 'instructions' ? '✓ COPIED' : 'COPY'}
                    </button>
                    <pre><code>{selectedSkill.instructions}</code></pre>
                  </div>
                )}
                {activeTab === 'script_content' && selectedSkill.script_content && (
                  <div className="skill-code-block">
                    <div className="skill-code-header">
                      <span className="skill-code-lang">{selectedSkill.language}</span>
                      <button
                        className="skill-copy-btn"
                        onClick={() => handleCopy(selectedSkill.script_content!, 'script_content')}
                      >
                        {copiedField === 'script_content' ? '✓ COPIED' : 'COPY'}
                      </button>
                    </div>
                    <pre><code>{selectedSkill.script_content}</code></pre>
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
