import math
import re
from textage_parser import LNDEF

# ---------------------------------------------------------------------------
# Phase 2: Density Analysis
# ---------------------------------------------------------------------------

def build_time_map(
    notes: list[dict],
    measure_lens: dict,
    bpm_changes: list[dict],
    bpm_base: str,
    lndef: int = LNDEF,
) -> list[dict]:
    """Assign a real timestamp (seconds) to every note.

    Uses BPM change events (soflan) to convert score position → real time.
    Returns notes with an added 'time' field (float, seconds from song start).

    BPM change format: [{measure, pos, bpm}] sorted by (measure, pos).
    bpm_base: raw string like "157" or "10～166" – used as the initial BPM.
    """
    # Parse initial BPM from bpm_base
    bpm_str = re.sub(r'～.*', '', bpm_base).strip()  # take the first value
    try:
        initial_bpm = float(bpm_str)
    except ValueError:
        initial_bpm = 120.0

    # If the first BPM change is at the very start (measure=1, pos=0),
    # use it as the true initial BPM (bpm_base min value may be a slow soflan)
    if bpm_changes and bpm_changes[0]['measure'] == 1 and bpm_changes[0]['pos'] == 0:
        initial_bpm = float(bpm_changes[0]['bpm'])

    # Build a flat list of (abs_pos, bpm) breakpoints
    # abs_pos: cumulative position in score units (same scale as note pos)
    def measure_to_abs(measure: int, pos: int) -> float:
        """Convert (measure, intra-measure pos) to absolute score position."""
        result = 0.0
        for m in range(1, measure):
            result += measure_lens.get(m, lndef)
        result += pos
        return result

    def pos_to_beats(delta_pos: float, seg_lndef: float) -> float:
        """Convert delta score-position to beats, accounting for time signature.
        Each measure has `ln_n` pos units. The ratio ln_n/lndef gives the
        time-signature multiplier (e.g. 0.75 for 3/4, 1.25 for 5/4).
        1 measure = 4 beats in 4/4, so beats = delta_pos / lndef * 4.
        For other time signatures: beats = delta_pos / seg_lndef * 4 * (seg_lndef/lndef)
        which simplifies to delta_pos * 4 / lndef — always divide by global lndef.
        """
        return delta_pos * 4.0 / lndef

    # Breakpoints: [(abs_pos, bpm), ...]
    breakpoints = [(0.0, initial_bpm)]
    for chg in bpm_changes:
        abs_pos = measure_to_abs(chg['measure'], chg['pos'])
        breakpoints.append((abs_pos, chg['bpm']))
    breakpoints.sort(key=lambda x: x[0])

    # Remove duplicate positions (last one wins)
    deduped = {}
    for abs_pos, bpm in breakpoints:
        deduped[abs_pos] = bpm
    breakpoints = sorted(deduped.items())

    # Precompute cumulative real time at each breakpoint
    # time[i] = real time (seconds) at breakpoints[i]
    bp_times = [0.0]
    for i in range(1, len(breakpoints)):
        prev_pos, prev_bpm = breakpoints[i - 1]
        curr_pos, _ = breakpoints[i]
        delta_pos = curr_pos - prev_pos
        # 1 measure = lndef pos units = 4 beats → each pos unit = 4/lndef beats
        beats = delta_pos * 4.0 / lndef
        seconds = beats * 60.0 / prev_bpm
        bp_times.append(bp_times[-1] + seconds)

    def abs_pos_to_time(abs_pos: float) -> float:
        """Interpolate real time for a given absolute score position."""
        # Find the breakpoint segment
        idx = 0
        for i in range(len(breakpoints) - 1):
            if breakpoints[i + 1][0] <= abs_pos:
                idx = i + 1
            else:
                break
        seg_pos, seg_bpm = breakpoints[idx]
        delta_pos = abs_pos - seg_pos
        beats = delta_pos * 4.0 / lndef
        seconds = beats * 60.0 / seg_bpm
        return bp_times[idx] + seconds

    # Assign timestamps to notes
    timed_notes = []
    for note in notes:
        abs_pos = measure_to_abs(note['measure'], note['pos'])
        t = abs_pos_to_time(abs_pos)
        timed_notes.append({**note, 'time': t})

    return timed_notes


