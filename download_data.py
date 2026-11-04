"""Download the exact 100-match Week 2 pilot. Python standard library only."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
RAW.mkdir(exist_ok=True)
snapshot = json.loads((ROOT / 'snapshot.json').read_text(encoding='utf-8-sig'))
revision = snapshot['git_commit']
BASE = f'https://raw.githubusercontent.com/hudl/open-data/{revision}/data'
reference = json.loads((ROOT / 'source_manifest.json').read_text(encoding='utf-8-sig'))
expected_hash = {int(r['match_id']): r['sha256'] for r in reference}

def fetch(url, target, checksum=None):
    if target.exists():
        data = target.read_bytes()
        try:
            json.loads(data)
            if checksum and hashlib.sha256(data).hexdigest() != checksum:
                raise ValueError('Cached file checksum mismatch')
            return
        except (ValueError, json.JSONDecodeError):
            pass
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'student-xg-pilot'})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
            json.loads(data)
            if checksum and hashlib.sha256(data).hexdigest() != checksum:
                raise ValueError('Downloaded file checksum mismatch')
            target.write_bytes(data)
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

fetch(f'{BASE}/matches/2/27.json', RAW / 'matches_2_27.json')
all_matches = json.loads((RAW / 'matches_2_27.json').read_text(encoding='utf-8-sig'))
selected = sorted(all_matches, key=lambda m: (m['match_date'], m['match_id']))[:100]
if {m['match_id'] for m in selected} != set(expected_hash):
    raise RuntimeError('Selected matches differ from the supplied pilot manifest')
(ROOT / 'selected_matches.json').write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding='utf-8')

def download_match(match):
    mid = match['match_id']
    fetch(f'{BASE}/events/{mid}.json', RAW / f'events_{mid}.json', expected_hash[mid])
    return mid

completed = 0
failures = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    pending = {pool.submit(download_match, m): m['match_id'] for m in selected}
    for future in concurrent.futures.as_completed(pending):
        try:
            future.result()
            completed += 1
            print(f'{completed}/100 downloaded or verified', flush=True)
        except Exception as exc:
            failures.append({'match_id': pending[future], 'error': str(exc)})
(ROOT / 'download_status.json').write_text(json.dumps({'success': completed, 'failures': failures}, indent=2), encoding='utf-8')
if failures:
    raise RuntimeError('Incomplete download. Check download_status.json and rerun.')
print('All 100 event JSON files verified. Next: python audit_xg.py')
