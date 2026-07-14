import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface SchemaField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  pattern: string;
  minLength: string;
  maxLength: string;
  minimum: string;
  maximum: string;
  default: string;
  enumValues?: string;
}

interface Props {
  title: string;
  value: Record<string, unknown> | null;
  onChange: (schema: Record<string, unknown>) => void;
}

interface SchemaProperty {
  type?: string;
  description?: string;
  pattern?: string;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  default?: unknown;
  enum?: unknown[];
}

const FIELD_TYPES = [
  'string', 'integer', 'number', 'boolean', 'array', 'object',
];

function schemaToFields(schema: Record<string, unknown> | null): SchemaField[] {
  if (!schema || typeof schema !== 'object') return [];
  const props = (schema.properties as Record<string, SchemaProperty> | undefined) ?? {};
  const required = Array.isArray(schema.required) ? schema.required.filter((item): item is string => typeof item === 'string') : [];
  return Object.entries(props).map(([name, prop]) => ({
    name,
    type: prop.type || 'string',
    required: required.includes(name),
    description: prop.description || '',
    pattern: prop.pattern || '',
    minLength: prop.minLength !== undefined ? String(prop.minLength) : '',
    maxLength: prop.maxLength !== undefined ? String(prop.maxLength) : '',
    minimum: prop.minimum !== undefined ? String(prop.minimum) : '',
    maximum: prop.maximum !== undefined ? String(prop.maximum) : '',
    default: prop.default !== undefined ? String(prop.default) : '',
    enumValues: Array.isArray(prop.enum) ? prop.enum.map((v) => String(v)).join(',') : '',
  }));
}

function fieldsToSchema(fields: SchemaField[]): Record<string, unknown> {
  const properties: Record<string, unknown> = {};
  const required: string[] = [];
  for (const f of fields) {
    const prop: Record<string, unknown> = { type: f.type };
    if (f.description) prop.description = f.description;
    const enumList = f.enumValues
      ? f.enumValues.split(',').map(s => s.trim()).filter(Boolean)
      : [];
    if (enumList.length > 0) {
      prop.enum = enumList;
    } else {
      if (f.pattern && f.type === 'string') prop.pattern = f.pattern;
      if (f.minLength && f.type === 'string') prop.minLength = Number(f.minLength);
      if (f.maxLength && f.type === 'string') prop.maxLength = Number(f.maxLength);
      if (f.minimum && (f.type === 'integer' || f.type === 'number')) prop.minimum = f.type === 'integer' ? parseInt(f.minimum) : parseFloat(f.minimum);
      if (f.maximum && (f.type === 'integer' || f.type === 'number')) prop.maximum = f.type === 'integer' ? parseInt(f.maximum) : parseFloat(f.maximum);
    }
    if (f.default) {
      const val = f.default.trim();
      if (f.type === 'integer') prop.default = parseInt(val);
      else if (f.type === 'number') prop.default = parseFloat(val);
      else if (f.type === 'boolean') prop.default = val.toLowerCase() === 'true';
      else prop.default = val;
    }
    properties[f.name] = prop;
    if (f.required) required.push(f.name);
  }
  const schema: Record<string, unknown> = { type: 'object', properties };
  if (required.length > 0) schema.required = required;
  return schema;
}

