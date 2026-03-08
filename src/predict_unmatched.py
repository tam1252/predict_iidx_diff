"""
predict_unmatched.py — Fetch chart features for unmatched ☆12 songs and predict difficulty.

Steps:
1. Read data/unmatched_sp12.txt (80 songs without CPI/BPI data)
2. Fetch score data from textage.cc and compute chart features
3. Train models on FEATURES only (no CPI/BPI cross-source features)
   using data/features_sp12.csv as training data
4. Predict difficulty_score and map to 11.0–13.0 level
5. Save to data/difficulty_table_unmatched.csv

Note: Without CPI/BPI data, accuracy is lower (R²~0.4–0.5 from chart features only).
"""

import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold

sys.path.insert(0, 'src')
sys.path.insert(0, 'src/textage')

from collect_data import compute_features
from textage_parser import get_score_data

FEATURES = [
    'rand', 'doji', 'kdan', 'tril', 'tate', 'sara', 'cnbs',
    'total_notes', 'duration',
    'peak_density', 'mean_density', 'peak_scratch_density',
    'bpm_min', 'bpm_max', 'bpm_ratio',
]

GBM_PARAMS = dict(n_estimators=300, max_depth=4, learning_rate=0.05,
                  subsample=0.8, random_state=42)


def map_levels(scores, ref_scores, lo=11.5, hi=13.0, p_lo=5, p_hi=95, step=0.1):
    """Map scores to levels using reference distribution for anchoring."""
    s_lo = np.percentile(ref_scores, p_lo)
    s_hi = np.percentile(ref_scores, p_hi)
    lvl = lo + (scores - s_lo) / (s_hi - s_lo) * (hi - lo)
    return np.round(np.clip(np.round(lvl / step) * step, lo, hi), 1)


def load_unmatched():
    songs = []
    with open('data/unmatched_sp12.txt', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) == 3:
                songs.append({'title': parts[0], 'difficulty': parts[1], 'url': parts[2]})
    return songs


def train_feature_only_models(df):
    """Train GBM models on chart features only, for each difficulty signal."""
    targets = {
        'bpi_at_aaa':  'BPI@AAA',
        'bpi_at_9444': 'BPI@94.44%',
        'cpi_hard':    'CPI HARD',
        'cpi_exhard':  'CPI EXHARD',
    }
    models = {}
    params_out = {}  # z-score params per target
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    for col, label in targets.items():
        sub = df[FEATURES + [col]].dropna()
        X = sub[FEATURES].values
        y = sub[col].values
        scores = cross_val_score(GradientBoostingRegressor(**GBM_PARAMS), X, y,
                                 cv=kf, scoring='r2')
        print(f'  {label}: R²={scores.mean():.3f}±{scores.std():.3f} (n={len(sub)})')
        m = GradientBoostingRegressor(**GBM_PARAMS).fit(X, y)
        models[col] = m
        params_out[col] = (y.mean(), y.std())

    return models, params_out