def analyze_density(
    parse_result: dict,
    window_sec: float = 5.0,
    step_sec: float = 1.0,
) -> dict:
    """Compute note density metrics from a parse_html() result.

    Parameters
    ----------
    parse_result : dict
        Output of parse_html().
    window_sec : float
        Sliding window size in seconds for density calculation.
    step_sec : float
        Step size between windows in seconds.

    Returns
    -------
    dict with:
        'duration'        : total song duration in seconds
        'timeline'        : list of {time, density, scratch_density}
                            density = notes/sec (all keys) in window
                            scratch_density = notes/sec (key==0) in window
        'peak_density'    : float  (notes/sec, all keys)
        'peak_time'       : float  (seconds, center of peak window)
        'peak_scratch_density' : float
        'peak_scratch_time'    : float
        'mean_density'    : float  (average over all windows with notes)
    """
    lndef = parse_result.get('lndef', LNDEF)

    timed_notes = build_time_map(
        notes=parse_result['notes'],
        measure_lens=parse_result['measure_lens'],
        bpm_changes=parse_result['bpm_changes'],
        bpm_base=parse_result['bpm_base'],
        lndef=lndef,
    )

    if not timed_notes:
        return {
            'duration': 0.0, 'timeline': [],
            'peak_density': 0.0, 'peak_time': 0.0,
            'peak_scratch_density': 0.0, 'peak_scratch_time': 0.0,
            'mean_density': 0.0,
        }

    all_times   = [n['time'] for n in timed_notes]
    scratch_times = [n['time'] for n in timed_notes if n['key'] == 0]
    duration = max(all_times)

    timeline = []
    t = 0.0
    while t <= duration:
        lo, hi = t - window_sec / 2, t + window_sec / 2
        count   = sum(1 for x in all_times   if lo <= x < hi)
        scratch = sum(1 for x in scratch_times if lo <= x < hi)
        timeline.append({
            'time': round(t, 3),
            'density': round(count / window_sec, 4),
            'scratch_density': round(scratch / window_sec, 4),
        })
        t += step_sec

    peak = max(timeline, key=lambda x: x['density'])
    peak_sc = max(timeline, key=lambda x: x['scratch_density'])
    non_zero = [x['density'] for x in timeline if x['density'] > 0]

    return {
        'duration': round(duration, 2),
        'timeline': timeline,
        'peak_density': peak['density'],
        'peak_time': peak['time'],
        'peak_scratch_density': peak_sc['scratch_density'],
        'peak_scratch_time': peak_sc['time'],
        'mean_density': round(sum(non_zero) / len(non_zero), 4) if non_zero else 0.0,
    }


# ---------------------------------------------------------------------------
# Phase 2: Pattern Detection
# ---------------------------------------------------------------------------

