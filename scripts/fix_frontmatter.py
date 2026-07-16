#!/usr/bin/env python3
"""
Fix frontmatter for all 55 VulnClaw skill .md files.

Requirements:
- name: kebab-case, no leading numbers
- description: single line, <= 120 chars
- tags: array, lowercase, no spaces
- skill_type: only "documentation", "script", "hybrid" (all skills are documentation)
- short_description: optional, single line, <= 80 chars (truncated from description)

Must preserve body content unchanged.
"""

import os
import re
import yaml
from pathlib import Path

# Frontmatter parsing regex
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

SKILLS_DIR = "apps/auto/VulnClaw/vulnclaw/skills"

# Files that need name fixing (have leading numbers or non-kebab-case)
NAME_FIXES = {
    "08-rapid-checklists-and-payloads": "rapid-checklists-and-payloads",
    "web-security-integrated": "web-security-integrated-pentest",  # differentiate from advanced
    "web-security-integrated": "web-security-integrated-advanced",  # differentiate from pentest
}

# Actually, let's just use the filename-based kebab-case name (without .md)
# and ensure no leading numbers

def to_kebab_case(name: str) -> str:
    """Convert name to kebab-case, remove leading numbers."""
    # Remove leading numbers and dashes
    name = re.sub(r'^\d+[-_\s]*', '', name)
    # Replace spaces, underscores with dashes
    name = re.sub(r'[\s_]+', '-', name)
    # Lowercase
    name = name.lower()
    # Remove any non-alphanumeric except dash
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Collapse multiple dashes
    name = re.sub(r'-+', '-', name)
    # Strip leading/trailing dashes
    name = name.strip('-')
    return name

def truncate_description(desc: str, max_len: int) -> str:
    """Truncate description to max_len, single line."""
    # Replace newlines with spaces
    desc = ' '.join(desc.split())
    # Truncate
    if len(desc) > max_len:
        desc = desc[:max_len].rstrip()
        # Ensure we don't cut mid-word if possible
        last_space = desc.rfind(' ')
        if last_space > max_len * 0.8:  # Only if not too short
            desc = desc[:last_space]
    return desc

def fix_tags(tags) -> list:
    """Ensure tags are lowercase, no spaces, array format."""
    if isinstance(tags, str):
        # Parse comma-separated or space-separated
        tags = [t.strip() for t in re.split(r'[,\s]+', tags) if t.strip()]
    elif not isinstance(tags, list):
        tags = []
    
    fixed = []
    for tag in tags:
        tag = str(tag).strip().lower()
        # Replace spaces with dashes
        tag = re.sub(r'\s+', '-', tag)
        # Remove non-alphanumeric except dash
        tag = re.sub(r'[^a-z0-9-]', '', tag)
        if tag and tag not in fixed:
            fixed.append(tag)
    return fixed

def parse_markdown(file_path: str):
    """Parse markdown file, return (frontmatter_dict, body_str)."""
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

def write_markdown(file_path: str, meta: dict, body: str):
    """Write markdown file with frontmatter and body."""
    # Ensure required fields in specific order
    ordered_keys = ['name', 'description', 'tags', 'skill_type', 'short_description']
    
    # Build frontmatter dict with ordered keys first, then any extras
    fm_dict = {}
    for key in ordered_keys:
        if key in meta:
            fm_dict[key] = meta[key]
    # Add any other keys
    for key, val in meta.items():
        if key not in fm_dict:
            fm_dict[key] = val
    
    # Dump YAML
    yaml_str = yaml.dump(fm_dict, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    # Write file
    body_str = body if body is not None else ""
    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write("---\n")
        fh.write(yaml_str)
        fh.write("---\n")
        fh.write(body_str)

def main():
    skills_dir = Path(SKILLS_DIR)
    md_files = sorted(skills_dir.rglob("*.md"))
    
    print(f"Found {len(md_files)} .md files")
    
    modified_count = 0
    
    for file_path in md_files:
        # Skip warstories directory
        if "warstories" in file_path.parts:
            print(f"Skipping warstory: {file_path}")
            continue
            
        rel_path = file_path.relative_to(skills_dir)
        print(f"\nProcessing: {rel_path}")
        
        meta, body = parse_markdown(str(file_path))
        if meta is None or body is None:
            print(f"  ERROR: Could not parse frontmatter")
            continue
        
        original_meta = meta.copy()
        changes = []
        
        # 1. Fix name: kebab-case from filename (without .md), no leading numbers
        filename_stem = file_path.stem
        new_name = to_kebab_case(filename_stem)
        if meta.get('name') != new_name:
            meta['name'] = new_name
            changes.append(f"name: '{original_meta.get('name')}' -> '{new_name}'")
        
        # 2. Fix description: single line, <= 120 chars
        old_desc = meta.get('description', '')
        new_desc = truncate_description(old_desc, 120)
        if old_desc != new_desc:
            meta['description'] = new_desc
            changes.append(f"description: truncated to {len(new_desc)} chars")
        
        # 3. Fix tags: lowercase, no spaces, array
        old_tags = meta.get('tags', [])
        new_tags = fix_tags(old_tags)
        if old_tags != new_tags:
            meta['tags'] = new_tags
            changes.append(f"tags: {old_tags} -> {new_tags}")
        
        # 4. Ensure skill_type is "documentation" (all skills are documentation)
        if meta.get('skill_type') != 'documentation':
            old_st = meta.get('skill_type')
            meta['skill_type'] = 'documentation'
            changes.append(f"skill_type: '{old_st}' -> 'documentation'")
        elif 'skill_type' not in meta:
            meta['skill_type'] = 'documentation'
            changes.append("skill_type: added 'documentation'")
        
        # 5. Fix short_description: single line, <= 80 chars (from description)
        if 'short_description' in meta:
            old_short = meta.get('short_description', '')
            new_short = truncate_description(meta['description'], 80)
            if old_short != new_short:
                meta['short_description'] = new_short
                changes.append(f"short_description: truncated to {len(new_short)} chars")
        else:
            # Add short_description from description
            new_short = truncate_description(meta['description'], 80)
            meta['short_description'] = new_short
            changes.append(f"short_description: added ({len(new_short)} chars)")
        
        # Write if changes
        if changes:
            write_markdown(str(file_path), meta, body)
            modified_count += 1
            for change in changes:
                print(f"  {change}")
        else:
            print(f"  No changes needed")
    
    print(f"\n=== Summary ===")
    print(f"Modified: {modified_count} files")
    print(f"Total processed: {len([f for f in md_files if 'warstories' not in f.parts])} files")

if __name__ == "__main__":
    main()