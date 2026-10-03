import csv, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACKER = ROOT / 'WEEK7_AUDIT_TRACKER.csv'
AUDIT = ROOT / 'audit_items.json'
EXPECTED = {**{i:'P0' for i in range(1,101)}, **{i:'P1' for i in range(101,301)}, **{i:'P2' for i in range(301,601)}, **{i:'P3' for i in range(601,851)}, **{i:'P4' for i in range(851,1001)}}

def fail(msg): print('FAIL:', msg); sys.exit(1)
if not TRACKER.exists() or not AUDIT.exists(): fail('Missing tracker or audit_items.json')
with TRACKER.open(encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f))
items=json.loads(AUDIT.read_text(encoding='utf-8'))
if len(rows)!=1000 or len(items)!=1000: fail('Expected exactly 1000 items')
for row, src in zip(rows, items):
    n=int(row['Item'])
    if n != src['n']: fail(f'Item sequence mismatch at {n}')
    if row['Priority'] != EXPECTED[n] or row['Priority'] != src['priority']: fail(f'Item {n}: invalid priority')
    for k, sk in [('Title','title'),('Category','category'),('File','file'),('Defect','defect'),('Remediation','remediation')]:
        if row[k] != src[sk]: fail(f'Item {n}: source mismatch in {k}')
    if row['Status'].strip() not in {'OPEN','IN PROGRESS','FIXED','VERIFIED'}: fail(f'Item {n}: invalid status')
    if row['Status'].strip() == 'VERIFIED' and not all(row[k].strip() for k in ('FixCommit','Evidence','VerifiedAt','Verifier')): fail(f'Item {n}: incomplete verification metadata')
counts=Counter(r['Status'].strip() for r in rows)
print('WEEK7 TRACKER STRUCTURE: PASS')
print('TOTAL=1000')
for s in ('OPEN','IN PROGRESS','FIXED','VERIFIED'): print(f'{s}={counts.get(s,0)}')
