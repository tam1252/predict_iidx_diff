"""
predict_sp11.py — Predict difficulty for ☆11 SP songs (11.0–13.0 scale).

Strategy:
  - Train on ☆12 data (data/features_sp12.csv) using same GBM/ensemble as make_difficulty_table.py
  - For ☆11 songs WITH CPI data: ensemble actual CPI + predicted BPI (same as ☆12 full model)
  - For ☆11 songs WITHOUT CPI: chart-features-only GBM (same as predict_unmatched.py)
  - Level mapping: 11.0–13.0, calibrated against the combined ☆11 distribution

Output: data/difficulty_table_sp11.csv
"""

import json
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'src')
from model_utils import select_best_model
from collect_data import normalize_title, _aggressive_norm

FEATURES = [
    'rand', 'doji', 'kdan', 'tril', 'tate', 'sara', 'cnbs',
    'total_notes', 'duration',
    'peak_density', 'mean_density', 'peak_scratch_density',
    'bpm_min', 'bpm_max', 'bpm_ratio',
]
FEAT_BPI = FEATURES + ['cpi_kojinsa']



def zscore_params(v):
    return v.mean(), v.std()


def zscore(v, mu, sigma):
    return (v - mu) / sigma


def map_levels_sp12_ref(scores, sp12_scores, lo=11.0, hi=13.0, p_lo=5, p_hi=95, step=0.1):
    """Map scores to levels using ☆12 distribution as reference.

    The ☆12 p5→11.5 / p95→13.0 anchors define the scale.
    ☆11 songs with scores below the ☆12 p5 naturally fall to 11.0–11.4.
    """
    s_lo = np.percentile(sp12_scores, p_lo)   # ☆12 p5  → level 11.5
    s_hi = np.percentile(sp12_scores, p_hi)   # ☆12 p95 → level 13.0
    lvl = 11.5 + (scores - s_lo) / (s_hi - s_lo) * 1.5
    return np.round(np.clip(np.round(lvl / step) * step, lo, hi), 1)


def _build_plain_cpi_lookup():
    """Build CPI lookup restricted to non-[L] entries only."""
    with open('data/raw/cpi_raw_dump.json', encoding='utf-8') as f:
        raw = json.load(f)
    headers = [h.lower() for h in raw['headers']]
    plain = {row[0]: dict(zip(headers[1:], row[1:]))
             for row in raw['result'] if not row[0].endswith('[L]')}
    norm    = {normalize_title(t): v for t, v in plain.items()}
    agg     = {_aggressive_norm(t): v for t, v in plain.items()}
    return norm, agg


def _drop_sp12_spl_duplicates(df11, sp12_path='data/features_sp12.csv',
                              unmatched_path='data/difficulty_table_unmatched.csv'):
    """Remove ☆11 A-difficulty songs whose ANOTHER chart is identical to the ☆12 SPL chart.

    Some textage songs share one HTML file for both ANOTHER (☆11) and LEGGENDARIA (☆12).
    When the two charts are truly identical (same total_notes), the ☆11 A row is a
    duplicate of the ☆12 SPL row and should be dropped.
    Songs where ANOTHER != LEGGENDARIA (different note counts) are genuine ☆11 charts
    and should be kept.
    Checks both features_sp12.csv (BPI-matched songs) and difficulty_table_unmatched.csv
    (BPI-unmatched songs that still appear as ☆12 SPL).
    """
    import os
    df12 = pd.read_csv(sp12_path, keep_default_na=False, na_values=[''])
    spl_notes = df12.loc[df12['difficulty'] == 'X'].set_index('filename')['total_notes'].to_dict()

    # Also include unmatched ☆12 SPL songs if filename/total_notes columns are present
    if os.path.exists(unmatched_path):
        uf = pd.read_csv(unmatched_path, keep_default_na=False, na_values=[''])
        if 'filename' in uf.columns and 'total_notes' in uf.columns:
            for _, r in uf[uf['chart_type'] == 'SPL'].iterrows():
                fn = r['filename']
                if fn and fn not in spl_notes:
                    spl_notes[fn] = int(r['total_notes'])

    def _is_true_duplicate(row):
        if row['difficulty'] != 'A':
            return False
        fn = row['filename']
        if fn not in spl_notes:
            return False
        # Drop only when note counts match exactly (truly identical chart)
        return int(row['total_notes']) == int(spl_notes[fn])

    mask = df11.apply(_is_true_duplicate, axis=1)
    n = mask.sum()
    kept = ((df11['difficulty'] == 'A') & df11['filename'].isin(spl_notes) & ~mask).sum()
    print(f'  Dropping {n} ☆11 A-difficulty rows that are ☆12 SPL duplicates '
          f'(keeping {kept} with different charts)')
    return df11[~mask].copy()