def detect_patterns(
    parse_result: dict,
    trill_min: int = 4,
    stairs_min: int = 4,
    jacks_min: int = 2,
) -> dict:
    """Detect difficult patterns in a parsed score.

    Parameters
    ----------
    parse_result : dict
        Output of parse_html().
    trill_min : int
        Minimum length to classify as trill/stairs (default 4).
    jacks_min : int
        Minimum consecutive notes on same lane to classify as jack (default 2).

    Returns
    -------
    dict with keys:
        'chords'       : list of {measure, pos, keys}  -- 2+ keys at same pos
        'scratch_chords': list of {measure, pos, keys} -- scratch + key(s) together
        'trills'       : list of {measure_start, pos_start, measure_end, pos_end, keys, length}
        'stairs'       : list of {measure_start, pos_start, measure_end, pos_end, keys, length}
        'jacks'        : list of {measure_start, pos_start, measure_end, pos_end, key, length}
        'summary'      : dict of counts per pattern type
    """
    notes = parse_result['notes']
    lndef = parse_result.get('lndef', LNDEF)

    # Jack threshold: BPM120 16th note interval in pos units
    # BPM120 → 1 beat = lndef/4 pos, 16th = lndef/16
    jack_threshold = lndef / 8  # BPM120 16分音符間隔

    # --- Build sorted list of (measure, pos, key) for normal+cn_start notes only ---
    # Use only note onsets (normal and cn_start) for pattern detection
    onset_notes = [n for n in notes if n['type'] in ('normal', 'cn_start')]
    onset_notes.sort(key=lambda n: (n['measure'], n['pos'], n['key']))

    # Group by (measure, pos) → chord groups
    from itertools import groupby
    def mp_key(n):
        return (n['measure'], n['pos'])

    chords = []
    scratch_chords = []
    for (measure, pos), group in groupby(onset_notes, key=mp_key):
        keys = sorted(set(n['key'] for n in group))
        if len(keys) >= 2:
            entry = {'measure': measure, 'pos': pos, 'keys': keys}
            chords.append(entry)
            if 0 in keys:
                scratch_chords.append(entry)

    # --- Flatten onset notes to a timeline for sequential pattern detection ---
    # For trill/stairs/jacks we need single-key events in order
    # Expand chords: each key at a position is a separate event
    events = []
    for n in onset_notes:
        events.append((n['measure'], n['pos'], n['key']))
    # events is already sorted

    # --- Jack detection ---
    # Same key appearing consecutively with interval < jack_threshold pos units
    jacks = []
    # Per-lane tracking
    lane_events = {}  # key → list of (measure, pos)
    for measure, pos, key in events:
        if key not in lane_events:
            lane_events[key] = []
        lane_events[key].append((measure, pos))

    def pos_diff(m1, p1, m2, p2, measure_lens, lndef):
        """Absolute pos difference between two notes."""
        abs1 = sum(measure_lens.get(m, lndef) for m in range(1, m1)) + p1
        abs2 = sum(measure_lens.get(m, lndef) for m in range(1, m2)) + p2
        return abs2 - abs1

    measure_lens = parse_result['measure_lens']

    for key, lane_evts in lane_events.items():
        if len(lane_evts) < jacks_min:
            continue
        i = 0
        while i < len(lane_evts):
            # Start a new jack run
            run = [lane_evts[i]]
            j = i + 1
            while j < len(lane_evts):
                m1, p1 = lane_evts[j-1]
                m2, p2 = lane_evts[j]
                diff = pos_diff(m1, p1, m2, p2, measure_lens, lndef)
                if diff < jack_threshold:
                    run.append(lane_evts[j])
                    j += 1
                else:
                    break
            if len(run) >= jacks_min:
                jacks.append({
                    'measure_start': run[0][0], 'pos_start': run[0][1],
                    'measure_end':   run[-1][0], 'pos_end':   run[-1][1],
                    'key': key, 'length': len(run),
                })
                i = j  # skip past this run
            else:
                i += 1

    # --- Trill detection ---
    # Strict alternation: A B A B A B ... (exactly 2 distinct keys)
    # Only consider key 1-7 (not scratch)
    # Interval constraint: consecutive notes must be within jack_threshold * 4 pos units
    # (= BPM120 8th note), preventing false positives across sparse sections
    key_events = [(m, p, k) for m, p, k in events if k > 0]
    stair_trill_max_interval = jack_threshold * 4  # BPM120 8分音符相当

    def ke_pos_diff(a, b):
        """Absolute pos diff between two key_events."""
        return pos_diff(a[0], a[1], b[0], b[1], measure_lens, lndef)

    trills = []
    i = 0
    while i < len(key_events) - trill_min + 1:
        ka = key_events[i][2]
        if i + 1 >= len(key_events):
            break
        kb = key_events[i+1][2]
        if ka == kb or ke_pos_diff(key_events[i], key_events[i+1]) > stair_trill_max_interval:
            i += 1
            continue
        run = [key_events[i], key_events[i+1]]
        j = i + 2
        expected = ka
        while j < len(key_events):
            mk, pk, kk = key_events[j]
            interval = ke_pos_diff(run[-1], key_events[j])
            if kk == expected and interval <= stair_trill_max_interval:
                run.append(key_events[j])
                expected = kb if expected == ka else ka
                j += 1
            else:
                break
        if len(run) >= trill_min:
            trills.append({
                'measure_start': run[0][0],  'pos_start': run[0][1],
                'measure_end':   run[-1][0], 'pos_end':   run[-1][1],
                'keys': [ka, kb], 'length': len(run),
            })
            i = j
        else:
            i += 1

    # --- Stairs detection ---
    # Consecutive notes all on different keys (no immediate key repeat),
    # more than 2 distinct keys (to exclude trills), key 1-7 only
    # Interval constraint: same as trill
    stairs = []
    i = 0
    while i < len(key_events) - stairs_min + 1:
        run = [key_events[i]]
        j = i + 1
        while j < len(key_events):
            prev_key = run[-1][2]
            curr_key = key_events[j][2]
            interval = ke_pos_diff(run[-1], key_events[j])
            if curr_key == prev_key or interval > stair_trill_max_interval:
                break
            run.append(key_events[j])
            j += 1
        if len(run) >= stairs_min:
            distinct_keys = set(n[2] for n in run)
            if len(distinct_keys) > 2:  # exclude trills
                stairs.append({
                    'measure_start': run[0][0],  'pos_start': run[0][1],
                    'measure_end':   run[-1][0], 'pos_end':   run[-1][1],
                    'keys': sorted(distinct_keys), 'length': len(run),
                })
                i = j
            else:
                i += 1
        else:
            i += 1

    summary = {
        'chord_count':         len(chords),
        'scratch_chord_count': len(scratch_chords),
        'trill_count':         len(trills),
        'trill_total_notes':   sum(t['length'] for t in trills),
        'stairs_count':        len(stairs),
        'stairs_total_notes':  sum(s['length'] for s in stairs),
        'jack_count':          len(jacks),
        'jack_total_notes':    sum(j['length'] for j in jacks),
    }

    return {
        'chords':         chords,
        'scratch_chords': scratch_chords,
        'trills':         trills,
        'stairs':         stairs,
        'jacks':          jacks,
        'summary':        summary,
    }