export default function SchemaEditor({ title, value, onChange }: Props) {
  const [fields, setFields] = useState<SchemaField[]>(() => schemaToFields(value));
  const [showJson, setShowJson] = useState(false);

  useEffect(() => {
    setFields(schemaToFields(value));
  }, [value]);

  const emitChange = useCallback((newFields: SchemaField[]) => {
    onChange(fieldsToSchema(newFields));
  }, [onChange]);

  const updateField = (i: number, patch: Partial<SchemaField>) => {
    setFields(prev => {
      const next = prev.map((f, idx) => idx === i ? { ...f, ...patch } : f);
      emitChange(next);
      return next;
    });
  };

  const removeField = (i: number) => {
    setFields(prev => {
      const next = prev.filter((_, idx) => idx !== i);
      emitChange(next);
      return next;
    });
  };

  const addField = () => {
    setFields(prev => {
      const next = [...prev, {
        name: '', type: 'string', required: false, description: '',
        pattern: '', minLength: '', maxLength: '', minimum: '', maximum: '', default: '',
        enumValues: '',
      }];
      emitChange(next);
      return next;
    });
  };

  const showNumeric = (f: SchemaField) => f.type === 'integer' || f.type === 'number';
  const showString = (f: SchemaField) => f.type === 'string';
  const hasEnum = (f: SchemaField) => !!(f.enumValues && f.enumValues.trim());

  const jsonPreview = JSON.stringify(fieldsToSchema(fields), null, 2);

  return (
    <div className="schema-editor">
      <div className="flex justify-between items-center">
        <div className="schema-editor-title">{title}</div>
        <button
          className="schema-field-add py-0.5 px-2 text-[0.7rem]"
          onClick={() => setShowJson(s => !s)}
        >
          {showJson ? 'Hide JSON' : 'View JSON'}
        </button>
      </div>
      <div className="text-[0.7rem] text-[#94a3b8] mb-2">
        Types: string&rarr;str, integer&rarr;int, number&rarr;float, boolean&rarr;bool, array&rarr;list, object&rarr;dict
      </div>
      {showJson && (
        <pre className="bg-black/40 text-[#94a3b8] p-2 rounded text-[0.7rem] font-mono mb-2 overflow-x-auto max-h-60 whitespace-pre-wrap break-words">
          {jsonPreview}
        </pre>
      )}
      {fields.length === 0 && (
        <div className="schema-editor-empty">No fields defined.</div>
      )}
      {fields.map((f, i) => (
        <div key={i} className="schema-field-row">
          <div className="schema-field-line">
            <input
              type="text"
              className="schema-field-name"
              placeholder="field_name"
              value={f.name}
              onChange={e => updateField(i, { name: e.target.value })}
            />
            <select
              className="schema-field-type"
              value={f.type}
              onChange={e => updateField(i, { type: e.target.value })}
            >
              {FIELD_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <label className="schema-field-req">
              <input
                type="checkbox"
                checked={f.required}
                onChange={e => updateField(i, { required: e.target.checked })}
              />
              required
            </label>
            <button className="schema-field-remove" onClick={() => removeField(i)}>✕</button>
          </div>
          <div className="schema-field-line">
            <input
              type="text"
              className="schema-field-desc"
              placeholder="description"
              value={f.description}
              onChange={e => updateField(i, { description: e.target.value })}
            />
            {showString(f) && (
              <input
                type="text"
                className={cn("schema-field-pattern", hasEnum(f) && 'opacity-50')}
                placeholder="pattern (regex)"
                value={f.pattern}
                disabled={hasEnum(f)}
              onChange={e => updateField(i, { pattern: e.target.value })}
              />
            )}
            {showString(f) && (
              <>
                <input
                  type="number"
                  className={cn("schema-field-minmax", hasEnum(f) && 'opacity-50')}
                  placeholder="min len"
                  value={f.minLength}
                  disabled={hasEnum(f)}
                  onChange={e => updateField(i, { minLength: e.target.value })}
                />
                <input
                  type="number"
                  className={cn("schema-field-minmax", hasEnum(f) && 'opacity-50')}
                  placeholder="max len"
                  value={f.maxLength}
                  disabled={hasEnum(f)}
                  onChange={e => updateField(i, { maxLength: e.target.value })}
                />
              </>
            )}
            {showNumeric(f) && (
              <>
                <input
                  type="number"
                  className="schema-field-minmax"
                  placeholder="min"
                  value={f.minimum}
                  onChange={e => updateField(i, { minimum: e.target.value })}
                />
                <input
                  type="number"
                  className="schema-field-minmax"
                  placeholder="max"
                  value={f.maximum}
                  onChange={e => updateField(i, { maximum: e.target.value })}
                />
              </>
            )}
            <input
              type="text"
              className="schema-field-default"
              placeholder="default"
              value={f.default}
              onChange={e => updateField(i, { default: e.target.value })}
            />
          </div>
          <div className="schema-field-line">
            <input
              type="text"
              className="schema-field-pattern"
              placeholder="enum: val1,val2,val3"
              value={f.enumValues || ''}
              onChange={e => updateField(i, { enumValues: e.target.value })}
            />
          </div>
        </div>
      ))}
      <button className="schema-field-add" onClick={addField}>+ Add Field</button>
    </div>
  );
}
