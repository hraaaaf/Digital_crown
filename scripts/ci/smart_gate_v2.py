"""Advisory-only GitHub Actions fan-out inventory. Never suppresses checks."""
from __future__ import annotations
import argparse
import fnmatch
import json
import os
from pathlib import Path
import re

EVENT_RE = re.compile(r"^  ([\w-]+):\s*(?:#.*)?$", re.M)

def on_section(content: str) -> str:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == 'on:' and not line.startswith((' ', '\t')):
            collected = []
            for next_line in lines[i + 1:]:
                if next_line.strip() and not next_line.startswith((' ', '\t', '#')):
                    break
                collected.append(next_line)
            return '\n'.join(collected)
    return ''

def event_section(section: str, event: str) -> str:
    lines = section.splitlines()
    found = False
    collected = []
    for line in lines:
        match = re.match(r'^  ([\w-]+):', line)
        if match:
            if found:
                break
            found = match.group(1) == event
        if found:
            collected.append(line)
    return '\n'.join(collected)

def path_patterns(section: str) -> list[str] | None:
    lines = section.splitlines()
    for i, line in enumerate(lines):
        if re.match(r'^    paths:\s*$', line):
            patterns = []
            for item in lines[i+1:]:
                match = re.match(r'^      -\s*(.+?)\s*$', item)
                if match:
                    patterns.append(match.group(1).strip('"\''))
                elif item.strip() and not item.startswith('      '):
                    break
            return patterns
        inline = re.match(r'^    paths:\s*\[(.*)\]\s*$', line)
        if inline:
            return [p.strip().strip('"\'') for p in inline.group(1).split(',') if p.strip()]
    return None

def inventory(workflows: Path, changed: list[str], base: str) -> dict:
    details = []
    for file in sorted(list(workflows.glob('*.yml')) + list(workflows.glob('*.yaml'))):
        content = file.read_text(encoding='utf-8-sig')
        section = on_section(content)
        events = sorted(set(EVENT_RE.findall(section)))
        pr_events = [e for e in ('pull_request', 'pull_request_target') if e in events]
        matches = []
        ambiguous = False
        for event in pr_events:
            paths = path_patterns(event_section(section, event))
            if paths is None:
                matches.append(event)
            elif not paths or any(p.startswith('!') or '{' in p or '[' in p for p in paths):
                ambiguous = True
                matches.append(event)
            elif any(fnmatch.fnmatchcase(name, p) for name in changed for p in paths):
                matches.append(event)
        details.append({
            'file': file.name,
            'events': events,
            'has_root_concurrency': bool(re.search(r'^concurrency:\s*$', content, re.M)),
            'candidate_pr_trigger': bool(matches),
            'uncertain_match': ambiguous or (not section and bool(re.search(r'^on:', content, re.M))),
            'reusable_calls': re.findall(r'uses:\s*\./\.github/workflows/([\w.-]+)', content),
            'job_dependencies': re.findall(r'^\s{4}needs:\s*(.+)$', content, re.M),
        })
    candidates = [r for r in details if r['candidate_pr_trigger']]
    report = {
        'mode': 'ADVISORY_ONLY_NO_SUPPRESSION',
        'required_checks_verified': False,
        'estimate_not_authoritative': True,
        'base_branch': base,
        'changed_files': changed,
        'workflow_count': len(details),
        'pr_candidate_count': len(candidates),
        'pr_candidates_without_root_concurrency': sum(not r['has_root_concurrency'] for r in candidates),
        'uncertain_count': sum(r['uncertain_match'] for r in details),
        'candidates': candidates,
        'all_workflows': details,
    }
    return report

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--changed-file', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--base', default='master')
    args = parser.parse_args()
    changed = [x.strip() for x in Path(args.changed_file).read_text(encoding='utf-8').splitlines() if x.strip()]
    report = inventory(Path('.github/workflows'), changed, args.base)
    Path(args.out).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as out:
            out.write('\n## Smart Gate V2 — advisory-only fan-out\n')
            out.write(f"Workflow YAML inventory: **{report['workflow_count']}**; possible PR candidates: **{report['pr_candidate_count']}**; candidates without root concurrency: **{report['pr_candidates_without_root_concurrency']}**.\n\n")
            out.write('**Not an authoritative required-check list.** No workflow was skipped, cancelled, disabled or dispatched by this report. Matches can overestimate triggers; branch/complex glob filters require human review.\n\n')
            for item in report['candidates'][:35]:
                out.write(f"- {item['file']} — root concurrency: {item['has_root_concurrency']}\n")
    print(f"SMART_GATE_V2_ADVISORY workflows={report['workflow_count']} candidates={report['pr_candidate_count']} report={args.out}")

if __name__ == '__main__':
    main()
