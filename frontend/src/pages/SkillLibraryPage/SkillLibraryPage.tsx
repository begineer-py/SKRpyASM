import { useState, useMemo } from 'react';
import { useHasuraQuery } from '../../hooks/useHasuraQuery';
import { GET_SKILLS } from '../../queries';
import './SkillLibrary.css';

interface SkillTemplate {
  id: number;
  name: string;
  description: string;
  language: string;
  tags: string[];
  usage_count: number;
  created_at: string;
  updated_at: string;
  instructions: string;
  script_content: string | null;
}

const LANG_COLOR: Record<string, string> = {
  python: '#3b82f6',
  bash: '#10b981',
  sh: '#10b981',
  javascript: '#eab308',
  ruby: '#ef4444',
};

const SkillLibraryPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedSkill, setSelectedSkill] = useState<SkillTemplate | null>(null);
  const [activeTab, setActiveTab] = useState<'instructions' | 'script'>('instructions');
  const [copiedField, setCopiedField] = useState<string | null>(null);

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
              onClick={() => { setSelectedSkill(skill); setActiveTab('instructions'); }}
            >
              <div className="skill-card-header">
                <span
                  className="skill-lang-badge"
                  style={{ background: LANG_COLOR[skill.language] ?? '#64748b' }}
                >
                  {skill.language}
                </span>
                <span className="skill-card-name">{skill.name}</span>
                <span className="skill-usage-badge" title="Usage count">
                  ▶ {skill.usage_count}
                </span>
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
                    style={{ background: LANG_COLOR[selectedSkill.language] ?? '#64748b', fontSize: '0.8rem' }}
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
              </div>

              {/* Tab Switcher */}
              <div className="skill-tabs">
                <button
                  className={`skill-tab-btn ${activeTab === 'instructions' ? 'active' : ''}`}
                  onClick={() => setActiveTab('instructions')}
                >
                  INSTRUCTIONS
                </button>
                <button
                  className={`skill-tab-btn ${activeTab === 'script' ? 'active' : ''}`}
                  onClick={() => setActiveTab('script')}
                  disabled={!selectedSkill.script_content}
                >
                  SCRIPT {!selectedSkill.script_content && '(NONE)'}
                </button>
              </div>

              {/* Tab Content */}
              <div className="skill-tab-content">
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
                {activeTab === 'script' && selectedSkill.script_content && (
                  <div className="skill-code-block">
                    <button
                      className="skill-copy-btn"
                      onClick={() => handleCopy(selectedSkill.script_content!, 'script')}
                    >
                      {copiedField === 'script' ? '✓ COPIED' : 'COPY'}
                    </button>
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
