import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { skillApi } from '../../services/skillApi';
import type { SkillTemplate } from '../../services/skillApi';
import MetaTab from './components/MetaTab';
import ScriptTab from './components/ScriptTab';
import SchemaTab from './components/SchemaTab';
import TestTab from './components/TestTab';
import type { SkillTemplateDef } from './skillTemplates';
import './SkillEditPage.css';

export interface FormState {
  name: string;
  description: string;
  instructions: string;
  language: string;
  tags: string;
  script_body: string;
  input_schema: Record<string, unknown> | null;
  output_schema: Record<string, unknown> | null;
}

const TABS = [
  { key: 'meta', label: 'META', icon: '📋' },
  { key: 'script', label: 'SCRIPT', icon: '💻' },
  { key: 'schema', label: 'I/O SCHEMA', icon: '🔌' },
  { key: 'test', label: 'TEST', icon: '🧪' },
] as const;

type TabKey = (typeof TABS)[number]['key'];

function emptyForm(): FormState {
  return {
    name: '',
    description: '',
    instructions: '',
    language: 'python',
    tags: '',
    script_body: '',
    input_schema: null,
    output_schema: null,
  };
}

function skillToForm(skill: SkillTemplate): FormState {
  return {
    name: skill.name,
    description: skill.description,
    instructions: skill.instructions,
    language: skill.language,
    tags: Array.isArray(skill.tags) ? skill.tags.join(', ') : '',
    script_body: skill.script_body || '',
    input_schema: skill.input_schema || null,
    output_schema: skill.output_schema || null,
  };
}

export default function SkillEditPage() {
  const { skillId } = useParams<{ skillId: string }>();
  const navigate = useNavigate();
  const isNew = !skillId || skillId === 'new';

  const [form, setForm] = useState<FormState>(emptyForm);
  const [original, setOriginal] = useState<SkillTemplate | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('meta');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) {
      setForm(emptyForm());
      setOriginal(null);
      setLoading(false);
      return;
    }
    const id = parseInt(skillId);
    if (isNaN(id)) return;
    setLoading(true);
    skillApi.get(id)
      .then(skill => {
        setForm(skillToForm(skill));
        setOriginal(skill);
      })
      .catch(e => setError(e?.response?.data?.detail || e?.message || 'Failed to load skill'))
      .finally(() => setLoading(false));
  }, [skillId, isNew]);

  const patch = useCallback((partial: Partial<FormState>) => {
    setForm(prev => ({ ...prev, ...partial }));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const tags = form.tags.split(',').map(t => t.trim()).filter(Boolean);
      if (isNew) {
        const created = await skillApi.create({
          name: form.name,
          description: form.description,
          instructions: form.instructions,
          language: form.language,
          tags,
          script_body: form.script_body || null,
          input_schema: form.input_schema,
          output_schema: form.output_schema,
        });
        navigate(`/skills/${created.id}/edit`, { replace: true });
      } else if (original) {
        const updated = await skillApi.update(original.id, {
          name: form.name || undefined,
          description: form.description || undefined,
          instructions: form.instructions || undefined,
          language: form.language || undefined,
          tags,
          script_body: form.script_body || null,
          input_schema: form.input_schema,
          output_schema: form.output_schema,
        });
        setOriginal(updated);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleApplyTemplate = useCallback((tpl: SkillTemplateDef) => {
    setForm({
      name: form.name || '',
      description: form.description || '',
      instructions: form.instructions || '',
      language: tpl.language,
      tags: form.tags || '',
      script_body: tpl.scriptBody,
      input_schema: tpl.inputSchema,
      output_schema: tpl.outputSchema,
    });
  }, [form.name, form.description, form.instructions, form.tags]);

  if (loading) {
    return (
      <div className="skill-edit-page">
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading skill...
        </div>
      </div>
    );
  }

  const valid = form.name.trim().length > 0 && form.description.trim().length > 0;

  return (
    <div className="skill-edit-page">
      {/* Header */}
      <div className="skill-edit-header">
        <button className="skill-edit-back" onClick={() => navigate('/skills')}>
          ← BACK
        </button>
        <div className="skill-edit-title">
          {isNew ? 'CREATE NEW SKILL' : `EDIT: ${original?.name || ''}`}
          <span className="mode-tag">{isNew ? 'NEW' : `v${original?.version || 1}`}</span>
        </div>
        {error && <span style={{ color: '#ef4444', fontSize: '0.7rem' }}>⚠ {error}</span>}
        <button className="skill-edit-save" onClick={handleSave} disabled={saving || !valid}>
          {saving ? 'SAVING...' : 'SAVE'}
        </button>
      </div>

      {/* Tabs */}
      <div className="skill-edit-tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`skill-edit-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <span className="tab-icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="skill-edit-content">
        {activeTab === 'meta' && <MetaTab form={form} onChange={patch} />}
        {activeTab === 'script' && (
          <ScriptTab
            scriptBody={form.script_body}
            language={form.language}
            skillForExport={original}
            onScriptBodyChange={val => patch({ script_body: val })}
            onLanguageChange={lang => patch({ language: lang })}
            onNameDetect={name => patch({ name })}
            onApplyTemplate={handleApplyTemplate}
          />
        )}
        {activeTab === 'schema' && <SchemaTab form={form} onChange={patch} />}
        {activeTab === 'test' && <TestTab skillId={original?.id ?? null} />}
      </div>
    </div>
  );
}
