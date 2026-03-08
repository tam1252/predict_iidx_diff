"""
merge_bpi.py — Merge BPI data into features_sp12.csv.

Sources:
  1. Historical features_sp12.csv (via git) — provides bpi_at_aaa, bpi_at_9444
     for songs that existed before the parser rewrite.
  2. data/raw/bpi_raw_dump.json — provides bpi_notes, bpi_avg, bpi_wr, bpi_coef
     for all songs.

Merges by 'filename' key.
"""

import csv
import io
import json
import subprocess
from pathlib import Path


def load_hist_bpi(git_ref: str = '2d62a3c') -> dict[str, dict]:
    """Load BPI columns from a historical features_sp12.csv via git."""
    result = subprocess.run(
        ['git', 'show', f'{git_ref}:data/features_sp12.csv'],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f'Warning: could not load historical CSV from {git_ref}')
        return {}
    reader = csv.DictReader(io.StringIO(result.stdout))
    data = {}
    for row in reader:
        fn = row['filename']
        data[fn] = {
            'bpi_notes':  row.get('bpi_notes', ''),
            'bpi_avg':    row.get('bpi_avg', ''),
            'bpi_wr':     row.get('bpi_wr', ''),
            'bpi_coef':   row.get('bpi_coef', ''),
            'bpi_at_aaa': row.get('bpi_at_aaa', ''),
            'bpi_at_9444': row.get('bpi_at_9444', ''),
        }
    return data


def load_bpi_dump(path: str = 'data/raw/bpi_raw_dump.json') -> dict[str, dict]:
    """Load BPI raw dump → {filename: {bpi_notes, bpi_avg, bpi_wr, bpi_coef}}."""
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    data = {}
    for entry in raw['body']:
        tg = entry.get('textage', '')
        # textage field format: "7/a_amuro.html?1AC00"
        if '/' in tg:
            fn = tg.split('/')[-1].split('.')[0]
        else:
            fn = tg.split('.')[0]
        if not fn:
            continue
        data[fn] = {
            'bpi_notes': str(entry.get('notes', '')),
            'bpi_avg':   str(entry.get('avg', '')),
            'bpi_wr':    str(entry.get('wr', '')),
            'bpi_coef':  str(entry.get('coef', '')),
        }
    return data


def main():
    feat_path = Path('data/features_sp12.csv')

    print('Loading historical BPI data ...')
    hist_bpi = load_hist_bpi()
    print(f'  {len(hist_bpi)} songs from historical CSV')

    print('Loading BPI raw dump ...')
    dump_bpi = load_bpi_dump()
    print(f'  {len(dump_bpi)} songs from raw dump')

    print('Reading current features CSV ...')
    with open(feat_path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f'  {len(rows)} rows in current CSV')

    # Add BPI columns
    bpi_cols = ['bpi_notes', 'bpi_avg', 'bpi_wr', 'bpi_coef', 'bpi_at_aaa', 'bpi_at_9444']
    matched_hist = 0
    matched_dump = 0
    unmatched = 0

    new_rows = []
    for row in rows:
        fn = row['filename']
        new_row = dict(row)

        if fn in hist_bpi:
            # Use historical data (has bpi_at_aaa/bpi_at_9444)
            for col in bpi_cols:
                new_row[col] = hist_bpi[fn].get(col, '')
            matched_hist += 1
        elif fn in dump_bpi:
            # Use dump data only (no at_aaa/at_9444 — will be CPI-only in pipeline)
            for col in ['bpi_notes', 'bpi_avg', 'bpi_wr', 'bpi_coef']:
                new_row[col] = dump_bpi[fn].get(col, '')
            new_row['bpi_at_aaa']  = ''
            new_row['bpi_at_9444'] = ''
            matched_dump += 1
        else:
            for col in bpi_cols:
                new_row[col] = ''
            unmatched += 1

        new_rows.append(new_row)

    print(f'  Matched historical: {matched_hist}')
    print(f'  Matched dump only:  {matched_dump}')
    print(f'  Unmatched:          {unmatched}')

    # Determine fieldnames: original cols + bpi cols (in order)
    orig_cols = list(rows[0].keys()) if rows else []
    all_cols = orig_cols.copy()
    for col in bpi_cols:
        if col not in all_cols:
            all_cols.append(col)

    with open(feat_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_cols)
        writer.writeheader()
        writer.writerows(new_rows)

    print(f'Saved {len(new_rows)} rows → {feat_path}')


if __name__ == '__main__':
    main()
