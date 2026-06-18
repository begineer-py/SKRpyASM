import type { SkillTemplate } from '../services/skillApi';

export function downloadBlob(content: string, filename: string, mime: string = 'text/plain') {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function exportScript(skill: { name: string; language: string; script_content?: string | null; script_body?: string | null }) {
  const ext = skill.language === 'bash' ? 'sh' : 'py';
  const content = skill.script_content || skill.script_body || '';
  downloadBlob(content, `${skill.name}.${ext}`);
}

export function exportSkillJson(skill: SkillTemplate) {
  const payload = {
    name: skill.name,
    description: skill.description,
    instructions: skill.instructions,
    language: skill.language,
    tags: skill.tags,
    script_body: skill.script_body,
    input_schema: skill.input_schema,
    output_schema: skill.output_schema,
    test_input_example: skill.test_input_example,
    _export_version: 1,
    _exported_at: new Date().toISOString(),
  };
  downloadBlob(JSON.stringify(payload, null, 2), `${skill.name}.skill.json`, 'application/json');
}

export function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

export function extractScriptBody(text: string): string {
  const mainIdx = text.indexOf('def main(');
  return mainIdx >= 0 ? text.slice(mainIdx).trim() : text.trim();
}

export function detectLanguage(filename: string): string {
  return filename.endsWith('.sh') ? 'bash' : 'python';
}