# ---------------------------------------------------------------------------
# Phase 2: Textage-compatible Score Points
# ---------------------------------------------------------------------------

def _stat_calc_diff(bpm: float) -> float:
    """BPM-adjusted lookahead window (seconds). Mirrors bms2jsh.js stat_calc_diff."""
    stat_dif = 0.2
    if bpm > 180: return stat_dif - 0.08
    if bpm > 100: return stat_dif - (bpm - 100) * 0.001
    return stat_dif

def _stat_calc_diff_t(bpm: float) -> float:
    """Wider lookahead for tsub/ssub. Mirrors bms2jsh.js stat_calc_diff_t."""
    stat_dif = 0.28
    if bpm > 180: return stat_dif - 0.08
    if bpm > 100: return stat_dif - (bpm - 100) * 0.001
    return stat_dif


def calc_textage_scores(parse_result: dict) -> dict:
    """Compute textage.cc-compatible score points for each pattern category.

    Mirrors bms2jsh.js stat_check_* + stat_result() logic exactly.

    Returns
    -------
    dict with:
        'rand'  : float  乱打 pt
        'doji'  : float  同時 pt
        'kdan'  : float  階段 pt
        'tril'  : float  トリル pt
        'tate'  : float  縦連 pt
        'sara'  : float  皿 pt
        'cnbs'  : float  ＣＮ pt
        'total' : float  合計 pt
        'notes' : int    ノーツ数 (P1)
        'oabmb' : float  補正ノーツ数
    """
    from textage_parser import LNDEF

    notes_list = parse_result['notes']
    lndef = parse_result.get('lndef', LNDEF)
    bpm_changes = parse_result['bpm_changes']
    bpm_base = parse_result['bpm_base']
    measure_lens = parse_result['measure_lens']

    # Build timed note list (onset only, P1 side = all SP notes)
    timed = build_time_map(
        notes=notes_list,
        measure_lens=measure_lens,
        bpm_changes=bpm_changes,
        bpm_base=bpm_base,
        lndef=lndef,
    )
    onset = [n for n in timed if n['type'] in ('normal', 'cn_start')]
    onset.sort(key=lambda n: (n['time'], n['key']))

    # CN width (seconds) per note for cnbs
    cn_starts = {(n['measure'], n['pos'], n['key']): n['time']
                 for n in timed if n['type'] == 'cn_start'}
    cn_ends   = {(n['measure'], n['pos'], n['key']): n['time']
                 for n in timed if n['type'] == 'cn_end'}

    # Build stat_list: list of dicts with time, key, bpm, wide(CN duration)
    # Determine BPM at each note's time using bpm_changes
    def bpm_at_time(t: float, bp_timeline: list) -> float:
        bpm = bp_timeline[0][1] if bp_timeline else 120.0
        for bp_t, bp_bpm in bp_timeline:
            if bp_t <= t:
                bpm = bp_bpm
            else:
                break
        return bpm

    # Build (time, bpm) breakpoint list for quick lookup
    initial_bpm_str = re.sub(r'～.*', '', bpm_base).strip()
    try:
        initial_bpm = float(initial_bpm_str)
    except ValueError:
        initial_bpm = 120.0
    if bpm_changes and bpm_changes[0]['measure'] == 1 and bpm_changes[0]['pos'] == 0:
        initial_bpm = float(bpm_changes[0]['bpm'])

    def measure_to_abs(measure, pos):
        result = 0.0
        for m in range(1, measure):
            result += measure_lens.get(m, lndef)
        return result + pos

    def abs_pos_to_time_fn(bkpts, bp_times_list):
        def fn(abs_pos):
            idx = 0
            for i in range(len(bkpts) - 1):
                if bkpts[i + 1][0] <= abs_pos:
                    idx = i + 1
                else:
                    break
            seg_pos, seg_bpm = bkpts[idx]
            delta_pos = abs_pos - seg_pos
            beats = delta_pos * 4.0 / lndef
            return bp_times_list[idx] + beats * 60.0 / seg_bpm
        return fn

    # Rebuild breakpoints (same as build_time_map)
    bkpts = [(0.0, initial_bpm)]
    for chg in bpm_changes:
        bkpts.append((measure_to_abs(chg['measure'], chg['pos']), float(chg['bpm'])))
    bkpts.sort(key=lambda x: x[0])
    deduped = {}
    for ap, bpm in bkpts:
        deduped[ap] = bpm
    bkpts = sorted(deduped.items())
    bp_times_list = [0.0]
    for i in range(1, len(bkpts)):
        pp, pb = bkpts[i-1]
        cp, _ = bkpts[i]
        beats = (cp - pp) * 4.0 / lndef
        bp_times_list.append(bp_times_list[-1] + beats * 60.0 / pb)

    # BPM timeline: [(time, bpm), ...]
    bp_timeline = [(bp_times_list[i], bkpts[i][1]) for i in range(len(bkpts))]

    # Build stat nodes
    stat = []
    for n in onset:
        bpm = bpm_at_time(n['time'], bp_timeline)
        wide = 0.0
        if n['type'] == 'cn_start':
            # find matching cn_end by key and nearest end time >= start
            key_ends = [(t, k) for (m, p, k), t in cn_ends.items() if k == n['key'] and t >= n['time']]
            if key_ends:
                end_t = min(key_ends, key=lambda x: abs(x[0] - n['time']))[0]
                wide = end_t - n['time']
        stat.append({
            'time': n['time'],
            'key':  n['key'],
            'bpm':  bpm,
            'wide': wide,
            # score accumulators
            'doji': 0.0, 'kdan': 0.0, 'tril': 0.0,
            'tate': 0.0, 'rand': 0.0, 'sara': 0.0,
            'cnbs': 0.0, 'tsub': 0.0, 'ssub': 0.0,
            'dsub': 0, 'sdep': 0,
        })

    n_stat = len(stat)

    def search_ahead(key, base_idx, width):
        """Find next node after base_idx with given key within time window."""
        base_time = stat[base_idx]['time']
        for i in range(base_idx + 1, n_stat):
            if stat[i]['time'] > base_time + width:
                break
            if stat[i]['key'] == key and stat[i]['time'] > base_time:
                return i
        return None

    # --- stat_check_doji ---
    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] == 0 or nd['doji']: continue
        if i + 1 < n_stat and stat[i+1]['time'] == nd['time']:
            depth = 1
            j = i + 1
            while j + 1 < n_stat and stat[j+1]['time'] == stat[j]['time']:
                depth += 1
                j += 1
            nd['doji'] = 0.5
            nd['dsub'] = depth
            for k in range(i+1, i+1+depth):
                if k < n_stat:
                    stat[k]['doji'] = 0.5 * depth
                    stat[k]['dsub'] = depth

    # --- stat_check_tate (縦連) ---
    def tate_depth(depth, base_idx, key):
        nd = stat[base_idx]
        nxt = search_ahead(key, base_idx, _stat_calc_diff(nd['bpm']))
        if nxt:
            depth = tate_depth(depth + 1, nxt, key)
        if depth >= 1:
            nd['tate'] = (depth + 1) / 2
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] == 0 or nd['tate']: continue
        nxt = search_ahead(nd['key'], i, _stat_calc_diff(nd['bpm']))
        if nxt:
            depth = tate_depth(1, nxt, nd['key'])
            if depth >= 1:
                nd['tate'] = 2 + (depth + 1) / 2

    # --- stat_check_tril (トリル) ---
    def tril_depth(depth, base_idx, key):
        nd = stat[base_idx]
        nxt = search_ahead(key, base_idx, _stat_calc_diff(nd['bpm']))
        if nxt:
            depth = tril_depth(depth + 1, nxt, stat[base_idx]['key'])
        if depth >= 3:
            nd['tril'] = 0.5 + depth * 0.125
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] == 0 or (nd['tate'] and nd['doji']): continue
        for ck_key in range(1, 8):
            if ck_key == nd['key']: continue
            nxt = search_ahead(ck_key, i, _stat_calc_diff(nd['bpm']))
            if nxt:
                depth = tril_depth(1, nxt, nd['key'])
                if depth >= 3:
                    if not nd['tril']:
                        nd['tril'] = 3
                break  # only first matching key

    # --- stat_check_kdan (階段) ---
    def kdan_depth_left(depth, base_idx):
        nd = stat[base_idx]
        for ck_key in range(nd['key'] - 1, 0, -1):
            nxt = search_ahead(ck_key, base_idx, _stat_calc_diff(nd['bpm']))
            if nxt:
                depth = kdan_depth_left(depth + 1, nxt)
                break
        if depth >= 2:
            nd['kdan'] = 0.75
        return depth

    def kdan_depth_right(depth, base_idx):
        nd = stat[base_idx]
        for ck_key in range(nd['key'] + 1, 8):
            nxt = search_ahead(ck_key, base_idx, _stat_calc_diff(nd['bpm']))
            if nxt:
                depth = kdan_depth_right(depth + 1, nxt)
                break
        if depth >= 2:
            nd['kdan'] = 0.75
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] == 0 or (nd['tate'] and nd['doji']): continue
        if nd['key'] >= 3:
            for ck_key in range(nd['key'] - 1, 1, -1):
                nxt = search_ahead(ck_key, i, _stat_calc_diff(nd['bpm']))
                if nxt:
                    if kdan_depth_left(1, nxt) >= 2:
                        nd['kdan'] = 1
                    break
        if nd['key'] <= 5:
            for ck_key in range(nd['key'] + 1, 7):
                nxt = search_ahead(ck_key, i, _stat_calc_diff(nd['bpm']))
                if nxt:
                    if kdan_depth_right(1, nxt) >= 2:
                        nd['kdan'] = 1
                    break

    # --- stat_check_rand (乱打) ---
    def rand_depth_left(depth, base_idx):
        nd = stat[base_idx]
        for ck_key in range(nd['key'] - 1, 0, -1):
            nxt = search_ahead(ck_key, base_idx, _stat_calc_diff(nd['bpm']))
            if nxt:
                depth = rand_depth_right(depth + 1, nxt)
                break
        if depth >= 2:
            nd['rand'] = 0.75
        return depth

    def rand_depth_right(depth, base_idx):
        nd = stat[base_idx]
        for ck_key in range(nd['key'] + 1, 8):
            nxt = search_ahead(ck_key, base_idx, _stat_calc_diff(nd['bpm']))
            if nxt:
                depth = rand_depth_left(depth + 1, nxt)
                break
        if depth >= 2:
            nd['rand'] = 0.75
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] == 0 or nd['tril']: continue
        if nd['key'] >= 2:
            for ck_key in range(nd['key'] - 1, 0, -1):
                nxt = search_ahead(ck_key, i, _stat_calc_diff(nd['bpm']))
                if nxt:
                    if rand_depth_right(1, nxt) >= 2:
                        nd['rand'] = 1
                    break
        if nd['key'] <= 6:
            for ck_key in range(nd['key'] + 1, 8):
                nxt = search_ahead(ck_key, i, _stat_calc_diff(nd['bpm']))
                if nxt:
                    if rand_depth_left(1, nxt) >= 2:
                        nd['rand'] = 1
                    break

    # --- stat_check_sara (皿) ---
    def sara_depth(depth, base_idx):
        nd = stat[base_idx]
        nxt = search_ahead(0, base_idx, _stat_calc_diff(nd['bpm']))
        if nxt:
            depth = sara_depth(depth + 1, nxt)
        if depth >= 1:
            nd['sara'] = (depth + 1) / 4
            nd['sdep'] = depth
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] != 0 or nd['sara']: continue
        nxt = search_ahead(0, i, _stat_calc_diff(nd['bpm']))
        if nxt:
            depth = sara_depth(1, nxt)
            if depth >= 1:
                nd['sara'] = 2 + (depth + 1) / 2
                nd['sdep'] = depth
        else:
            nd['sara'] = 0.75

    # --- stat_check_cnbs (ＣＮ) ---
    playt = max((n['time'] for n in timed), default=1.0)
    for nd in stat:
        if nd['wide']:
            nd['cnbs'] = (nd['wide'] + 0.3) / playt

    # --- Accumulate totals ---
    stat_rand = sum(nd['rand'] for nd in stat)
    stat_doji = sum(nd['doji'] for nd in stat)
    stat_kdan = sum(nd['kdan'] for nd in stat)
    stat_tril = sum(nd['tril'] for nd in stat)
    stat_tate = sum(nd['tate'] for nd in stat)
    stat_sara = sum(nd['sara'] for nd in stat)
    stat_cnbs = sum(nd['cnbs'] for nd in stat)

    # tsub contributes to tate in stat_result
    def tsub_depth(depth, base_idx, key):
        nd = stat[base_idx]
        nxt = search_ahead(key, base_idx, _stat_calc_diff_t(nd['bpm']))
        if nxt:
            depth = tsub_depth(depth + 1, nxt, key)
        if depth >= 1:
            nd['tsub'] = (depth + 1) / 4
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] == 0 or nd['tate']: continue
        nxt = search_ahead(nd['key'], i, _stat_calc_diff_t(nd['bpm']))
        if nxt:
            depth = tsub_depth(1, nxt, nd['key'])
            if depth >= 1:
                nd['tsub'] = 1 + (depth + 1) / 4

    # ssub contributes to sara
    def ssub_depth(depth, base_idx):
        nd = stat[base_idx]
        nxt = search_ahead(0, base_idx, 1.6 * _stat_calc_diff_t(nd['bpm']))
        if nxt:
            depth = ssub_depth(depth + 1, nxt)
        if depth >= 1:
            nd['ssub'] = 0.5
        return depth

    for i in range(n_stat):
        nd = stat[i]
        if nd['key'] != 0 or nd['sdep']: continue
        nxt = search_ahead(0, i, 1.6 * _stat_calc_diff_t(nd['bpm']))
        if nxt:
            depth = ssub_depth(1, nxt)
            if depth >= 1:
                nd['ssub'] = 0.5

    # stat_result: tsub contributes to tate, ssub to sara
    for nd in stat:
        if nd['tsub'] and nd['dsub'] < 2:
            stat_tate += nd['tsub']
        if nd['ssub'] and not nd['sdep']:
            stat_sara += nd['ssub']

    # Score formula: oabmb = notes>800 ? (notes-800)/2+800 : notes
    oanotes = len(onset)
    oabmb = (oanotes - 800) / 2 + 800 if oanotes > 800 else oanotes
    oabmb = max(oabmb, 1)

    def to_pt(val, use_oabmb=True):
        base = oabmb if use_oabmb else 1
        return round(math.ceil(1000 * val / base) / 10, 1)

    return {
        'rand':  to_pt(stat_rand),
        'doji':  to_pt(stat_doji),
        'kdan':  to_pt(stat_kdan),
        'tril':  to_pt(stat_tril),
        'tate':  to_pt(stat_tate),
        'sara':  to_pt(stat_sara),
        'cnbs':  round(math.ceil(1000 * stat_cnbs) / 10, 1),  # CN uses raw value
        'total': round(sum([
            to_pt(stat_rand), to_pt(stat_doji), to_pt(stat_kdan),
            to_pt(stat_tril), to_pt(stat_tate), to_pt(stat_sara),
            round(math.ceil(1000 * stat_cnbs) / 10, 1)
        ]), 1),
        'notes': oanotes,
        'oabmb': round(oabmb, 1),
    }