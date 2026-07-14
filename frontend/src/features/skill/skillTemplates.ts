export interface SkillTemplateDef {
  id: string;
  name: string;
  icon: string;
  description: string;
  language: 'python' | 'bash';
  scriptBody: string;
  inputSchema: Record<string, unknown> | null;
  outputSchema: Record<string, unknown> | null;
}

export const SKILL_TEMPLATES: SkillTemplateDef[] = [
  {
    id: 'python-full',
    name: 'Python + I/O Schema',
    icon: '🐍',
    description: 'Standard skill with validated input and structured output. The most common pattern.',
    language: 'python',
    scriptBody: `import requests


def main(inputs: SkillInput) -> None:
    # Access validated inputs via inputs.<field_name>
    url = inputs.target_url

    resp = requests.get(url, timeout=10)
    title = ""
    if "<title>" in resp.text:
        start = resp.text.index("<title>") + 7
        end = resp.text.index("</title>", start)
        title = resp.text[start:end].strip()

    # Emit output — keys MUST match your output schema
    _emit_output({
        "url": url,
        "status_code": resp.status_code,
        "title": title,
    })
`,
    inputSchema: {
      type: "object",
      properties: {
        target_url: {
          type: "string",
          pattern: "^https?://.+",
          description: "Target URL to fetch",
        },
      },
      required: ["target_url"],
    },
    outputSchema: {
      type: "object",
      properties: {
        url: { type: "string", description: "The URL that was fetched" },
        status_code: { type: "integer", description: "HTTP status code" },
        title: { type: "string", description: "Page title (empty if not found)" },
      },
      required: ["url", "status_code", "title"],
    },
  },
  {
    id: 'python-no-schema',
    name: 'Python (No Schema)',
    icon: '⚡',
    description: 'Minimal skill with no input/output validation. Use _emit_output() with any shape.',
    language: 'python',
    scriptBody: `def main() -> None:
    # No inputs parameter — no input_schema defined.
    # Emit any output shape you like via _emit_output().
    _emit_output({
        "message": "Hello from skill",
        "ok": True,
    })
`,
    inputSchema: null,
    outputSchema: null,
  },
  {
    id: 'python-helper',
    name: 'Python + Helper Functions',
    icon: '🔧',
    description: 'Shows how to define helper functions outside main(). Useful for complex logic.',
    language: 'python',
    scriptBody: `import requests
from bs4 import BeautifulSoup


def fetch_csrf_token(url: str, session: requests.Session) -> str:
    """Helper functions are allowed before main()."""
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    token_el = soup.find("input", {"name": "csrfmiddlewaretoken"})
    return token_el["value"] if token_el else ""


def main(inputs: SkillInput) -> None:
    session = requests.Session()
    token = fetch_csrf_token(inputs.url, session)

    _emit_output({
        "csrf_token": token,
        "success": bool(token),
    })
`,
    inputSchema: {
      type: "object",
      properties: {
        url: {
          type: "string",
          pattern: "^https?://.+",
          description: "Target URL to fetch CSRF token from",
        },
      },
      required: ["url"],
    },
    outputSchema: {
      type: "object",
      properties: {
        csrf_token: { type: "string", description: "Extracted CSRF token (empty if not found)" },
        success: { type: "boolean", description: "True if a token was found" },
      },
      required: ["csrf_token", "success"],
    },
  },
  {
    id: 'bash-raw',
    name: 'Bash (Raw Script)',
    icon: '📜',
    description: 'Bash skills bypass the I/O Contract entirely. Use $1 for JSON input, echo for output.',
    language: 'bash',
    scriptBody: `#!/usr/bin/env bash
# Bash skills: NO Pydantic validation, NO _emit_output().
# Input arrives as JSON in $1. Output goes to stdout.
target="\${1:-127.0.0.1}"

echo "Scanning \$target..."
nmap -sV -p 80,443,8080 "\$target"
`,
    inputSchema: null,
    outputSchema: null,
  },
  {
    id: 'empty',
    name: 'Empty (Start from Scratch)',
    icon: '📄',
    description: 'Begin with a blank canvas. Remember: main() is required for Python skills.',
    language: 'python',
    scriptBody: `def main(inputs: SkillInput) -> None:
    # Your code here
    # Use inputs.<field_name> to access validated inputs
    # Call _emit_output({...}) to return results
    pass
`,
    inputSchema: null,
    outputSchema: null,
  },
];
