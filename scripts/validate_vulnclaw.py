#!/usr/bin/env python3
"""
VulnClaw Markdown Validation Script

Validates VulnClaw .md files for:
- Frontmatter structure and required fields
- Section completeness
- Style consistency
- WarStories format
- Reference integrity
- Baseline scan (structure analysis)

Usage:
    python scripts/validate_vulnclaw.py --check-frontmatter
    python scripts/validate_vulnclaw.py --check-sections
    python scripts/validate_vulnclaw.py --check-style
    python scripts/validate_vulnclaw.py --check-warstories
    python scripts/validate_vulnclaw.py --check-refs
    python scripts/validate_vulnclaw.py --all
    python scripts/validate_vulnclaw.py --scan-baseline --output-file .omo/evidence/task-2-baseline.json
"""

import argparse
import json
import os
import re
import sys
import yaml
from typing import Any, Dict, List, Tuple, Optional, Set


# Frontmatter parsing regex (adapted from import_skills.py)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

# Default scan directory
DEFAULT_SCAN_DIR = "apps/auto/VulnClaw/vulnclaw"


def parse_markdown(file_path: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Parse a markdown file, returning (frontmatter_dict, body_str).
    Returns (None, None) on failure.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return None, None

    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return None, None

    yaml_block, body = match.group(1), match.group(2)
    try:
        meta = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError:
        return None, None

    if not isinstance(meta, dict):
        return None, None

    return meta, body


def scan_markdown_files(root_dir: str) -> List[str]:
    """Scan for all .md files under root_dir."""
    md_files = []
    for dirpath, _dirs, filenames in os.walk(root_dir):
        for fname in sorted(filenames):
            if fname.endswith(".md"):
                md_files.append(os.path.join(dirpath, fname))
    md_files.sort()
    return md_files


def make_result(errors: List, warnings: List, files_checked: int) -> Dict[str, Any]:
    """Create standardized result JSON."""
    return {
        "errors": errors,
        "warnings": warnings,
        "files_checked": files_checked,
    }


def check_frontmatter(root_dir: str) -> Dict[str, Any]:
    """Check frontmatter validity for all .md files."""
    errors = []
    warnings = []
    files_checked = 0

    md_files = scan_markdown_files(root_dir)

    for file_path in md_files:
        files_checked += 1
        rel_path = os.path.relpath(file_path, root_dir)

        meta, body = parse_markdown(file_path)
        if meta is None:
            errors.append({
                "file": rel_path,
                "message": "缺少或無法解析 frontmatter"
            })
            continue

        # Check required fields
        required_fields = ["name", "description", "tags"]
        for field in required_fields:
            if field not in meta or not meta[field]:
                errors.append({
                    "file": rel_path,
                    "message": f"frontmatter 缺少必要欄位: {field}"
                })

        # Check tags is a list
        if "tags" in meta and not isinstance(meta["tags"], list):
            warnings.append({
                "file": rel_path,
                "message": "tags 應為列表格式"
            })

        # Check skill_type if present
        if "skill_type" in meta and meta["skill_type"] not in ["skill", "documentation", "reference", "warstory"]:
            warnings.append({
                "file": rel_path,
                "message": f"未知的 skill_type: {meta['skill_type']}"
            })

    return make_result(errors, warnings, files_checked)


def check_sections(root_dir: str) -> Dict[str, Any]:
    """Check section completeness for skill files."""
    errors = []
    warnings = []
    files_checked = 0

    md_files = scan_markdown_files(root_dir)

    for file_path in md_files:
        files_checked += 1
        rel_path = os.path.relpath(file_path, root_dir)

        meta, body = parse_markdown(file_path)
        if meta is None:
            continue

        # Only check skill-type files for section completeness
        skill_type = meta.get("skill_type", "skill")
        if skill_type != "skill":
            continue

        if not body or not body.strip():
            warnings.append({
                "file": rel_path,
                "message": "技能內容為空"
            })

        # Check for common skill sections
        recommended_sections = [
            "## 使用時機",
            "## 核心原理",
            "## 實作步驟",
            "## 注意事項",
        ]

        for section in recommended_sections:
            if body and section not in body:
                warnings.append({
                    "file": rel_path,
                    "message": f"建議包含章節: {section}"
                })

    return make_result(errors, warnings, files_checked)


def check_style(root_dir: str) -> Dict[str, Any]:
    """Check markdown style consistency."""
    errors = []
    warnings = []
    files_checked = 0

    md_files = scan_markdown_files(root_dir)

    for file_path in md_files:
        files_checked += 1
        rel_path = os.path.relpath(file_path, root_dir)

        meta, body = parse_markdown(file_path)
        if meta is None or body is None:
            continue

        lines = body.splitlines()

        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                warnings.append({
                    "file": rel_path,
                    "line": i,
                    "message": "行尾有多餘空白"
                })

        # Check for heading style (ATX style with space)
        for i, line in enumerate(lines, 1):
            if line.startswith("#") and not line.startswith("# "):
                warnings.append({
                    "file": rel_path,
                    "line": i,
                    "message": "標題格式建議使用 '# 標題' (ATX 風格且需空格)"
                })

        # Check for empty file
        if not body.strip():
            warnings.append({
                "file": rel_path,
                "message": "內容為空"
            })

    return make_result(errors, warnings, files_checked)


def check_warstories(root_dir: str) -> Dict[str, Any]:
    """Check WarStories format compliance."""
    errors = []
    warnings = []
    files_checked = 0

    warstory_dir = os.path.join(root_dir, "warstories")
    if not os.path.isdir(warstory_dir):
        return make_result(errors, warnings, 0)

    md_files = scan_markdown_files(warstory_dir)

    for file_path in md_files:
        files_checked += 1
        rel_path = os.path.relpath(file_path, root_dir)

        meta, body = parse_markdown(file_path)
        if meta is None:
            errors.append({
                "file": rel_path,
                "message": "缺少或無法解析 frontmatter"
            })
            continue

        # WarStories should have specific frontmatter fields
        required_warstory_fields = ["name", "description", "tags", "date", "cve"]
        for field in required_warstory_fields:
            if field not in meta or not meta[field]:
                warnings.append({
                    "file": rel_path,
                    "message": f"WarStory 建議包含欄位: {field}"
                })

        # Check filename format: YYYY-MM-DD_slug.md
        filename = os.path.basename(file_path)
        if not re.match(r"^\d{4}-\d{2}-\d{2}_.+\.md$", filename):
            warnings.append({
                "file": rel_path,
                "message": "檔名格式建議: YYYY-MM-DD_描述.md"
            })

    return make_result(errors, warnings, files_checked)


def check_refs(root_dir: str) -> Dict[str, Any]:
    """Check reference integrity (links, cross-refs)."""
    errors = []
    warnings = []
    files_checked = 0

    md_files = scan_markdown_files(root_dir)

    # Build index of all files for cross-reference checking
    file_index = {}
    for file_path in md_files:
        rel_path = os.path.relpath(file_path, root_dir)
        meta, _ = parse_markdown(file_path)
        if meta and "name" in meta:
            file_index[meta["name"]] = rel_path

    for file_path in md_files:
        files_checked += 1
        rel_path = os.path.relpath(file_path, root_dir)

        meta, body = parse_markdown(file_path)
        if meta is None or body is None:
            continue

        # Check markdown links [text](path)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        for match in link_pattern.finditer(body):
            link_text, link_target = match.groups()

            # Skip external links
            if link_target.startswith(("http://", "https://", "mailto:")):
                continue

            # Check local file references
            if link_target.endswith(".md"):
                # Resolve relative to current file
                current_dir = os.path.dirname(file_path)
                target_path = os.path.normpath(os.path.join(current_dir, link_target))
                if not os.path.exists(target_path):
                    warnings.append({
                        "file": rel_path,
                        "message": f"引用的檔案不存在: {link_target}"
                    })

        # Check for skill references by name (e.g., "see waf-bypass skill")
        for skill_name, skill_path in file_index.items():
            if skill_name in body and skill_name != meta.get("name"):
                # Just a warning that there's a potential reference
                pass

    return make_result(errors, warnings, files_checked)


def run_all_checks(root_dir: str) -> Dict[str, Any]:
    """Run all checks and aggregate results."""
    all_errors = []
    all_warnings = []
    total_files = 0

    checks = [
        ("frontmatter", check_frontmatter),
        ("sections", check_sections),
        ("style", check_style),
        ("warstories", check_warstories),
        ("refs", check_refs),
    ]

    for check_name, check_func in checks:
        result = check_func(root_dir)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        total_files = max(total_files, result["files_checked"])

    return make_result(all_errors, all_warnings, total_files)


def scan_baseline(root_dir: str) -> Dict[str, Any]:
    """Scan all .md files and generate baseline structure report."""
    md_files = scan_markdown_files(root_dir)
    files_data = []

    for file_path in md_files:
        rel_path = os.path.relpath(file_path, root_dir)
        meta, body = parse_markdown(file_path)

        if meta is None or body is None:
            files_data.append({
                "file": rel_path,
                "frontmatter": {},
                "sections": [],
                "table_count": 0,
                "code_block_count": 0,
                "internal_references": [],
                "parse_error": True
            })
            continue

        # Extract sections (headings)
        sections = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                sections.append(stripped)

        # Count tables (markdown tables with |---| pattern)
        table_count = 0
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if "|" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.match(r"^\s*\|?\s*:?-+:?\s*\|", next_line):
                    table_count += 1
                    # Skip to end of table
                    i += 2
                    while i < len(lines) and "|" in lines[i]:
                        i += 1
                    continue
            i += 1

        # Count code blocks (```...```)
        code_block_count = 0
        in_code_block = False
        for line in body.splitlines():
            if line.strip().startswith("```"):
                if not in_code_block:
                    code_block_count += 1
                    in_code_block = True
                else:
                    in_code_block = False

        # Extract internal references (markdown links to .md files)
        internal_refs = []
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        for match in link_pattern.finditer(body):
            link_text, link_target = match.groups()
            if link_target.endswith(".md") and not link_target.startswith(("http://", "https://")):
                internal_refs.append({
                    "text": link_text,
                    "target": link_target
                })

        files_data.append({
            "file": rel_path,
            "frontmatter": meta,
            "sections": sections,
            "table_count": table_count,
            "code_block_count": code_block_count,
            "internal_references": internal_refs,
            "parse_error": False
        })

    return {
        "total_files": len(md_files),
        "files": files_data
    }


def main():
    parser = argparse.ArgumentParser(
        description="VulnClaw Markdown Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_vulnclaw.py --check-frontmatter
  python scripts/validate_vulnclaw.py --all
  python scripts/validate_vulnclaw.py --check-sections --check-style
        """
    )

    parser.add_argument(
        "--check-frontmatter",
        action="store_true",
        help="Validate frontmatter structure and required fields"
    )
    parser.add_argument(
        "--check-sections",
        action="store_true",
        help="Validate section completeness for skill files"
    )
    parser.add_argument(
        "--check-style",
        action="store_true",
        help="Validate markdown style consistency"
    )
    parser.add_argument(
        "--check-warstories",
        action="store_true",
        help="Validate WarStories format compliance"
    )
    parser.add_argument(
        "--check-refs",
        action="store_true",
        help="Validate reference integrity (links, cross-refs)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all checks"
    )
    parser.add_argument(
        "--dir",
        default=DEFAULT_SCAN_DIR,
        help=f"Root directory to scan (default: {DEFAULT_SCAN_DIR})"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--scan-baseline",
        action="store_true",
        help="Scan all .md files and generate baseline structure report"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file path for baseline scan (default: stdout)"
    )

    args = parser.parse_args()

    # Handle baseline scan (independent of other checks)
    if args.scan_baseline:
        root_dir = args.dir
        if not os.path.isdir(root_dir):
            print(json.dumps({"errors": [f"目錄不存在: {root_dir}"], "warnings": [], "files_checked": 0}), file=sys.stderr)
            sys.exit(1)
        
        baseline_result = scan_baseline(root_dir)
        output_json = json.dumps(baseline_result, ensure_ascii=False, indent=2)
        
        if args.output_file:
            os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output_json)
        else:
            print(output_json)
        sys.exit(0)

    # Determine which checks to run
    run_checks = {
        "frontmatter": args.check_frontmatter or args.all,
        "sections": args.check_sections or args.all,
        "style": args.check_style or args.all,
        "warstories": args.check_warstories or args.all,
        "refs": args.check_refs or args.all,
    }

    if not any(run_checks.values()):
        parser.print_help()
        sys.exit(1)

    root_dir = args.dir
    if not os.path.isdir(root_dir):
        print(json.dumps({"errors": [f"目錄不存在: {root_dir}"], "warnings": [], "files_checked": 0}), file=sys.stderr)
        sys.exit(1)

    # Run selected checks
    all_errors = []
    all_warnings = []
    total_files = 0

    if run_checks["frontmatter"]:
        result = check_frontmatter(root_dir)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        total_files = max(total_files, result["files_checked"])

    if run_checks["sections"]:
        result = check_sections(root_dir)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        total_files = max(total_files, result["files_checked"])

    if run_checks["style"]:
        result = check_style(root_dir)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        total_files = max(total_files, result["files_checked"])

    if run_checks["warstories"]:
        result = check_warstories(root_dir)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        total_files = max(total_files, result["files_checked"])

    if run_checks["refs"]:
        result = check_refs(root_dir)
        all_errors.extend(result["errors"])
        all_warnings.extend(result["warnings"])
        total_files = max(total_files, result["files_checked"])

    # Output result
    result = make_result(all_errors, all_warnings, total_files)

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Text output
        print(f"Files checked: {total_files}")
        print(f"Errors: {len(all_errors)}")
        print(f"Warnings: {len(all_warnings)}")
        for err in all_errors:
            print(f"  ERROR: {err}")
        for warn in all_warnings:
            print(f"  WARNING: {warn}")

    # Exit with error code if any errors
    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()