"""
collect_data.py — Phase 3 data collection

1. Fetches actbl.js and titletbl.js from textage.cc
2. Extracts all ☆12 SP songs (ANOTHER or LEGGENDARIA)
3. Matches against CPI data (data/raw/cpi_raw_dump.json)
4. Fetches score data for each matched song
5. Saves features + CPI to data/features_sp12.csv
"""

import csv
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, 'src')
sys.path.insert(0, 'src/textage')

from textage_parser import get_score_data, parse_html
from score_analyzer import analyze_density, calc_textage_scores

TEXTAGE_BASE = 'https://textage.cc'

# Hex constants used in actbl.js
HEX_MAP = {'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15}

# actbl array indices
# [version, SBo_lv, SBo_style, SB_lv, SB_style, SN_lv, SN_style,
#  SH_lv, SH_style, SA_lv, SA_style, SX_lv, SX_style,
#  DB_lv, DB_style, DN_lv, DN_style, DH_lv, DH_style,
#  DA_lv, DA_style, DX_lv, DX_style]
IDX_SA_LV = 9   # SP ANOTHER level
IDX_SX_LV = 11  # SP LEGGENDARIA level

# titletbl array indices: [version, id, opt, genre, artist, title]
IDX_VERSION = 0
IDX_TITLE   = 5


def fetch_js(path: str) -> str:
    url = TEXTAGE_BASE + '/score' + path
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_actbl(js_text: str) -> dict[str, list]:
    """Parse actbl.js → {filename: [values...]}"""
    result = {}
    # Replace hex constants
    for h, v in HEX_MAP.items():
        js_text = re.sub(rf'\b{h}\b', str(v), js_text)

    pattern = re.compile(r"'(\w+)'\s*:\s*\[([^\]]+)\]")
    for m in pattern.finditer(js_text):
        filename = m.group(1)
        raw = m.group(2)
        try:
            values = [int(x.strip()) for x in raw.split(',') if x.strip()]
            result[filename] = values
        except ValueError:
            pass
    return result


def _extract_title(raw_field: str) -> str:
    """Extract display title from a titletbl title field.

    Handles cases like:
      "Verflucht"
      "A MINSTREL".fontcolor("#ff4080")," ～ ver.short-scape ～".fontcolor("#ff4080")
      "ACT&Oslash;"
    """
    import html
    # Strip HTML tags (e.g. <span ...>...</span>)
    s = re.sub(r'<[^>]+>', '', raw_field)
    # Unescape JS escaped slashes (\/)
    s = s.replace('\\/', '/')
    # Strip .fontcolor("...") method calls
    s = re.sub(r'\.fontcolor\("[^"]*"\)', '', s)
    # Extract all double-quoted string contents and concatenate
    parts = re.findall(r'"([^"]*)"', s)
    if parts:
        title = ''.join(parts)
    else:
        # Fallback: strip outer quotes
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or \
           (s.startswith("'") and s.endswith("'")):
            title = s[1:-1]
        else:
            title = s
    return html.unescape(title)


def parse_titletbl(js_text: str) -> dict[str, list]:
    """Parse titletbl.js → {filename: [version, id, opt, genre, artist, title]}"""
    result = {}

    pattern = re.compile(r"'(\w+)'\s*:\s*\[([^\]]+)\]")
    for m in pattern.finditer(js_text):
        filename = m.group(1)
        raw = m.group(2)
        # Format: version, id, opt, "genre", "artist", "title"
        # The genre field may contain commas (e.g. "JUNGLE, DRUM N BASS"), so we cannot
        # simply split on commas. Instead: extract the 3 leading ints, then find the 3
        # quoted string fields by walking the remaining text quote-by-quote.
        try:
            int_m = re.match(r'\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(.*)', raw.strip(), re.DOTALL)
            if not int_m:
                continue
            version = int(int_m.group(1))
            rest = int_m.group(4)  # everything after the 3 ints

            # Extract 3 quoted string fields in order, respecting escaped quotes
            quoted_fields = re.findall(r'"((?:[^"\\]|\\.)*)"', rest)
            if len(quoted_fields) < 3:
                continue
            genre  = _extract_title(f'"{quoted_fields[0]}"')
            artist = _extract_title(f'"{quoted_fields[1]}"')
            title  = _extract_title(f'"{quoted_fields[2]}"')
            result[filename] = [version, None, None, genre, artist, title]
        except (ValueError, IndexError):
            pass
    return result


def load_cpi(path: str) -> dict[str, dict]:
    """Load CPI data → {title: {easy, clear, hard, exhard, fc}}"""
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    headers = [h.lower() for h in raw['headers']]
    result = {}
    for row in raw['result']:
        if len(row) < len(headers):
            continue
        rec = dict(zip(headers, row))
        title = rec.pop('title')
        result[title] = rec
    return result


def normalize_title(t: str) -> str:
    """Light normalization for title matching."""
    # Collapse multiple spaces
    t = re.sub(r'  +', ' ', t.strip())
    return t.lower()


def _aggressive_norm(t: str) -> str:
    """Aggressive normalization for fuzzy title matching.

    - Strips all whitespace
    - NFKD decomposition + drop combining chars (accents)
    - Special char substitution: Ø→0, etc.
    """
    import unicodedata
    t = re.sub(r' \[L\]$', '', t)
    t = t.lower()
    # Special char substitutions (before NFKD)
    t = t.replace('ø', '0').replace('∅', '0')
    t = t.replace('æ', 'ae').replace('œ', 'oe')  # ligatures CPI expands
    # NFKD + strip combining characters (accents)
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    # Strip all whitespace
    t = re.sub(r'\s+', '', t)
    return t


def _strip_quoted(t: str) -> str:
    """Strip "quoted" substrings — textage uses \\ where CPI uses "subtitle".
    CPI mixes ASCII " (U+0022) and curly " (U+201D) for quoted substrings.
    """
    # Handle both ASCII quotes and curly right double quotes (U+201D used as both open/close)
    t = re.sub(r'"[^"]*"', '', t)    # ASCII "..."
    t = re.sub(r'\u201d[^\u201d]*\u201d', '', t)  # curly "..."
    return t.strip()


def _strip_backslash(t: str) -> str:
    """Strip \\ sequences from textage titles (represent quoted subtitle)."""
    return re.sub(r'\\+', '', t).strip()


def build_song_list(actbl: dict, titletbl: dict) -> list[dict]:
    """Find all ☆12 SP songs."""
    songs = []
    for filename, act in actbl.items():
        if len(act) <= IDX_SX_LV:
            continue
        sa_lv = act[IDX_SA_LV] if len(act) > IDX_SA_LV else 0
        sx_lv = act[IDX_SX_LV] if len(act) > IDX_SX_LV else 0

        difficulty = None
        query_suffix = None
        if sa_lv == 12:
            difficulty = 'A'
            query_suffix = '1AC00'
        elif sx_lv == 12:
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
            # Consumer-only, no URL
            continue

        url = f"{TEXTAGE_BASE}/score/{version}/{filename}.html?{query_suffix}"

        # For LEGGENDARIA songs, compute the expected CPI title: strip † / LEGGENDARIA suffix, add [L]
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


def compute_features(score_data: dict) -> dict:
    density = analyze_density(score_data)
    scores  = calc_textage_scores(score_data)
    bpm_changes = score_data.get('bpm_changes', [])
    bpm_base    = score_data.get('bpm_base', '120')

    # BPM range
    bpms = [float(c['bpm']) for c in bpm_changes if c.get('bpm')]
    base_bpm_str = re.sub(r'[～~].*', '', bpm_base).strip()
    try:
        base_bpm = float(base_bpm_str)
    except ValueError:
        base_bpm = 120.0
    bpms.append(base_bpm)
    bpm_min = min(bpms)
    bpm_max = max(bpms)

    return {
        'total_notes': score_data['total_notes'],
        'duration':    round(density['duration'], 3),
        'peak_density':    round(density['peak_density'], 4),
        'mean_density':    round(density['mean_density'], 4),
        'peak_scratch_density': round(density['peak_scratch_density'], 4),
        'bpm_min': bpm_min,
        'bpm_max': bpm_max,
        'bpm_ratio': round(bpm_max / bpm_min, 4) if bpm_min > 0 else 1.0,
        **{k: v for k, v in scores.items()},
    }


def main():
    out_path = Path('data/features_sp12.csv')
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print('Fetching actbl.js ...')
    actbl_js = fetch_js('/actbl.js')
    print('Fetching titletbl.js ...')
    titletbl_js = fetch_js('/titletbl.js')

    print('Parsing JS data ...')
    actbl   = parse_actbl(actbl_js)
    titletbl = parse_titletbl(titletbl_js)

    songs = build_song_list(actbl, titletbl)
    print(f'Found {len(songs)} ☆12 SP songs')

    print('Loading CPI data ...')
    cpi_data = load_cpi('data/raw/cpi_raw_dump.json')
    cpi_norm = {normalize_title(t): v for t, v in cpi_data.items()}
    # Aggressive lookup: strip spaces + NFKD + special chars
    cpi_agg  = {_aggressive_norm(t): v for t, v in cpi_data.items()}
    # Quote-stripped lookup: remove "..." substrings (CPI) for matching against textage \\ titles
    cpi_noquote = {_aggressive_norm(_strip_quoted(t)): v for t, v in cpi_data.items()}
    print(f'CPI entries: {len(cpi_data)}')

    def _find_cpi(title: str, cpi_title: str | None = None) -> dict | None:
        # Tier 1: cpi_title (e.g. base + ' [L]' for LEGGENDARIA)
        for key_title in ([cpi_title] if cpi_title else []) + [title]:
            if key_title and normalize_title(key_title) in cpi_norm:
                return cpi_norm[normalize_title(key_title)]
        # Tier 2: † ANOTHER songs → base + ' [L]'
        if '†' in title:
            base = re.sub(r'†LEGGENDARIA$', '', title)
            base = re.sub(r'†$', '', base).strip()
            v = cpi_norm.get(normalize_title(base + ' [L]'))
            if v:
                return v
        # Tier 3: aggressive normalization (strip spaces, NFKD, Ø→0)
        for candidate in ([cpi_title] if cpi_title else []) + [title]:
            if candidate is None:
                continue
            v = cpi_agg.get(_aggressive_norm(candidate))
            if v:
                return v
            # also try with [L]
            v = cpi_agg.get(_aggressive_norm(candidate + ' [L]'))
            if v:
                return v
        # Tier 4: \\ in textage = "quoted" in CPI — strip both and compare aggressively
        if '\\' in title:
            t_stripped = _aggressive_norm(_strip_backslash(title))
            v = cpi_noquote.get(t_stripped)
            if v:
                return v
            # Also try without [L] and with [L]
            v = cpi_noquote.get(t_stripped.rstrip('l][ '))
            for suffix in ['', '[l]']:
                v = cpi_noquote.get(t_stripped.rstrip('l][ ') + suffix)
                if v:
                    return v
        # Tier 5: difficulty bracket matching ([A] for ANOTHER, [H] for special)
        for bracket in [' [A]', ' [H]']:
            v = cpi_norm.get(normalize_title(title + bracket))
            if v:
                return v
        # Tier 6: prefix match — textage title is a prefix of a CPI title followed by ' ['
        # e.g. "CODE:1" matches "CODE:1 [revision1.0.1]"
        t_lower = normalize_title(title)
        for cpi_key, cpi_val in cpi_norm.items():
            if cpi_key.startswith(t_lower + ' [') and not cpi_key.endswith('[l]'):
                return cpi_val
        return None

    # Match songs to CPI
    matched = []
    unmatched_titles = []
    for song in songs:
        cpi = _find_cpi(song['title'], song.get('cpi_title'))
        if cpi:
            matched.append((song, cpi))
        else:
            unmatched_titles.append(song['title'])

    print(f'Matched: {len(matched)}, Unmatched: {len(unmatched_titles)}')
    if unmatched_titles:
        print('Unmatched songs (first 20):')
        for t in unmatched_titles[:20]:
            print(f'  {t!r}')

    if not matched:
        print('No matched songs. Aborting.')
        return

    # Collect features
    fieldnames = None
    rows = []
    failed = []

    for i, (song, cpi) in enumerate(matched):
        print(f'[{i+1}/{len(matched)}] {song["title"]} ({song["difficulty"]}) ...')
        try:
            score_data = get_score_data(song['url'])
            feats = compute_features(score_data)
            row = {
                'title':      song['title'],
                'filename':   song['filename'],
                'difficulty': song['difficulty'],
                **feats,
                **{f'cpi_{k}': v for k, v in cpi.items()},
            }
            rows.append(row)
            if fieldnames is None:
                fieldnames = list(row.keys())
        except Exception as e:
            print(f'  ERROR: {e}')
            failed.append((song['title'], str(e)))

        time.sleep(0.5)  # be polite to textage.cc

    # Write CSV
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'\nSaved {len(rows)} rows to {out_path}')
    if failed:
        print(f'Failed ({len(failed)}):')
        for title, err in failed:
            print(f'  {title!r}: {err}')


if __name__ == '__main__':
    main()
