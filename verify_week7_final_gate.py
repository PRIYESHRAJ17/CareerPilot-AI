from __future__ import annotations
import csv, hashlib, json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACKER = ROOT / 'WEEK7_AUDIT_TRACKER.csv'
AUDIT = ROOT / 'audit_items.json'
REPORT = ROOT / 'verification_runs' / 'week7_final_gate.json'

def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout

def die(msg: str):
    print('FAIL:', msg)
    sys.exit(1)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

if not TRACKER.exists() or not AUDIT.exists(): die('Required Week 7 audit files are missing.')
items = json.loads(AUDIT.read_text(encoding='utf-8'))
with TRACKER.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
if len(items) != 1000 or len(rows) != 1000: die(f'Expected 1000 records; audit_items={len(items)}, tracker={len(rows)}')
by_n = {int(x['n']): x for x in items}
for row in rows:
    n = int(row['Item'])
    if n not in by_n: die(f'Unexpected tracker item {n}')
    src = by_n[n]
    for row_key, src_key in (('Priority','priority'),('Title','title'),('Category','category'),('File','file'),('Defect','defect'),('Remediation','remediation')):
        if row[row_key] != src[src_key]: die(f'Item {n}: tracker/source mismatch in {row_key}')
    target = ROOT / src['file']
    if not target.exists(): die(f'Item {n}: target path missing: {src["file"]}')
    if row['Status'].strip() != 'VERIFIED': die(f'Item {n}: status is not VERIFIED')
    if not all(row[k].strip() for k in ('FixCommit','Evidence','VerifiedAt','Verifier')):
        die(f'Item {n}: missing verification metadata')
    if f'Item {n}' not in row['Evidence']:
        die(f'Item {n}: evidence is not item-specific')

rc, branch = run(['git', 'branch', '--show-current'])
if rc or branch.strip() != 'week7-finalization': die(f'Expected branch week7-finalization; got {branch.strip()!r}')
commits = sorted(set(r['FixCommit'].strip() for r in rows))
for c in commits:
    if not re.fullmatch(r'[0-9a-f]{40}', c): die(f'Invalid FixCommit SHA: {c}')
    rc, _ = run(['git', 'cat-file', '-e', c + '^{commit}'])
    if rc: die(f'FixCommit does not exist in repository: {c}')

manifest = []
for row in rows:
    target = ROOT / row['File']
    if target.is_file(): digest = sha256(target)
    elif target.is_dir():
        h = hashlib.sha256()
        for q in sorted(x for x in target.rglob('*') if x.is_file()):
            h.update(q.relative_to(ROOT).as_posix().encode()); h.update(hashlib.sha256(q.read_bytes()).digest())
        digest = h.hexdigest()
    else: digest = 'missing'
    manifest.append({'item': int(row['Item']), 'file': row['File'], 'sha256': digest})
REPORT.parent.mkdir(parents=True, exist_ok=True)
report = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'branch': branch.strip(),
    'fix_commits': commits,
    'tracker_items': len(rows),
    'verified_items': sum(r['Status'].strip() == 'VERIFIED' for r in rows),
    'unresolved_items': sum(r['Status'].strip() != 'VERIFIED' for r in rows),
    'source_manifest': manifest,
}
REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('WEEK 7 TRACKER/PROVENANCE GATE: PASS')
print('TOTAL=1000')
print('VERIFIED=1000')
print('BRANCH=' + branch.strip())
print('FIX_COMMITS=' + ','.join(commits))
