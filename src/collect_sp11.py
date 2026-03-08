"""
collect_sp11.py — Collect chart features for ☆11 SP songs.

1. Fetch actbl.js / titletbl.js from textage.cc
2. Extract all ☆11 SP ANOTHER / LEGGENDARIA songs
3. Match against CPI data (data/raw/cpi_raw_dump.json)
4. Fetch score data and compute chart features
5. Save to data/features_sp11.csv
   - Matched songs include CPI columns
   - Unmatched songs have empty CPI columns
"""

import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/textage')

# Re-use all helpers from collect_data
from collect_data import (
    fetch_js, parse_actbl, parse_titletbl, load_cpi,
    normalize_title, _aggressive_norm, _strip_quoted, _strip_backslash,
    compute_features,
    TEXTAGE_BASE, IDX_SX_LV, IDX_TITLE, IDX_VERSION,
)
from textage_parser import get_score_data

import csv
import re
import time
from pathlib import Path


def build_sp11_song_list(actbl: dict, titletbl: dict) -> list[dict]:
    """Find all ☆11 SP songs (ANOTHER lv=11 or LEGGENDARIA lv=11)."""
    IDX_SA_LV = 9
    IDX_SX_LV = 11
    songs = []
    for filename, act in actbl.items():
        if len(act) <= IDX_SX_LV:
            continue
        sa_lv = act[IDX_SA_LV]
        sx_lv = act[IDX_SX_LV]

        difficulty = None
        query_suffix = None
        if sa_lv == 11:
            difficulty = 'A'
            query_suffix = '1AC00'
        elif sx_lv == 11:
            difficulty = 'X'
            query_suffix = '1XC00'

        if difficulty is None:
            continue

        tbl = titletbl.get(filename)
        if tbl is None:
            continue
        version = tbl[IDX_VERSION]
        title   = tbl[IDX_TITLE]
        if version == 0:
            continue

        url = f"{TEXTAGE_BASE}/score/{version}/{filename}.html?{query_suffix}"

        cpi_title = None
        if difficulty == 'X':
            base = re.sub(r'†LEGGENDARIA$', '', title)
            base = re.sub(r'†$', '', base).strip()
            cpi_title = base + ' [L]'

        songs.append({
            'filename': filename,
            'title': title,
            'cpi_title': cpi_title,
            'version': version,
            'difficulty': difficulty,
            'url': url,
        })
    return songs


def main():
    out_path = Path('data/features_sp11.csv')
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print('Fetching actbl.js ...')
    actbl_js = fetch_js('/actbl.js')
    print('Fetching titletbl.js ...')
    titletbl_js = fetch_js('/titletbl.js')

    actbl    = parse_actbl(actbl_js)
    titletbl = parse_titletbl(titletbl_js)

    songs = build_sp11_song_list(actbl, titletbl)
    print(f'Found {len(songs)} ☆11 SP songs')

    print('Loading CPI data ...')
    cpi_data = load_cpi('data/raw/cpi_raw_dump.json')
    cpi_norm    = {normalize_title(t): v for t, v in cpi_data.items()}
    cpi_agg     = {_aggressive_norm(t): v for t, v in cpi_data.items()}
    cpi_noquote = {_aggressive_norm(_strip_quoted(t)): v for t, v in cpi_data.items()}
    print(f'CPI entries: {len(cpi_data)}')

    def _find_cpi(title, cpi_title=None):
        for key_title in ([cpi_title] if cpi_title else []) + [title]:
            if key_title and normalize_title(key_title) in cpi_norm:
                return cpi_norm[normalize_title(key_title)]
        if '†' in title:
            base = re.sub(r'†LEGGENDARIA$', '', title)
            base = re.sub(r'†$', '', base).strip()
            v = cpi_norm.get(normalize_title(base + ' [L]'))
            if v:
                return v
        for candidate in ([cpi_title] if cpi_title else []) + [title]:
            if candidate is None:
                continue
            v = cpi_agg.get(_aggressive_norm(candidate))
            if v:
                return v
            v = cpi_agg.get(_aggressive_norm(candidate + ' [L]'))
            if v:
                return v
        if '\\' in title:
            t_stripped = _aggressive_norm(_strip_backslash(title))
            v = cpi_noquote.get(t_stripped)
            if v:
                return v
            for suffix in ['', '[l]']:
                v = cpi_noquote.get(t_stripped.rstrip('l][ ') + suffix)
                if v:
                    return v
        for bracket in [' [A]', ' [H]']:
            v = cpi_norm.get(normalize_title(title + bracket))
            if v:
                return v
        t_lower = normalize_title(title)
        for cpi_key, cpi_val in cpi_norm.items():
            if cpi_key.startswith(t_lower + ' [') and not cpi_key.endswith('[l]'):
                return cpi_val
        return None

    matched_songs, unmatched_songs = [], []
    for song in songs:
        cpi = _find_cpi(song['title'], song.get('cpi_title'))
        if cpi:
            matched_songs.append((song, cpi))
        else:
            unmatched_songs.append((song, None))

    print(f'CPI matched: {len(matched_songs)}, unmatched: {len(unmatched_songs)}')

    all_songs = matched_songs + unmatched_songs
    rows = []
    failed = []
    fieldnames = None

    for i, (song, cpi) in enumerate(all_songs):
        status = 'CPI' if cpi else 'no-CPI'
        print(f'[{i+1}/{len(all_songs)}] {song["title"]!r} ({song["difficulty"]}, {status}) ...')
        try:
            score_data = get_score_data(song['url'])
            feats = compute_features(score_data)
            row = {
                'title':      song['title'],
                'filename':   song['filename'],
                'difficulty': song['difficulty'],
                **feats,
            }
            if cpi:
                row.update({f'cpi_{k}': v for k, v in cpi.items()})
            else:
                for k in ['easy', 'clear', 'hard', 'exhard', 'fc']:
                    row[f'cpi_{k}'] = ''
            rows.append(row)
            if fieldnames is None:
                fieldnames = list(row.keys())
        except Exception as e:
            print(f'  ERROR: {e}')
            failed.append((song['title'], str(e)))

        time.sleep(0.5)

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'\nSaved {len(rows)} rows → {out_path}')
    print(f'Failed: {len(failed)}')
    if failed:
        for title, err in failed:
            print(f'  {title!r}: {err}')


if __name__ == '__main__':
    main()
