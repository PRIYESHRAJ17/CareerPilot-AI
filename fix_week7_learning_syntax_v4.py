from pathlib import Path
p = Path('frontend/app/learning/page.tsx')
if not p.exists():
    raise SystemExit(f'Missing {p}')
s = p.read_text(encoding='utf-8')
bad = '`r`n`r`n'
if bad in s:
    s = s.replace(bad, '\n\n')
    p.write_text(s, encoding='utf-8')
    print('PATCH frontend/app/learning/page.tsx: repaired literal CRLF escape text')
elif '`r`n' in s:
    s = s.replace('`r`n', '\n')
    p.write_text(s, encoding='utf-8')
    print('PATCH frontend/app/learning/page.tsx: repaired literal newline escapes')
else:
    print('SKIP frontend/app/learning/page.tsx: no literal newline escape corruption found')
