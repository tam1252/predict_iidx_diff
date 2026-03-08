"""
train_model.py — Phase 3: Difficulty estimation models

Targets (difficulty):
  bpi_at_aaa   — BPI at AAA threshold (score difficulty)
  bpi_at_9444  — BPI at 94.44% threshold (score difficulty)
  cpi_hard     — CPI HARD (clear difficulty)
  cpi_exhard   — CPI EXHARD (clear difficulty, stricter)

Targets (individual difference / 個人差):
  bpi_coef     — BPI curve coefficient (lower = more individual-diff)
  cpi_kojinsa  — CPI EXHARD − HARD spread (higher = more individual-diff)

Approach A: add cross-source 個人差 metric as a feature when predicting difficulty
  - BPI targets ← add cpi_kojinsa as feature
  - CPI targets ← add bpi_coef as feature

Approach B: separately predict 個人差, produce 2D output (difficulty, kojinsa)

Tuning: Optuna optimises LightGBM / XGBoost hyperparameters per target.
"""

import copy
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings('ignore', category=UserWarning)

# ── Chart features (from textage analysis) ────────────────────────────────────
FEATURES = [
    'rand', 'doji', 'kdan', 'tril', 'tate', 'sara', 'cnbs',
    'total_notes', 'duration',
    'peak_density', 'mean_density', 'peak_scratch_density',
    'bpm_min', 'bpm_max', 'bpm_ratio',
]

# ── 個人差 metrics ──────────────────────────────────────────────────────────────
# bpi_coef: lower → BPI curve is steeper → higher individual difference
# cpi_kojinsa: exhard−hard spread → higher → harder to predict clearability
KOJINSA_COLS = ['bpi_coef', 'cpi_kojinsa']

CV = 5
RANDOM_STATE = 42
OPTUNA_TRIALS = 20


# ── Data loading ───────────────────────────────────────────────────────────────

def load_data(csv_path: str) -> pd.DataFrame:
    # keep_default_na=False prevents song titles like "n/a" from being read as NaN
    df = pd.read_csv(csv_path, keep_default_na=False, na_values=[''])
    num_cols = FEATURES + ['cpi_hard', 'cpi_exhard', 'bpi_at_aaa', 'bpi_at_9444', 'bpi_coef']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['cpi_kojinsa'] = df['cpi_exhard'] - df['cpi_hard']
    return df


# ── Model evaluation helpers ───────────────────────────────────────────────────

