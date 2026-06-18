import SchemaEditor from '../../SkillLibraryPage/SchemaEditor';
import type { FormState } from '../SkillEditPage';

interface Props {
  form: FormState;
  onChange: (patch: Partial<FormState>) => void;
}

export default function SchemaTab({ form, onChange }: Props) {
  return (
    <div className="schema-tab">
      <div className="schema-pair">
        <SchemaEditor
          title="📥 INPUT SCHEMA (SkillInput)"
          value={form.input_schema}
          onChange={val => onChange({ input_schema: val })}
        />
        <SchemaEditor
          title="📤 OUTPUT SCHEMA (SkillOutput)"
          value={form.output_schema}
          onChange={val => onChange({ output_schema: val })}
        />
      </div>
    </div>
  );
}
