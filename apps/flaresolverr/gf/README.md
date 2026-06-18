# [PROJECT_NAME] - The Hacker's Girlfriend

_A Pure Python, `grep`-free, spiritual successor to `gf` (Grep-Frick)._

She understands you. She's reliable. She's system-agnostic. And she brings back structured reports, not just messy text. She's the partner every hacker, pentester, and code auditor deserves.

This project was born out of a deep respect and heavy usage of the brilliant [gf](https://github.com/tomnomnom/gf) by tomnomnom. We stand on the shoulders of a giant.

## What? Why? (Our Story)

The original `gf` solved a huge problem: typing complex, error-prone `grep` patterns is a pain in the ass. It gives names to your regular expressions so you can fire them off quickly.

We used it. We loved it. But then, as we tried to integrate it deeper into automated systems (like a C2 framework), we ran into a new set of problems. **The tool itself became the problem.**

- **`grep` Hell:** Is the target machine running GNU `grep` or BSD `grep`? The behavior is different. Does it even have `grep`?
- **External Dependencies:** It's written in Go. This means you need a Go compiler to build it, or you need to pre-compile binaries for every single target architecture you might encounter.
- **Unstructured Output:** `grep` just screams lines of text. For a human, this is fine. For a machine trying to parse the results, it's a nightmare. Where did the match start? Which pattern found it?
- **Integration Pain:** You can't `import gf` into a Python project. You have to call it as a subprocess, which is slow, clumsy, and fragile.

We decided to take the brilliant **soul** of `gf` and forge it into a new body. A body made of pure Python, designed from the ground up for reliability, portability, and most importantly, **intelligent, structured output**.

## Key Differences & Philosophy

This isn't just a clone. It's an evolution.

- **Pure Fucking Python:** Zero external dependencies besides Python 3 itself. No more `grep`. No more Go. If the target has Python, it runs. Period.
- **Structured JSON Output:** This is the game-changer. It doesn't just print matching lines. It returns a detailed JSON object containing which pattern matched, where it matched (line, start, end), and the matched content. It's built for machines, not just for human eyes.
- **System Agnostic:** Because we use Python's built-in `re` engine, our patterns behave **exactly the same** on Windows, macOS, Linux, or whatever the hell else you're running Python on. No more `grep` version insanity.
- **Integration Ready:** It's built as a `class`. You can run it from the command line, or you can `import PatternAnalyzer` directly into your own projects and use it as a powerful analysis library.
- **Self-Contained:** The patterns live in a `patterns/` directory right next to the script. No more hunting for them in `~/.gf`. You clone the repo, you have the engine and all its ammunition, ready to go.

## Installation

It doesn't get easier than this.

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/your-project-name.git
    cd your-project-name
    ```
2.  That's it. You're ready to go. You can optionally put the script in your `PATH`.

## Usage

The engine is designed to be simple and powerful. It works with files or piped input.

#### List all available patterns:

```bash
▶ ./pygf_engine.py --list
aws-keys
cloud-keys
dev-comments
...
```

#### Run a single pattern on piped input:

```bash
▶ cat ultimate_test_target.js | ./pygf_engine.py sec
```

#### Run ALL patterns on piped input (The "Annihilation" Mode):

```bash
▶ cat ultimate_test_target.js | ./pygf_engine.py all
```

This will return a beautifully structured JSON report, perfect for piping into tools like `jq` or being sent back to a C2 server.

**Example Output:**

```json
{
  "source": "stdin",
  "analysis": [
    {
      "pattern": "cloud-keys",
      "matches": [
        {
          "line": 21,
          "match": "[REDACTED_GOOGLE_EXAMPLE]",
          "start": 17,
          "end": 58
        }
      ],
      "count": 1
    },
    {
      "pattern": "dev-comments",
      "matches": [
        {
          "line": 5,
          "match": "TODO",
          "start": 3,
          "end": 7
        }
      ],
      "count": 1
    }
  ]
}
```

## Pattern Files

The heart of this engine is the `patterns/` directory. Each `.json` file is a self-contained "bullet" with two main components:

- `"flags"`: A string containing characters to modify the regex engine's behavior (e.g., `"i"` for case-insensitive, `"o"` for only-matching).
- `"pattern"` or `"patterns"`: A single regex string or a list of regex strings.

**Example (`ip.json`):**

```json
{
  "flags": "-o",
  "pattern": "(?<![0-9])(?:(?:25[0-5]|...)(?![0-9])"
}
```

## Contributing - Let's Build This Arsenal Together

This is where the real magic happens. We've built the gun; now we need the community to help us make the best fucking ammunition on the planet.

**We want your brilliant patterns.**

If you have a regular expression you use all the time to find cool shit, we want it.

**How to contribute:**

1.  **Fork** the repository.
2.  Create your new `your-awesome-pattern.json` file in the `patterns/` directory.
3.  Test your pattern against real-world data. Make sure it works and doesn't have too many false positives.
4.  Submit a **Pull Request**.

Let's build the most badass, community-driven, regular expression arsenal on the planet.