def _clear_invalid_cpi(df):
    """Clear CPI columns for A-difficulty songs that only matched a [L] CPI entry.

    The _aggressive_norm function strips ' [L]' suffixes, causing ☆11 ANOTHER charts
    (e.g. SAMURAI-Scramble SPA) to incorrectly match the LEGGENDARIA CPI entry.
    Only keep CPI data when a genuine plain (non-[L]) CPI entry exists.
    """
    plain_norm, plain_agg = _build_plain_cpi_lookup()
    cpi_cols = ['cpi_easy', 'cpi_clear', 'cpi_hard', 'cpi_exhard', 'cpi_fc', 'cpi_kojinsa']
    mask = df['difficulty'] == 'A'
    cleared = 0
    for idx in df[mask].index:
        t = df.at[idx, 'title']
        has_plain = (normalize_title(t) in plain_norm or _aggressive_norm(t) in plain_agg)
        if not has_plain and df.at[idx, 'cpi_hard'] != '':
            for col in cpi_cols:
                if col in df.columns:
                    df.at[idx, col] = np.nan
            cleared += 1
    print(f'  Cleared invalid [L] CPI matches for {cleared} A-difficulty songs')
    return df


def _fix_leggendaria(df):
    """Drop duplicate A-difficulty † entries and reclassify lone LEGGENDARIA charts as SPL."""
    x_titles = set(df.loc[df['difficulty'] == 'X', 'title'])
    dag_mask = (df['difficulty'] == 'A') & df['title'].apply(
        lambda t: bool(re.search(r'†(?:LEGGENDARIA)?$', t)))
    to_drop, to_reclassify = [], []
    for idx in df[dag_mask].index:
        base = re.sub(r'†.*$', '', df.at[idx, 'title']).strip()
        (to_drop if base in x_titles else to_reclassify).append(idx)
    print(f'  Dropping {len(to_drop)} duplicate † entries, reclassifying {len(to_reclassify)} to SPL')
    df = df.drop(to_drop).copy()
    df.loc[to_reclassify, 'difficulty'] = 'X'
    return df


def kojinsa_label(z):
    if pd.isna(z):
        return '—'
    return '高' if z >= 0.8 else ('中' if z >= -0.3 else '低')