def main():
    # ── Load training data ────────────────────────────────────────────────────
    print('Loading training data ...')
    train_df = pd.read_csv('data/features_sp12.csv', keep_default_na=False, na_values=[''])
    for col in FEATURES + ['bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard']:
        if col in train_df.columns:
            train_df[col] = pd.to_numeric(train_df[col], errors='coerce')

    # ── Train models ──────────────────────────────────────────────────────────
    print('\nTraining chart-feature-only models (no CPI/BPI cross-source features):')
    models, z_params = train_feature_only_models(train_df)

    # Compute reference ensemble scores from training data for level calibration
    full_train = train_df[FEATURES + ['bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard']].dropna()
    def zscore(v, mu, sig): return (v - mu) / sig
    mu_aaa,  s_aaa  = z_params['bpi_at_aaa']
    mu_9444, s_9444 = z_params['bpi_at_9444']
    mu_hard, s_hard = z_params['cpi_hard']
    mu_exh,  s_exh  = z_params['cpi_exhard']
    ref_ensemble = (
        zscore(full_train['bpi_at_aaa'].values,  mu_aaa,  s_aaa) +
        zscore(full_train['bpi_at_9444'].values, mu_9444, s_9444) +
        zscore(full_train['cpi_hard'].values,    mu_hard, s_hard) +
        zscore(full_train['cpi_exhard'].values,  mu_exh,  s_exh)
    ) / 4.0

    # ── Fetch chart features for unmatched songs ──────────────────────────────
    songs = load_unmatched()
    print(f'\nFetching chart data for {len(songs)} unmatched songs ...')

    rows = []
    failed = []
    for i, song in enumerate(songs):
        print(f'[{i+1}/{len(songs)}] {song["title"]!r} ({song["difficulty"]}) ...')
        try:
            score_data = get_score_data(song['url'])
            feats = compute_features(score_data)
            row = {
                'title':      song['title'],
                'chart_type': 'SPA' if song['difficulty'] == 'A' else 'SPL',
                **feats,
            }
            rows.append(row)
        except Exception as e:
            print(f'  ERROR: {e}')
            failed.append((song['title'], str(e)))
        time.sleep(0.5)

    print(f'\nFetched: {len(rows)}, Failed: {len(failed)}')
    if failed:
        print('Failed songs:')
        for t, e in failed:
            print(f'  {t!r}: {e}')

    if not rows:
        print('No data fetched. Aborting.')
        return

    # ── Predict difficulty ────────────────────────────────────────────────────
    pred_df = pd.DataFrame(rows)
    for col in FEATURES:
        pred_df[col] = pd.to_numeric(pred_df[col], errors='coerce')

    valid = pred_df.dropna(subset=FEATURES)
    X_pred = valid[FEATURES].values
    print(f'\nPredicting difficulty for {len(valid)} songs ...')

    pred_aaa  = models['bpi_at_aaa'].predict(X_pred)
    pred_9444 = models['bpi_at_9444'].predict(X_pred)
    pred_hard = models['cpi_hard'].predict(X_pred)
    pred_exh  = models['cpi_exhard'].predict(X_pred)

    ensemble = (
        zscore(pred_aaa,  mu_aaa,  s_aaa) +
        zscore(pred_9444, mu_9444, s_9444) +
        zscore(pred_hard, mu_hard, s_hard) +
        zscore(pred_exh,  mu_exh,  s_exh)
    ) / 4.0

    valid = valid.copy()
    valid['difficulty_score'] = ensemble
    valid['level'] = map_levels(ensemble, ref_ensemble)
    valid['bpi_at_aaa_pred']  = np.round(pred_aaa,  1)
    valid['bpi_at_9444_pred'] = np.round(pred_9444, 1)
    valid['cpi_hard_pred']    = np.round(pred_hard,  0)
    valid['cpi_exhard_pred']  = np.round(pred_exh,   0)
    valid['source'] = 'chart_features_only'

    # ── Save ──────────────────────────────────────────────────────────────────
    out_cols = ['title', 'chart_type', 'level',
                'bpi_at_aaa_pred', 'bpi_at_9444_pred', 'cpi_hard_pred', 'cpi_exhard_pred',
                'source']
    out = valid.sort_values(['level', 'difficulty_score'], ascending=[False, False])[out_cols]
    out.to_csv('data/difficulty_table_unmatched.csv', index=False)
    print(f'Saved {len(out)} rows → data/difficulty_table_unmatched.csv')

    # ── Summary ───────────────────────────────────────────────────────────────
    print('\nLevel distribution:')
    dist = out['level'].value_counts().sort_index(ascending=False)
    for lvl, cnt in dist.items():
        print(f'  {lvl:.1f}  {cnt:3d}  {"█" * cnt}')

    print('\nAll predicted songs (sorted by level):')
    print(out[['title', 'chart_type', 'level',
               'bpi_at_aaa_pred', 'cpi_hard_pred']].to_string(index=False))


if __name__ == '__main__':
    main()
