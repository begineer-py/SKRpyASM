import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { skillApi } from '../services/skillApi';
import type { SkillTemplate } from '../services/skillApi';
import MetaTab from '../components/MetaTab';
import ScriptTab from '../components/ScriptTab';
import SchemaTab from '../components/SchemaTab';
import TestTab from '../components/TestTab';
import type { SkillTemplateDef } from '../skillTemplates';
import { cn } from '@/lib/utils';

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
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Failed to load skill'))
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
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed');
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
      <div className="c2-workspace c2-workspace--skill bg-bg-base text-text-primary">
        <div className="p-12 text-center text-text-muted">
          Loading skill...
        </div>
      </div>
    );
  }

  const valid = form.name.trim().length > 0 && form.description.trim().length > 0;

  return (
    <div className="c2-workspace c2-workspace--skill bg-bg-base text-text-primary">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-3 bg-bg-surface border-b border-border-subtle shrink-0 z-10">
        <button className="bg-transparent border-0 text-text-muted cursor-pointer text-sm px-[10px] py-1.5 rounded transition-all duration-150 hover:text-text-primary hover:bg-bg-card" onClick={() => navigate('/skills')}>
          ← BACK
        </button>
        <div className="flex-1 text-[0.9rem] font-bold tracking-wider text-text-cyan">
          {isNew ? 'CREATE NEW SKILL' : `EDIT: ${original?.name || ''}`}
          <span className="text-green text-xs bg-green/[0.16] px-2 py-0.5 rounded-sm ml-2">{isNew ? 'NEW' : `v${original?.version || 1}`}</span>
        </div>
        {error && <span className="text-red text-xs">⚠ {error}</span>}
        <button className="px-6 py-[7px] rounded bg-green/[0.12] border border-green/30 text-green text-xs font-bold tracking-wider cursor-pointer transition-all duration-150 hover:bg-green/20 disabled:opacity-40 disabled:cursor-not-allowed" onClick={handleSave} disabled={saving || !valid}>
          {saving ? 'SAVING...' : 'SAVE'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex px-6 bg-bg-surface border-b border-border-subtle shrink-0">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={cn(
              "px-5 py-[10px] bg-transparent border-0 border-b-2 border-transparent text-text-muted text-xs font-semibold tracking-wider cursor-pointer transition-all duration-200 hover:text-text-primary hover:bg-bg-card/50",
              activeTab === tab.key && "text-green border-b-green"
            )}
            onClick={() => setActiveTab(tab.key)}
          >
            <span className="mr-1.5">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
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