def cv_r2(model, X: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    kf = KFold(n_splits=CV, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, X, y, cv=kf, scoring='r2')
    return scores.mean(), scores.std()


def cv_predict(model, X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Out-of-fold predictions."""
    preds = np.zeros(len(y))
    kf = KFold(n_splits=CV, shuffle=True, random_state=RANDOM_STATE)
    for tr_idx, val_idx in kf.split(X):
        m = copy.deepcopy(model)
        m.fit(X[tr_idx], y[tr_idx])
        preds[val_idx] = m.predict(X[val_idx])
    return preds


# ── Optuna tuning ──────────────────────────────────────────────────────────────

def tune_lgbm(X: np.ndarray, y: np.ndarray) -> lgb.LGBMRegressor:
    def objective(trial):
        params = {
            'n_estimators':     trial.suggest_int('n_estimators', 200, 1000),
            'max_depth':        trial.suggest_int('max_depth', 3, 8),
            'learning_rate':    trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'num_leaves':       trial.suggest_int('num_leaves', 15, 127),
            'subsample':        trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'reg_alpha':        trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
            'reg_lambda':       trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
            'random_state': RANDOM_STATE, 'verbose': -1,
        }
        m = lgb.LGBMRegressor(**params)
        r2, _ = cv_r2(m, X, y)
        return r2

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    best = lgb.LGBMRegressor(**study.best_params, random_state=RANDOM_STATE, verbose=-1)
    return best


def tune_xgb(X: np.ndarray, y: np.ndarray) -> xgb.XGBRegressor:
    def objective(trial):
        params = {
            'n_estimators':     trial.suggest_int('n_estimators', 200, 1000),
            'max_depth':        trial.suggest_int('max_depth', 3, 8),
            'learning_rate':    trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'subsample':        trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'reg_alpha':        trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
            'reg_lambda':       trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
            'random_state': RANDOM_STATE, 'verbosity': 0,
        }
        m = xgb.XGBRegressor(**params)
        r2, _ = cv_r2(m, X, y)
        return r2

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
    best = xgb.XGBRegressor(**study.best_params, random_state=RANDOM_STATE, verbosity=0)
    return best


# ── Main training routine ──────────────────────────────────────────────────────

def train_target(df: pd.DataFrame, target: str, label: str,
                 feature_cols: list[str]) -> tuple:
    """Train and select best model for one target. Returns (best_model, oof_preds)."""
    sub = df[feature_cols + [target]].dropna()
    X = sub[feature_cols].values
    y = sub[target].values
    print(f'\n=== {label} (n={len(sub)}) ===')
    print(f'  Target: {y.min():.3f} ~ {y.max():.3f}, mean={y.mean():.3f}')

    baseline_models = {
        'Ridge': Pipeline([('sc', StandardScaler()), ('m', Ridge(alpha=1.0))]),
        'RF':    RandomForestRegressor(n_estimators=200, max_depth=8, random_state=RANDOM_STATE),
        'GBM':   GradientBoostingRegressor(n_estimators=300, max_depth=4,
                                           learning_rate=0.05, subsample=0.8,
                                           random_state=RANDOM_STATE),
    }
    results = {}
    for name, m in baseline_models.items():
        r2, r2_std = cv_r2(m, X, y)
        results[name] = (r2, m)
        print(f'  [{name}] R²={r2:.3f}±{r2_std:.3f}')

    # Optuna-tuned LightGBM and XGBoost
    print(f'  [LightGBM] tuning {OPTUNA_TRIALS} trials ...')
    lgbm_best = tune_lgbm(X, y)
    r2_lgbm, r2_lgbm_std = cv_r2(lgbm_best, X, y)
    results['LightGBM'] = (r2_lgbm, lgbm_best)
    print(f'  [LightGBM] R²={r2_lgbm:.3f}±{r2_lgbm_std:.3f}')

    print(f'  [XGBoost]  tuning {OPTUNA_TRIALS} trials ...')
    xgb_best = tune_xgb(X, y)
    r2_xgb, r2_xgb_std = cv_r2(xgb_best, X, y)
    results['XGBoost'] = (r2_xgb, xgb_best)
    print(f'  [XGBoost]  R²={r2_xgb:.3f}±{r2_xgb_std:.3f}')

    best_name = max(results, key=lambda k: results[k][0])
    best_model = results[best_name][1]
    print(f'  Best: {best_name} (R²={results[best_name][0]:.3f})')

    # Feature importance
    best_model.fit(X, y)
    m = best_model.named_steps['m'] if hasattr(best_model, 'named_steps') else best_model
    if hasattr(m, 'feature_importances_'):
        imps = sorted(zip(feature_cols, m.feature_importances_), key=lambda x: -x[1])
        print('  Top features:', [(f, f'{v:.3f}') for f, v in imps[:6]])

    # OOF predictions on the same subset (re-fit model for cv_predict)
    oof = cv_predict(best_model, X, y)
    return best_model, sub.index, oof, y


def zscore(v: np.ndarray) -> np.ndarray:
    return (v - v.mean()) / v.std()


def main():
    csv_path = 'data/features_sp12.csv'
    df = load_data(csv_path)
    print(f'Loaded {len(df)} rows')
    print(f'  Complete chart features: {df[FEATURES].notna().all(axis=1).sum()}')
    print(f'  With BPI data: {df["bpi_at_aaa"].notna().sum()}')
    print(f'  With CPI data: {df["cpi_hard"].notna().sum()}')

    # ── Approach A: cross-source 個人差 as additional feature ──────────────────
    # BPI targets get cpi_kojinsa; CPI targets get bpi_coef
    FEAT_BPI = FEATURES + ['cpi_kojinsa']   # CPI個人差 → BPI prediction
    FEAT_CPI = FEATURES + ['bpi_coef']      # BPI個人差 → CPI prediction

    print('\n' + '='*60)
    print('DIFFICULTY MODELS (Approach A: cross-source 個人差 feature)')
    print('='*60)

    _, idx_aaa,   oof_aaa,    y_aaa    = train_target(df, 'bpi_at_aaa',  'BPI@AAA',     FEAT_BPI)
    _, idx_9444,  oof_9444,   y_9444   = train_target(df, 'bpi_at_9444', 'BPI@94.44%',  FEAT_BPI)
    _, idx_hard,  oof_hard,   y_hard   = train_target(df, 'cpi_hard',    'CPI HARD',    FEAT_CPI)
    _, idx_exh,   oof_exhard, y_exhard = train_target(df, 'cpi_exhard',  'CPI EXHARD',  FEAT_CPI)

    # ── Approach B: 個人差 prediction ──────────────────────────────────────────
    print('\n' + '='*60)
    print('KOJINSA MODELS (Approach B: predict 個人差 from chart features)')
    print('='*60)

    _, idx_coef,  oof_coef,   y_coef   = train_target(df, 'bpi_coef',    'BPI coef (個人差)', FEATURES)
    _, idx_koji,  oof_koji,   y_koji   = train_target(df, 'cpi_kojinsa', 'CPI kojinsa (exhard−hard)', FEATURES)

    # ── Ensemble: difficulty score ─────────────────────────────────────────────
    # Use songs that have all four difficulty targets
    shared_idx = idx_aaa.intersection(idx_9444).intersection(idx_hard).intersection(idx_exh)
    print(f'\n=== Difficulty Ensemble (n={len(shared_idx)}) ===')

    def align(oof, idx):
        """Return oof values aligned to shared_idx."""
        mapping = dict(zip(idx, oof))
        return np.array([mapping[i] for i in shared_idx])

    z_aaa    = zscore(align(oof_aaa,    idx_aaa))
    z_9444   = zscore(align(oof_9444,   idx_9444))
    z_hard   = zscore(align(oof_hard,   idx_hard))
    z_exhard = zscore(align(oof_exhard, idx_exh))
    difficulty = (z_aaa + z_9444 + z_hard + z_exhard) / 4.0

    print(f'  Corr BPI@AAA vs CPI-HARD:    {np.corrcoef(z_aaa, z_hard)[0,1]:.3f}')
    print(f'  Corr BPI@AAA vs CPI-EXHARD:  {np.corrcoef(z_aaa, z_exhard)[0,1]:.3f}')
    print(f'  Corr CPI-HARD vs CPI-EXHARD: {np.corrcoef(z_hard, z_exhard)[0,1]:.3f}')
    print(f'  Difficulty range: {difficulty.min():.3f} ~ {difficulty.max():.3f}')

    # ── 個人差 score ────────────────────────────────────────────────────────────
    koji_shared = idx_coef.intersection(idx_koji)
    print(f'\n=== Kojinsa Ensemble (n={len(koji_shared)}) ===')

    def align2(oof, idx):
        mapping = dict(zip(idx, oof))
        return np.array([mapping[i] for i in koji_shared])

    # bpi_coef: lower = more individual-diff → negate for consistent direction
    z_coef = zscore(-align2(oof_coef, idx_coef))   # invert: higher = more kojinsa
    z_koji = zscore(align2(oof_koji, idx_koji))
    kojinsa = (z_coef + z_koji) / 2.0

    print(f'  Corr −bpi_coef vs cpi_kojinsa: {np.corrcoef(z_coef, z_koji)[0,1]:.3f}')
    print(f'  Kojinsa range: {kojinsa.min():.3f} ~ {kojinsa.max():.3f}')

    # ── Build output DataFrame ─────────────────────────────────────────────────
    result = pd.DataFrame({
        'difficulty_score': difficulty,
        'bpi_at_aaa':  align(oof_aaa,    idx_aaa),
        'bpi_at_9444': align(oof_9444,   idx_9444),
        'cpi_hard':    align(oof_hard,   idx_hard),
        'cpi_exhard':  align(oof_exhard, idx_exh),
    }, index=shared_idx)
    result['title'] = df.loc[shared_idx, 'title'].values

    # Add kojinsa where available
    koji_in_shared = shared_idx.intersection(koji_shared)
    result['kojinsa_score'] = np.nan
    koji_mapping = dict(zip(koji_shared, kojinsa))
    for i in koji_in_shared:
        result.loc[i, 'kojinsa_score'] = koji_mapping[i]

    # ── Print top/bottom difficulty ────────────────────────────────────────────
    cols_show = ['title', 'difficulty_score', 'kojinsa_score', 'bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard']
    print('\n  Top 10 hardest:')
    for _, row in result.nlargest(10, 'difficulty_score')[cols_show].iterrows():
        koji = f'{row["kojinsa_score"]:.2f}' if pd.notna(row['kojinsa_score']) else '  N/A'
        print(f'    {row["title"]!r:40s}  diff={row["difficulty_score"]:.2f}  koji={koji}')

    print('\n  Bottom 10 easiest:')
    for _, row in result.nsmallest(10, 'difficulty_score')[cols_show].iterrows():
        koji = f'{row["kojinsa_score"]:.2f}' if pd.notna(row['kojinsa_score']) else '  N/A'
        print(f'    {row["title"]!r:40s}  diff={row["difficulty_score"]:.2f}  koji={koji}')

    # ── High kojinsa songs ─────────────────────────────────────────────────────
    print('\n  Top 10 highest 個人差 (kojinsa):')
    for _, row in result.dropna(subset=['kojinsa_score']).nlargest(10, 'kojinsa_score')[cols_show].iterrows():
        print(f'    {row["title"]!r:40s}  koji={row["kojinsa_score"]:.2f}  diff={row["difficulty_score"]:.2f}')

    # ── Save ───────────────────────────────────────────────────────────────────
    out_cols = ['title', 'difficulty_score', 'kojinsa_score',
                'bpi_at_aaa', 'bpi_at_9444', 'cpi_hard', 'cpi_exhard']
    result[out_cols].to_csv('data/difficulty_scores.csv', index=False)
    print(f'\nSaved {len(result)} rows to data/difficulty_scores.csv')


if __name__ == '__main__':
    main()
