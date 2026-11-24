from pathlib import Path
import re, sys
root = Path(__file__).resolve().parents[1]
required = [
    '.github/copilot-instructions.md', 'README-AI-TEAM.md',
    'docs/project/project-profile.md', 'docs/ems/safety-checklist.md'
]
errors = []
for item in required:
    if not (root / item).is_file(): errors.append(f'Missing required file: {item}')
agents = sorted((root / '.github/agents').glob('*.agent.md'))
instructions = sorted((root / '.github/instructions').glob('*.instructions.md'))
prompts = sorted((root / '.github/prompts').glob('*.prompt.md'))
if len(agents) != 12: errors.append(f'Expected 12 agents, found {len(agents)}')
if len(instructions) < 10: errors.append(f'Expected at least 10 instruction files, found {len(instructions)}')
if len(prompts) < 8: errors.append(f'Expected at least 8 prompts, found {len(prompts)}')
for path in agents + instructions + prompts:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n') or text.count('---') < 2:
        errors.append(f'Invalid frontmatter: {path.relative_to(root)}')
for path in agents:
    text = path.read_text(encoding='utf-8')
    if not re.search(r'^name:\s*.+$', text, re.M): errors.append(f'Missing name: {path.name}')
    if not re.search(r'^description:\s*.+$', text, re.M): errors.append(f'Missing description: {path.name}')
if errors:
    print('\n'.join('ERROR: ' + x for x in errors)); sys.exit(1)
print(f'OK: {len(agents)} agents, {len(instructions)} instructions, {len(prompts)} prompts, {sum(1 for p in root.rglob("*") if p.is_file())} files')
