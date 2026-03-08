"""
make_difficulty_table.py — Generate ☆12 SP difficulty table (11.0–13.0).

For 532 songs with both BPI + CPI data:
  Use actual bpi_at_aaa, bpi_at_9444, cpi_hard, cpi_exhard values.

For 23 songs with CPI only (no BPI data):
  Predict bpi_at_aaa and bpi_at_9444 using GBM trained on the 532 full songs,
  with FEATURES + ['cpi_kojinsa'] as inputs.

Ensemble: z-score of all four signals averaged (same logic as train_model.py).
Level mapping: p5 → 11.0, p95 → 13.0, rounded to 0.25, clipped.

Output: data/difficulty_table.csv
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

FEATURES = [
    'rand', 'doji', 'kdan', 'tril', 'tate', 'sara', 'cnbs',
    'total_notes', 'duration',
    'peak_density', 'mean_density', 'peak_scratch_density',
    'bpm_min', 'bpm_max', 'bpm_ratio',
]
FEAT_BPI = FEATURES + ['cpi_kojinsa']   # add CPI個人差 for BPI prediction


def zscore_params(v):
    return v.mean(), v.std()


def zscore(v, mu, sigma):
    return (v - mu) / sigma


def map_levels(scores, lo=11.0, hi=13.0, p_lo=5, p_hi=95, step=0.1):
    s_lo = np.percentile(scores, p_lo)
    s_hi = np.percentile(scores, p_hi)
    lvl = lo + (scores - s_lo) / (s_hi - s_lo) * (hi - lo)
    return np.clip(np.round(lvl / step) * step, lo, hi)


def kojinsa_label(z):
    if pd.isna(z):
        return '—'
    return '高' if z >= 0.8 else ('中' if z >= -0.3 else '低')


def main():
    df = pd.read_csv('data/features_sp12.csv', keep_default_na=False, na_values=[''])
    num_cols = FEATURES + ['cpi_hard', 'cpi_exhard', 'bpi_at_aaa', 'bpi_at_9444',
                           'bpi_coef', 'bpi_notes', 'bpi_avg', 'bpi_wr']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['cpi_kojinsa'] = df['cpi_exhard'] - df['cpi_hard']

    has_bpi = df['bpi_at_aaa'].notna()
    has_cpi = df['cpi_hard'].notna()
    full_mask = has_bpi & has_cpi
    cpi_only_mask = ~has_bpi & has_cpi

    print(f'Both BPI+CPI: {full_mask.sum()}')
    print(f'CPI only:     {cpi_only_mask.sum()}')

    # ── Train BPI models on full songs ────────────────────────────────────────
    full = df[full_mask].dropna(subset=FEAT_BPI + ['bpi_at_aaa', 'bpi_at_9444'])
    X_full = full[FEAT_BPI].values

    print(f'Training BPI models on {len(full)} songs ...')
    gbm_params = dict(n_estimators=300, max_depth=4, learning_rate=0.05,
                      subsample=0.8, random_state=42)
    model_aaa  = GradientBoostingRegressor(**gbm_params).fit(X_full, full['bpi_at_aaa'].values)
    model_9444 = GradientBoostingRegressor(**gbm_params).fit(X_full, full['bpi_at_9444'].values)

    # ── Predict BPI for CPI-only songs ────────────────────────────────────────
    cpi_only = df[cpi_only_mask].dropna(subset=FEAT_BPI)
    X_cpi = cpi_only[FEAT_BPI].values
    pred_aaa_cpi  = model_aaa.predict(X_cpi)
    pred_9444_cpi = model_9444.predict(X_cpi)
    print(f'Predicted BPI for {len(cpi_only)} CPI-only songs')

    # ── Compute ensemble ──────────────────────────────────────────────────────
    # Use actual values for full songs; predicted for CPI-only
    # Z-score parameters derived from all 555 combined values

    bpi_aaa_all  = np.concatenate([full['bpi_at_aaa'].values,  pred_aaa_cpi])
    bpi_9444_all = np.concatenate([full['bpi_at_9444'].values, pred_9444_cpi])
    cpi_hard_all  = np.concatenate([full['cpi_hard'].values,   cpi_only['cpi_hard'].values])
    cpi_exh_all   = np.concatenate([full['cpi_exhard'].values, cpi_only['cpi_exhard'].values])

    mu_aaa,  s_aaa  = zscore_params(bpi_aaa_all)
    mu_9444, s_9444 = zscore_params(bpi_9444_all)
    mu_hard, s_hard = zscore_params(cpi_hard_all)
    mu_exh,  s_exh  = zscore_params(cpi_exh_all)

    z_aaa_f  = zscore(full['bpi_at_aaa'].values,  mu_aaa,  s_aaa)
    z_9444_f = zscore(full['bpi_at_9444'].values, mu_9444, s_9444)
    z_hard_f = zscore(full['cpi_hard'].values,    mu_hard, s_hard)
    z_exh_f  = zscore(full['cpi_exhard'].values,  mu_exh,  s_exh)
    diff_full = (z_aaa_f + z_9444_f + z_hard_f + z_exh_f) / 4.0

    z_aaa_c  = zscore(pred_aaa_cpi,               mu_aaa,  s_aaa)
    z_9444_c = zscore(pred_9444_cpi,              mu_9444, s_9444)
    z_hard_c = zscore(cpi_only['cpi_hard'].values,  mu_hard, s_hard)
    z_exh_c  = zscore(cpi_only['cpi_exhard'].values, mu_exh, s_exh)
    diff_cpi = (z_aaa_c + z_9444_c + z_hard_c + z_exh_c) / 4.0

    # ── Kojinsa score ─────────────────────────────────────────────────────────
    # Use bpi_coef (inverted) and cpi_kojinsa from full songs only
    koji_full = df[full_mask].dropna(subset=['bpi_coef', 'cpi_kojinsa'])
    mu_coef, s_coef = zscore_params(koji_full['bpi_coef'].values)
    mu_koji, s_koji = zscore_params(koji_full['cpi_kojinsa'].values)

    def kojinsa_score(row):
        if pd.isna(row.get('bpi_coef')) or pd.isna(row.get('cpi_kojinsa')):
            return np.nan
        z_c = zscore(-row['bpi_coef'],    mu_coef, s_coef)
        z_k = zscore(row['cpi_kojinsa'],  mu_koji, s_koji)
        return (z_c + z_k) / 2.0

    # ── Assemble output dataframe ─────────────────────────────────────────────
    full_out = full.copy()
    full_out['difficulty_score'] = diff_full
    full_out['bpi_at_aaa_disp']  = full_out['bpi_at_aaa']
    full_out['bpi_at_9444_disp'] = full_out['bpi_at_9444']
    full_out['source']           = 'full_model'
    full_out['kojinsa_score']    = full_out.apply(kojinsa_score, axis=1)

    cpi_out = cpi_only.copy()
    cpi_out['difficulty_score'] = diff_cpi
    cpi_out['bpi_at_aaa_disp']  = pred_aaa_cpi
    cpi_out['bpi_at_9444_disp'] = pred_9444_cpi
    cpi_out['source']           = 'cpi_only_predicted'
    cpi_out['kojinsa_score']    = np.nan  # no bpi_coef for CPI-only songs

    all_df = pd.concat([full_out, cpi_out], ignore_index=True)
    all_df['level'] = map_levels(all_df['difficulty_score'].values)
    all_df['kojinsa'] = all_df['kojinsa_score'].apply(kojinsa_label)

    # ── Save ──────────────────────────────────────────────────────────────────
    out = all_df.sort_values(['level', 'difficulty_score'], ascending=[False, False])
    out['bpi_at_aaa']  = out['bpi_at_aaa_disp'].round(1)
    out['bpi_at_9444'] = out['bpi_at_9444_disp'].round(1)

    # Normalize chart type notation
    out['chart_type'] = out['difficulty'].map({'A': 'SPA', 'X': 'SPL'})

    save_cols = ['title', 'chart_type', 'level', 'kojinsa',
                 'bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard', 'source']
    out[save_cols].to_csv(
        'data/difficulty_table.csv', index=False)
    print(f'Saved {len(out)} rows → data/difficulty_table.csv')

    # ── Level distribution ────────────────────────────────────────────────────
    print('\nLevel distribution:')
    dist = out['level'].value_counts().sort_index(ascending=False)
    for lvl, cnt in dist.items():
        bar = '█' * cnt
        print(f'  {lvl:.2f}  {cnt:3d}  {bar}')

    # ── Show tables ───────────────────────────────────────────────────────────
    disp_cols = ['title', 'chart_type', 'level', 'kojinsa', 'bpi_at_aaa', 'cpi_hard', 'source']
    out_disp = out[save_cols]

    print('\nTop 20 hardest:')
    print(out_disp.head(20)[disp_cols].to_string(index=False))

    print('\nBottom 15 easiest:')
    print(out_disp.tail(15)[disp_cols].to_string(index=False))

    print('\nCPI-only predicted songs:')
    predicted = out_disp[out_disp['source'].str.startswith('cpi_only')]
    print(predicted.sort_values('level', ascending=False)[disp_cols].to_string(index=False))


if __name__ == '__main__':
    main()