def main():
    # ── Load and prepare ☆12 training data ───────────────────────────────────
    print('Loading ☆12 training data ...')
    train = pd.read_csv('data/features_sp12.csv', keep_default_na=False, na_values=[''])
    num_cols = FEATURES + ['cpi_hard', 'cpi_exhard', 'bpi_at_aaa', 'bpi_at_9444', 'bpi_coef']
    for col in num_cols:
        if col in train.columns:
            train[col] = pd.to_numeric(train[col], errors='coerce')
    train['sara'] = train['sara'].clip(upper=100.0)
    train['cpi_kojinsa'] = train['cpi_exhard'] - train['cpi_hard']

    full_mask = train['bpi_at_aaa'].notna() & train['cpi_hard'].notna()
    full = train[full_mask].dropna(subset=FEAT_BPI + ['bpi_at_aaa', 'bpi_at_9444'])
    print(f'  Training set: {len(full)} songs with BPI+CPI')

    # ── Train BPI prediction models ───────────────────────────────────────────
    print('Training BPI models on ☆12 data ...')
    model_aaa  = select_best_model(full[FEAT_BPI].values, full['bpi_at_aaa'].values,  'bpi_at_aaa')
    model_9444 = select_best_model(full[FEAT_BPI].values, full['bpi_at_9444'].values, 'bpi_at_9444')

    # ── Train chart-features-only models for CPI prediction ──────────────────
    print('Training chart-features-only models ...')
    feat_only_models = {}
    for col in ['bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard']:
        sub = train[FEATURES + [col]].dropna()
        feat_only_models[col] = select_best_model(sub[FEATURES].values, sub[col].values, col)

    # ── Z-score parameters from full ☆12 ensemble ────────────────────────────
    bpi_aaa_all  = full['bpi_at_aaa'].values
    bpi_9444_all = full['bpi_at_9444'].values
    cpi_hard_all  = full['cpi_hard'].values
    cpi_exh_all   = full['cpi_exhard'].values

    mu_aaa,  s_aaa  = zscore_params(bpi_aaa_all)
    mu_9444, s_9444 = zscore_params(bpi_9444_all)
    mu_hard, s_hard = zscore_params(cpi_hard_all)
    mu_exh,  s_exh  = zscore_params(cpi_exh_all)

    # Kojinsa z-score params
    koji_full = train[full_mask].dropna(subset=['bpi_coef', 'cpi_kojinsa'])
    mu_coef, s_coef = zscore_params(koji_full['bpi_coef'].values)
    mu_koji, s_koji = zscore_params(koji_full['cpi_kojinsa'].values)

    # ── Load ☆11 features ─────────────────────────────────────────────────────
    print('\nLoading ☆11 features ...')
    df11 = pd.read_csv('data/features_sp11.csv', keep_default_na=False, na_values=[''])
    for col in FEATURES + ['cpi_hard', 'cpi_exhard']:
        if col in df11.columns:
            df11[col] = pd.to_numeric(df11[col], errors='coerce')
    df11['sara'] = df11['sara'].clip(upper=100.0)
    df11 = _drop_sp12_spl_duplicates(df11)
    df11 = _clear_invalid_cpi(df11)
    df11['cpi_kojinsa'] = df11['cpi_exhard'] - df11['cpi_hard']
    print(f'  Total ☆11 songs before dedup: {len(df11)}')
    df11 = _fix_leggendaria(df11)
    print(f'  Total ☆11 songs: {len(df11)}')

    has_cpi = df11['cpi_hard'].notna()
    print(f'  With CPI: {has_cpi.sum()}, without CPI: {(~has_cpi).sum()}')

    # ── Predict for ☆11 songs with CPI ───────────────────────────────────────
    cpi_mask = has_cpi & df11[FEAT_BPI].notna().all(axis=1)
    cpi_df = df11[cpi_mask].copy()
    if not cpi_df.empty:
        X_cpi = cpi_df[FEAT_BPI].values
        pred_aaa  = model_aaa.predict(X_cpi)
        pred_9444 = model_9444.predict(X_cpi)

        z_aaa  = zscore(pred_aaa,                  mu_aaa,  s_aaa)
        z_9444 = zscore(pred_9444,                 mu_9444, s_9444)
        z_hard = zscore(cpi_df['cpi_hard'].values, mu_hard, s_hard)
        z_exh  = zscore(cpi_df['cpi_exhard'].values, mu_exh, s_exh)
        cpi_df['difficulty_score'] = (z_aaa + z_9444 + z_hard + z_exh) / 4.0
        cpi_df['source'] = 'cpi_model'
        cpi_df['bpi_at_aaa_disp']  = np.round(pred_aaa,  1)
        cpi_df['bpi_at_9444_disp'] = np.round(pred_9444, 1)
        cpi_df['bpi_coef_disp']    = np.nan
    print(f'  Predicted (with CPI): {len(cpi_df)}')

    # ── Predict for ☆11 songs without CPI ────────────────────────────────────
    no_cpi_mask = ~has_cpi & df11[FEATURES].notna().all(axis=1)
    no_cpi_df = df11[no_cpi_mask].copy()
    if not no_cpi_df.empty:
        X_nc = no_cpi_df[FEATURES].values
        p_aaa  = feat_only_models['bpi_at_aaa'].predict(X_nc)
        p_9444 = feat_only_models['bpi_at_9444'].predict(X_nc)
        p_hard = feat_only_models['cpi_hard'].predict(X_nc)
        p_exh  = feat_only_models['cpi_exhard'].predict(X_nc)

        z_aaa  = zscore(p_aaa,  mu_aaa,  s_aaa)
        z_9444 = zscore(p_9444, mu_9444, s_9444)
        z_hard = zscore(p_hard, mu_hard, s_hard)
        z_exh  = zscore(p_exh,  mu_exh,  s_exh)
        no_cpi_df['difficulty_score'] = (z_aaa + z_9444 + z_hard + z_exh) / 4.0
        no_cpi_df['source'] = 'chart_features_only'
        no_cpi_df['bpi_at_aaa_disp']  = np.round(p_aaa,  1)
        no_cpi_df['bpi_at_9444_disp'] = np.round(p_9444, 1)
        no_cpi_df['cpi_hard']    = np.round(p_hard, 0)
        no_cpi_df['cpi_exhard']  = np.round(p_exh,  0)
        no_cpi_df['bpi_coef_disp'] = np.nan
    print(f'  Predicted (chart only): {len(no_cpi_df)}')

    # ── Combine and compute levels ────────────────────────────────────────────
    all_df = pd.concat([cpi_df, no_cpi_df], ignore_index=True)

    # Use ☆12 OOF difficulty_scores as the reference distribution
    sp12_ref = pd.read_csv('data/difficulty_scores.csv')['difficulty_score'].values
    all_df['level'] = map_levels_sp12_ref(
        all_df['difficulty_score'].values, sp12_ref, lo=11.0, hi=13.0)
    all_df['chart_type'] = all_df['difficulty'].map({'A': 'SPA', 'X': 'SPL'})

    # Kojinsa for CPI songs
    def _kojinsa_score(row):
        koji = row.get('cpi_kojinsa')
        if pd.isna(koji):
            return np.nan
        z_k = zscore(koji, mu_koji, s_koji)
        return z_k   # bpi_coef not available for ☆11, use CPI kojinsa only

    all_df['kojinsa_score'] = all_df.apply(_kojinsa_score, axis=1)
    all_df['kojinsa'] = all_df['kojinsa_score'].apply(kojinsa_label)

    # ── Save ──────────────────────────────────────────────────────────────────
    out = all_df.sort_values(['level', 'difficulty_score'], ascending=[False, False])
    out['bpi_at_aaa']  = out['bpi_at_aaa_disp'].round(1)
    out['bpi_at_9444'] = out['bpi_at_9444_disp'].round(1)

    save_cols = ['title', 'chart_type', 'level', 'kojinsa',
                 'bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard', 'source']
    out[save_cols].to_csv('data/difficulty_table_sp11.csv', index=False)
    print(f'\nSaved {len(out)} rows → data/difficulty_table_sp11.csv')

    # ── Level distribution ────────────────────────────────────────────────────
    print('\nLevel distribution:')
    dist = out['level'].value_counts().sort_index(ascending=False)
    for lvl, cnt in dist.items():
        print(f'  {lvl:.1f}  {cnt:3d}  {"█" * cnt}')

    print('\nTop 20 hardest:')
    disp_cols = ['title', 'chart_type', 'level', 'kojinsa', 'bpi_at_aaa', 'cpi_hard', 'source']
    print(out.head(20)[disp_cols].to_string(index=False))


if __name__ == '__main__':
    main()
