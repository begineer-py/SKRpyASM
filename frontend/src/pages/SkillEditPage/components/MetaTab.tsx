import type { FormState } from '../SkillEditPage';

interface Props {
  form: FormState;
  onChange: (patch: Partial<FormState>) => void;
}

export default function MetaTab({ form, onChange }: Props) {
  return (
    <div className="meta-form">
      <div className="meta-field">
        <label>Name <span style={{ color: '#ef4444' }}>*</span></label>
        <input
          type="text"
          value={form.name}
          onChange={e => onChange({ name: e.target.value })}
          placeholder="kebab-case: django-csrf-bypass"
        />
        <div className="field-hint">Only lowercase letters, numbers, and hyphens. Used as filename.</div>
      </div>

      <div className="meta-field">
        <label>Description <span style={{ color: '#ef4444' }}>*</span></label>
        <textarea
          value={form.description}
          onChange={e => onChange({ description: e.target.value })}
          placeholder="Short description for RAG retrieval (max 500 chars)"
          maxLength={500}
        />
        <div className={`char-count ${form.description.length > 500 ? 'over' : ''}`}>
          {form.description.length}/500
        </div>
      </div>

      <div className="meta-field">
        <label>Language</label>
        <select value={form.language} onChange={e => onChange({ language: e.target.value })}>
          <option value="python">Python</option>
          <option value="bash">Bash</option>
        </select>
        {form.language === 'bash' && (
          <div style={{
            marginTop: 6, padding: '8px 12px', borderRadius: 4, fontSize: '0.72rem',
            background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)',
            color: '#f59e0b', lineHeight: 1.5,
          }}>
            ⚠ Bash skills bypass the I/O Contract entirely — no Pydantic validation, no <code>_emit_output()</code>.
            Input arrives as JSON in <code>$1</code>; output via stdout. Schemas in the I/O SCHEMA tab will be ignored.
          </div>
        )}
      </div>

      <div className="meta-field">
        <label>Tags (comma-separated)</label>
        <input
          type="text"
          value={form.tags}
          onChange={e => onChange({ tags: e.target.value })}
          placeholder="django, csrf, bypass"
        />
        <div className="field-hint">Used for filtering and discovery in the skill library.</div>
      </div>

      <div className="meta-field">
        <label>Instructions</label>
        <textarea
          value={form.instructions}
          onChange={e => onChange({ instructions: e.target.value })}
          placeholder="How to use this skill, parameter details, usage examples..."
          maxLength={2000}
          rows={5}
        />
        <div className={`char-count ${form.instructions.length > 2000 ? 'over' : ''}`}>
          {form.instructions.length}/2000
        </div>
        <div className="field-hint">Similar to SKILL.md — guides the AI on proper usage.</div>
      </div>
    </div>
  );
}
