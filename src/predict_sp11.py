"""
predict_sp11.py — Predict difficulty for ☆11 SP songs (11.0–13.0 scale).

Strategy:
  - Train on ☆12 data (data/features_sp12.csv) using same GBM/ensemble as make_difficulty_table.py
  - For ☆11 songs WITH CPI data: ensemble actual CPI + predicted BPI (same as ☆12 full model)
  - For ☆11 songs WITHOUT CPI: chart-features-only GBM (same as predict_unmatched.py)
  - Level mapping: 11.0–13.0, calibrated against the combined ☆11 distribution

Output: data/difficulty_table_sp11.csv
"""

import re

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

FEATURES = [
    'rand', 'doji', 'kdan', 'tril', 'tate', 'sara', 'cnbs',
    'total_notes', 'duration',
    'peak_density', 'mean_density', 'peak_scratch_density',
    'bpm_min', 'bpm_max', 'bpm_ratio',
]
FEAT_BPI = FEATURES + ['cpi_kojinsa']

GBM_PARAMS = dict(n_estimators=300, max_depth=4, learning_rate=0.05,
                  subsample=0.8, random_state=42)


def zscore_params(v):
    return v.mean(), v.std()


def zscore(v, mu, sigma):
    return (v - mu) / sigma


def map_levels(scores, lo=11.0, hi=13.0, p_lo=5, p_hi=95, step=0.1):
    s_lo = np.percentile(scores, p_lo)
    s_hi = np.percentile(scores, p_hi)
    lvl = lo + (scores - s_lo) / (s_hi - s_lo) * (hi - lo)
    return np.round(np.clip(np.round(lvl / step) * step, lo, hi), 1)


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
    train['cpi_kojinsa'] = train['cpi_exhard'] - train['cpi_hard']

    full_mask = train['bpi_at_aaa'].notna() & train['cpi_hard'].notna()
    full = train[full_mask].dropna(subset=FEAT_BPI + ['bpi_at_aaa', 'bpi_at_9444'])
    print(f'  Training set: {len(full)} songs with BPI+CPI')

    # ── Train BPI prediction models ───────────────────────────────────────────
    print('Training BPI models on ☆12 data ...')
    model_aaa  = GradientBoostingRegressor(**GBM_PARAMS).fit(
        full[FEAT_BPI].values, full['bpi_at_aaa'].values)
    model_9444 = GradientBoostingRegressor(**GBM_PARAMS).fit(
        full[FEAT_BPI].values, full['bpi_at_9444'].values)

    # ── Train chart-features-only models for CPI prediction ──────────────────
    print('Training chart-features-only models ...')
    feat_only_models = {}
    for col in ['bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard']:
        sub = train[FEATURES + [col]].dropna()
        m = GradientBoostingRegressor(**GBM_PARAMS).fit(sub[FEATURES].values, sub[col].values)
        feat_only_models[col] = m

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

    all_df['level'] = map_levels(all_df['difficulty_score'].values, lo=11.0, hi=13.0)
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
