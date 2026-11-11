"""Download all available in-scope matches at the pinned Week 2 source revision.

Raw JSON is compressed locally and ignored by Git. Reruns verify and reuse cache.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import zlib

from scope import eligible_catalogue_entry, eligible_match

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'week3/data'
RAW = ROOT/'raw/week3'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def fetch(url):
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'student-xg-week3'})
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
            json.loads(payload)
            return payload
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt+1)


def main(metadata_only=False, workers=8):
    DATA.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    revision = read(ROOT/'snapshot.json')['git_commit']
    base = f'https://raw.githubusercontent.com/hudl/open-data/{revision}/data'
    catalogue_path = DATA/'competitions.json'
    if not catalogue_path.exists():
        catalogue_path.write_bytes(fetch(f'{base}/competitions.json'))
    catalogue = read(catalogue_path)
    metadata_sources = [dict(url=f'{base}/competitions.json', sha256=sha(catalogue_path.read_bytes()))]
    matches, coverage = {}, []
    for comp in catalogue:
        if not eligible_catalogue_entry(comp):
            continue
        # Entire season wholly before cutoff cannot contain eligible matches.
        if int(comp['season_name'][-4:]) < 2001:
            continue
        cid, sid = comp['competition_id'], comp['season_id']
        path = DATA/f'matches_{cid}_{sid}.json'
        url = f'{base}/matches/{cid}/{sid}.json'
        if not path.exists():
            path.write_bytes(fetch(url))
        metadata_sources.append(dict(url=url, sha256=sha(path.read_bytes())))
        all_matches = read(path)
        selected = []
        for match in all_matches:
            if not eligible_match(match):
                continue
            mid = match['match_id']
            if mid in matches:
                raise ValueError(f'Duplicate match in catalogue: {mid}')
            # Preserve necessary metadata without manager/player personal details.
            slim = {key: match[key] for key in ['match_id', 'match_date', 'competition', 'season']}
            for team in ['home_team', 'away_team']:
                slim[team] = {f'{team}_gender': match[team][f'{team}_gender']}
            matches[mid] = slim
            selected.append(match)
        if selected:
            coverage.append(dict(competition_id=cid, season_id=sid,
                competition=comp['competition_name'], country=comp['country_name'], season=comp['season_name'],
                catalogue_matches=len(all_matches), selected_matches=len(selected),
                first_date=min(m['match_date'] for m in selected), last_date=max(m['match_date'] for m in selected)))
    ordered = sorted(matches.values(), key=lambda m: (m['match_date'], m['match_id']))
    save(DATA/'selected_matches.json', ordered)
    save(DATA/'coverage.json', coverage)
    snapshot = dict(repository='https://github.com/hudl/open-data', git_commit=revision,
        scope='Senior men; European competition region or FIFA World Cup; match_date >= 2001-01-01',
        cutoff_basis='Actual match date, not season label',
        selected_matches=len(ordered), competition_seasons=len(coverage),
        selected_matches_sha256=sha((DATA/'selected_matches.json').read_bytes()),
        metadata_sources=metadata_sources)
    save(DATA/'snapshot.json', snapshot)
    print(json.dumps(dict(matches=len(ordered), coverage=coverage), ensure_ascii=False), flush=True)
    if metadata_only:
        return
    old_path = DATA/'source_manifest.json'
    old = {r['match_id']: r for r in read(old_path)} if old_path.exists() else {}
    pilot = {r['match_id']: r['sha256'] for r in read(ROOT/'source_manifest.json')}

    def download(match):
        mid = match['match_id']
        path = RAW/f'events_{mid}.json.gz'
        expected = old.get(mid, {}).get('sha256') or pilot.get(mid)
        payload = None
        cache_valid = False
        if path.exists():
            try:
                cached = gzip.decompress(path.read_bytes())
                json.loads(cached)
                if expected and sha(cached) == expected:
                    payload = cached
                    cache_valid = True
            except (OSError, ValueError, EOFError, zlib.error):
                pass
        pilot_path = ROOT/'raw'/f'events_{mid}.json'
        if payload is None and mid in pilot and pilot_path.exists():
            cached = pilot_path.read_bytes()
            if sha(cached) == pilot[mid]:
                payload = cached
        url = f'{base}/events/{mid}.json'
        if payload is None:
            payload = fetch(url)
        checksum = sha(payload)
        if expected and checksum != expected:
            raise ValueError(f'Source hash mismatch {mid}')
        events = json.loads(payload)
        if not isinstance(events, list) or not events:
            raise ValueError(f'Empty or malformed events {mid}')
        if not cache_valid:
            temporary = path.with_suffix('.tmp')
            temporary.write_bytes(gzip.compress(payload, compresslevel=1, mtime=0))
            temporary.replace(path)
        return dict(match_id=mid, url=url, sha256=checksum, events=len(events), bytes=len(payload))

    manifest, failures = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download, m): m['match_id'] for m in ordered}
        for future in as_completed(futures):
            try:
                manifest.append(future.result())
            except Exception as exc:
                failures.append(dict(match_id=futures[future], error=str(exc)))
            done = len(manifest)+len(failures)
            if done % 50 == 0 or done == len(ordered):
                save(old_path, sorted(manifest, key=lambda r:r['match_id']))
                print(f'{done}/{len(ordered)} processed; failures={len(failures)}', flush=True)
    save(old_path, sorted(manifest, key=lambda r:r['match_id']))
    save(DATA/'download_status.json', dict(success=len(manifest), expected=len(ordered), failures=failures,
         checked_utc=datetime.now(timezone.utc).isoformat()))
    if failures:
        raise RuntimeError('Incomplete download; rerun to resume')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    main(args.metadata_only, args.workers)
