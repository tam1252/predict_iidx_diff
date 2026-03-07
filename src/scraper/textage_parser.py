import math
import re
import requests

B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
LNDEF = 384  # default measure length


def _b64_find(c: str) -> int:
    v = B64.find(c)
    return v if v != -1 else 0


def _decode_hash(sdd: str, ln_n: int) -> list[dict]:
    """Decode a '#'-prefixed measure string. Returns list of {pos, key} dicts."""
    notes = []
    sft = 1
    v2c = 0

    while sft < len(sdd):
        v2o = ""
        v2v = (1 if v2c else 3) * ln_n // 6
        ch = sdd[sft]
        v2s = 0; v2p = 0; v2t = 0

        # --- Type 0: repeating single char ---
        if ch in "CcRrPp":
            if ch == 'C':   v2s, v2p = 0,  192
            elif ch == 'c': v2s, v2p = 96, 192
            elif ch == 'R': v2s, v2p = 0,  96
            elif ch == 'r': v2s, v2p = 48, 96
            elif ch == 'P': v2s, v2p = 0,  48
            elif ch == 'p': v2s, v2p = 24, 48
            v2t = 0
            if not v2c:
                sft += 1
                v2o = sdd[sft] if sft < len(sdd) else ""
            sft += 1

        # --- Type 1: Base64 block ---
        elif ch in "BbQqOoXxZzSsTtUuVvWw":
            MAP = {
                'B': (0, 192), 'b': (96, 192), 'Q': (0, 96),  'q': (48, 96),
                'O': (0, 48),  'o': (24, 48),  'X': (0, 24),  'x': (12, 24),
                'Z': (0, 12),  'z': (6,  12),  'S': (0, 64),  's': (32, 64),
                'T': (0, 32),  't': (16, 32),  'U': (0, 16),  'u': (8,  16),
                'V': (0, 8),   'v': (4,  8),   'W': (0, 4),   'w': (2,  4),
            }
            v2s, v2p = MAP[ch]
            v2t = 1
            v2b = math.ceil(v2v / v2p) + 1
            v2o = sdd[sft + 1 : sft + v2b]
            sft += v2b

        # --- Type 2: explicit position ---
        elif ch in "1234567":
            v2o = sdd[sft : sft + 3]
            v2t = 2
            sft += 3

        elif ch in "89":
            if ch == "9":
                v2o = "1" + sdd[sft + 2 : sft + 4]
            else:
                v2o = ""
            b64_val = _b64_find(sdd[sft + 1]) if sft + 1 < len(sdd) else 0
            for i2 in range(6):
                if b64_val & (1 << i2):
                    v2o += str(i2 + 2) + sdd[sft + 2 : sft + 4]
            v2t = 2
            sft += 4

        elif ch == "-":
            v2c = 1
            sft += 1
            continue

        elif ch == "_":
            v2o = "AA" if sft == len(sdd) - 1 else sdd[sft + 1:]
            v2c = 2
            v2t = 2

        else:
            break  # unknown char → end of measure

        # JS: if(sdd.charAt(sft-1)=="-") continue;
        if sft > 0 and sft - 1 < len(sdd) and sdd[sft - 1] == "-":
            continue

        # --- Build v2k for type 0 / 1 ---
        v2k = ""
        if v2t == 1:
            for c2 in v2o:
                v2x = _b64_find(c2)
                if v2c == 0:
                    v2k += str(v2x // 8) + str(v2x % 8)
                else:
                    for i3 in range(5, -1, -1):
                        v2k += "1" if (v2x >> i3) & 1 else "0"
        elif v2t == 0:
            i2 = v2s
            while i2 < ln_n:
                v2k += "1" if v2c else v2o
                i2 += v2p

        # --- Emit notes ---
        if v2t != 2:
            v2i = 0
            i2 = v2s
            # JS loop runs until i2 >= ln_n (not limited by v2k length)
            while i2 < ln_n:
                ob2 = v2k[v2i] if v2i < len(v2k) else ""
                if ob2 and ob2 != "0":
                    if v2c:
                        key_val = 0
                    else:
                        try:
                            key_val = int(ob2)
                        except ValueError:
                            key_val = 8
                    if key_val < 8:
                        notes.append({"pos": i2, "key": key_val})
                v2i += 1
                i2 += v2p
        else:
            i2 = 0
            while i2 < len(v2o):
                if v2c == 0:
                    ob2 = v2o[i2]
                    i2 += 1
                else:
                    ob2 = "0"
                ch1 = v2o[i2] if i2 < len(v2o) else ""
                ch2 = v2o[i2 + 1] if i2 + 1 < len(v2o) else ""
                if ch1 and ch2:
                    v2h = _b64_find(ch1) * 64 + _b64_find(ch2)
                    try:
                        key_val = 0 if v2c else int(ob2)
                    except ValueError:
                        key_val = 8
                    if key_val < 8:
                        notes.append({"pos": v2h, "key": key_val})
                i2 += 2

        if v2c == 2:
            break

    return notes


def _decode_hex(sdd: str, ln_n: int, max_lane: int = 7) -> list[dict]:
    """Decode a hex-format measure string. Returns list of {pos, key} dicts.
    SP uses key=7 (ky=7), so j=0..7 (lanes 0-7 all valid).
    """
    notes = []
    nbar = -(-ln_n // 3)  # ceil(ln_n / 3)

    if sdd.startswith("x"):
        sft_len = int(sdd[1:4], 16)
        idx = 4
    else:
        sft_len = len(sdd)
        idx = 0

    div = 0
    while idx < len(sdd):
        while idx < len(sdd) and sdd[idx] == "@":
            try:
                div += int(sdd[idx + 1 : idx + 3], 16) * 2
            except ValueError:
                pass
            idx += 3
        if idx >= len(sdd):
            break
        if idx + 2 <= len(sdd):
            try:
                y = int(sdd[idx : idx + 2], 16)
                pos = (nbar * div * 3) // sft_len
                for j in range(max_lane + 1):  # SP: j=0..7 (ky=7)
                    if (y >> j) == 0:
                        break
                    if (y >> j) & 1:
                        notes.append({"pos": pos, "key": j})
            except ValueError:
                pass
        idx += 2
        div += 2

    return notes


def _parse_cn_arrays(text: str) -> dict:
    """Parse c1[n] and c2[n] arrays from JS text.
    Handles both literal arrays and reference copies (e.g. c1[61]=c1[21]).
    """
    result = {"c1": {}, "c2": {}}

    # Pass 1: literal array assignments  c1[n]=[[...],[...],...];
    pattern = r'(c[12])\[(\d+)\]=((?:\[(?:\[.*?\])\])+);'
    for side, measure_str, data_str in re.findall(pattern, text, re.DOTALL):
        measure = int(measure_str)
        if measure not in result[side]:
            result[side][measure] = []
        for entry_str in re.findall(r'\[(\d+(?:,\d+)*)\]', data_str):
            vals = [int(x) for x in entry_str.split(',')]
            lane_raw  = vals[0]
            cnp       = vals[1] if len(vals) > 1 else 0    # start position (in nbar units)
            cnh       = vals[2] if len(vals) > 2 else 30   # length (in nbar units)
            cnf       = vals[3] if len(vals) > 3 else 3    # flag: &1=has_start, &2=has_end
            result[side][measure].append({
                "lane_raw": lane_raw, "cnp": cnp, "cnh": cnh, "cnf": cnf,
            })

    # Pass 2: reference copies  c1[n]=c1[m];  (e.g. c1[61]=c1[21])
    ref_pattern = r'(c[12])\[(\d+)\]=(c[12])\[(\d+)\];'
    for side_dst, dst_str, side_src, src_str in re.findall(ref_pattern, text):
        dst = int(dst_str)
        src = int(src_str)
        if dst not in result[side_dst] and src in result[side_src]:
            result[side_dst][dst] = [dict(e) for e in result[side_src][src]]

    return result


def _expand_cn_lanes(lane_raw: int) -> list[int]:
    if lane_raw == 0:
        return [0]
    if 1 <= lane_raw <= 7:
        return [lane_raw]
    lanes = []
    v = lane_raw
    while v >= 10:
        lanes.append(v % 10)
        v //= 10
    lanes.append(v)
    return sorted(set(lanes))


def _build_measure_abs_starts(measure_lens: dict, max_measure: int) -> dict:
    """Compute cumulative absolute start position (in pos units) for each measure."""
    abs_starts = {}
    current = 0
    for m in range(1, max_measure + 2):
        abs_starts[m] = current
        ln_n = measure_lens.get(m, LNDEF)
        # pos units = 1 per unit, max pos = ln_n - 1
        current += ln_n
    return abs_starts


def decode_textage_sp(
    sp_raw_by_measure: dict,    # {measure_num: raw_string}
    measure_lens: dict,         # {measure_num: ln_n}
    cn_arrays: dict,            # result of _parse_cn_arrays
    side: int = 1,              # 1 = P1
) -> list[dict]:
    """
    Decode all notes (normal + CN start/end) for SP side.
    Returns list of {measure, pos, key} where:
      - key 0-7: lane (0=scratch)
      - pos: position within measure (0 to ln_n-1)
      - type: 'normal' | 'cn_start' | 'cn_end'
    """
    notes = []

    # 1. Decode normal notes
    for measure_num, sdd in sorted(sp_raw_by_measure.items()):
        if not sdd or sdd in ("00", ""):
            continue
        ln_n = measure_lens.get(measure_num, LNDEF)

        if sdd.startswith("#"):
            raw_notes = _decode_hash(sdd, ln_n)
        else:
            raw_notes = _decode_hex(sdd, ln_n)

        # Deduplicate within measure using (pos, key) set
        seen = set()
        for note in raw_notes:
            key = (note["pos"], note["key"])
            if key not in seen:
                seen.add(key)
                notes.append({"measure": measure_num, "pos": note["pos"], "key": note["key"], "type": "normal"})

    # 2. Decode CN notes with cross-measure endpoint support
    max_measure = max(sp_raw_by_measure.keys()) if sp_raw_by_measure else 100
    abs_starts = _build_measure_abs_starts(measure_lens, max_measure + 10)
    # Reverse lookup: given absolute position, which measure?
    measure_boundaries = sorted(abs_starts.items())  # [(m, abs_start), ...]

    def abs_to_measure_and_pos(abs_pos: int) -> tuple[int, int]:
        """Convert absolute position to (measure_num, relative_pos)."""
        for i in range(len(measure_boundaries) - 1):
            m, start = measure_boundaries[i]
            _, next_start = measure_boundaries[i + 1]
            if start <= abs_pos < next_start:
                return m, abs_pos - start
        # Fallback
        m, start = measure_boundaries[-1]
        return m, abs_pos - start

    side_key = "c1" if side == 1 else "c2"
    for def_measure, entries in cn_arrays[side_key].items():
        abs_measure_start = abs_starts.get(def_measure, 0)

        for e in entries:
            lanes = _expand_cn_lanes(e["lane_raw"])
            cnp = e["cnp"]
            cnh = e["cnh"]
            cnf = e["cnf"]

            # CN coordinates: cnp and cnp+cnh are in "bar row" units
            # From JS: stat_insert uses (cnp*3) as position → same scale as pos
            start_abs = abs_measure_start + cnp * 3
            end_abs   = abs_measure_start + (cnp + cnh) * 3

            for lane in lanes:
                # cnf & 1 → has start note
                if cnf & 1:
                    sm, sp = abs_to_measure_and_pos(start_abs)
                    notes.append({"measure": sm, "pos": sp, "key": lane, "type": "cn_start"})

                # cnf & 2 → has end note
                if cnf & 2:
                    em, ep = abs_to_measure_and_pos(end_abs)
                    notes.append({"measure": em, "pos": ep, "key": lane, "type": "cn_end"})

    return notes


def _extract_difficulty_block(html_text: str, difficulty: str) -> str:
    """
    Extract the JS block corresponding to the given difficulty.
    Based on bms2jsh.js char2 mapping:
      X → a=1,kuro=1 (LEGGENDARIA, uses if(a) block)
      A → a=1        (ANOTHER,     uses if(a) block)
      L → l=1        (uses if(l) block - rare)
      N → l=1,hps=1  (NORMAL,      uses if(l)? actually separate)
      H → hps=1      (HYPER)
      P → beginner
    In practice, sp data lives in if(a){} for ANOTHER/LEGGENDARIA,
    and difficulty-specific blocks for others.
    Returns the text of the matching if(...){...} block, or full html if not found.
    """
    # Map URL char2 to the JS variable that gates the sp data
    # X and A both set a=1 → if(a) block
    diff_to_var = {
        'X': 'a',  # LEGGENDARIA (a=1, kuro=1)
        'A': 'a',  # ANOTHER
        'L': 'l',  # rare leggendaria variant
        'N': 'n',  # NORMAL - try 'n' first, fallback handled below
        'H': 'h',  # HYPER
        'P': 'p',  # BEGINNER
    }
    var = diff_to_var.get(difficulty.upper(), 'a')

    # Find "if(VAR){" and extract the balanced braces block
    pattern = rf'if\s*\(\s*{re.escape(var)}\s*\)\s*\{{'
    m = re.search(pattern, html_text)
    if not m:
        return html_text  # fallback: use full text

    start = m.end() - 1  # position of the opening '{'
    depth = 0
    for i in range(start, len(html_text)):
        if html_text[i] == '{':
            depth += 1
        elif html_text[i] == '}':
            depth -= 1
            if depth == 0:
                return html_text[start:i+1]

    return html_text  # fallback


def parse_html(html_text: str, side: int = 1, difficulty: str = 'A') -> dict:
    """
    Main entry point. Parses Textage HTML and returns:
    {
        'title': str,
        'notes': list[{measure, pos, key, type}],
        'measure_lens': dict,
        'total_notes': int,
    }
    difficulty: 'P'=beginner, 'N'=normal, 'H'=hyper, 'A'=another, 'X'=leggendaria
    """
    # Extract measure lengths and title from full HTML (these are outside if blocks)
    measure_lens = {}
    for m in re.finditer(r'ln\[(\d+)\]=(\d+);', html_text):
        measure_lens[int(m.group(1))] = int(m.group(2))

    title_m = re.search(r'title\s*=\s*"([^"]+)"', html_text)
    title = title_m.group(1) if title_m else ""

    # Extract only the block for the requested difficulty
    block = _extract_difficulty_block(html_text, difficulty)

    # Extract sp[] entries - two formats exist:
    # Format A (array literal): sp=[,,"entry2","entry3",...];
    # Format B (individual assignment): sp[2]="entry2"; sp[3]="entry3"; ...
    sp_raw_by_measure = {}

    array_match = re.search(r'sp=\[(.*?)\];', block, re.DOTALL)
    if array_match:
        # Format A: split on commas outside quotes, raw index = measure number
        content = array_match.group(1)
        raw_parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', content)
        results_raw = {}
        for i, p in enumerate(raw_parts):
            measure_num = i
            p = p.strip()
            if p.startswith('"'):
                sdd = p.strip('"')
            elif p.startswith("sp["):
                ref_m = re.search(r'\d+', p)
                sdd = results_raw.get(int(ref_m.group()), "") if ref_m else ""
            else:
                sdd = ""
            results_raw[measure_num] = sdd
            sp_raw_by_measure[measure_num] = sdd
    else:
        # Format B: individual sp[n]="..." assignments
        for m in re.finditer(r'sp\[(\d+)\]\s*=\s*"([^"]*)";', block):
            sp_raw_by_measure[int(m.group(1))] = m.group(2)
        # Also handle sp[n]=sp[m] (reference to another measure)
        for m in re.finditer(r'sp\[(\d+)\]\s*=\s*sp\[(\d+)\];', block):
            ref = int(m.group(2))
            sp_raw_by_measure[int(m.group(1))] = sp_raw_by_measure.get(ref, "")

    if not sp_raw_by_measure:
        return {"title": title, "notes": [], "measure_lens": measure_lens, "total_notes": 0}

    # Extract CN arrays from the difficulty block
    cn_arrays = _parse_cn_arrays(block)

    # Decode all notes
    notes = decode_textage_sp(sp_raw_by_measure, measure_lens, cn_arrays, side=side)

    return {
        "title": title,
        "notes": notes,
        "measure_lens": measure_lens,
        "total_notes": len(notes),
    }


def get_score_data(url: str) -> dict:
    """Fetch Textage HTML and parse it. Difficulty is inferred from URL query param."""
    res = requests.get(url)
    res.encoding = res.apparent_encoding

    # Extract difficulty from URL query: ?1XC00 → char2='X', ?1AC00 → 'A', etc.
    # char2 mapping (from bms2jsh.js):
    #   X → LEGGENDARIA (a=1, kuro=1)   A → ANOTHER (a=1)
    #   N → NORMAL      H → HYPER       P → BEGINNER
    difficulty = 'A'  # default
    try:
        q_start = url.index('?') + 1
        if len(url) > q_start + 1:
            char2 = url[q_start + 1].upper()
            if char2 in 'XANHLPBGRN':
                difficulty = char2
    except ValueError:
        pass

    return parse_html(res.text, difficulty=difficulty)


if __name__ == "__main__":
    url = "https://textage.cc/score/33/amorfati.html?1AC00"
    data = get_score_data(url)
    print(f"Title: {data['title']}")
    print(f"Total notes: {data['total_notes']}")

    # Per-measure count
    from collections import defaultdict
    per_measure = defaultdict(int)
    for n in data["notes"]:
        per_measure[n["measure"]] += 1
    print("\nMeasure | Notes")
    print("--------|------")
    total = 0
    for m in sorted(per_measure.keys()):
        count = per_measure[m]
        total += count
        print(f"{m:7d} | {count:5d}")
    print("--------|------")
    print(f"Total   | {total:5d}")