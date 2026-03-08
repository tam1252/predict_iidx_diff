"""
model_utils.py — Shared model selection utility.

Compares GBM, LightGBM, XGBoost, and RandomForest via 5-fold CV,
then fits and returns the best model for a given (X, y) pair.
"""

import numpy as np
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from xgboost import XGBRegressor

_KF = KFold(n_splits=5, shuffle=True, random_state=42)


def _candidates():
    return {
        'GBM': GradientBoostingRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, random_state=42,
        ),
        'LGB': LGBMRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            random_state=42, verbose=-1, feature_name='auto',
        ),
        'XGB': XGBRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            random_state=42, verbosity=0,
        ),
        'RF': RandomForestRegressor(
            n_estimators=300, random_state=42,
        ),
    }


def select_best_model(X: np.ndarray, y: np.ndarray, label: str = '') -> object:
    """
    Train and compare multiple regressors via 5-fold CV.
    Returns the best estimator (already fitted on full X, y).
    """
    prefix = f'  [{label}] ' if label else '  '
    best_name, best_score, best_est = None, -np.inf, None

    for name, est in _candidates().items():
        scores = cross_val_score(est, X, y, cv=_KF, scoring='r2')
        mean, std = scores.mean(), scores.std()
        marker = ''
        if best_score == -np.inf or mean > best_score:
            best_score, best_name, best_est = mean, name, est
            marker = ' ←'
        print(f'{prefix}{name}: R²={mean:.3f}±{std:.3f}{marker}')

    print(f'{prefix}→ Best: {best_name} (R²={best_score:.3f})')
    return best_est.fit(X, y)
