# モデリング設計

## 概要

☆12 SP 譜面の総合難易度と個人差を、スコア難易度・クリア難易度の両面から予測するアンサンブルモデル。

- **データ**: `data/features_sp12.csv`（555曲、532曲にBPIデータあり）
- **実装**: `src/train_model.py`
- **出力**: `data/difficulty_scores.csv`（`difficulty_score` + `kojinsa_score` の2次元）

---

## 目的変数

### 難易度 (4変数)

| カラム | 種別 | 定義 |
|--------|------|------|
| `bpi_at_aaa` | スコア難易度 | AAA閾値でのBPI（`floor(notes×2 × 8/9)`） |
| `bpi_at_9444` | スコア難易度 | MAX-閾値でのBPI（`floor(notes×2 × 17/18)`） |
| `cpi_hard` | クリア難易度 | CPI HARD |
| `cpi_exhard` | クリア難易度 | CPI EXHARD |

### 個人差 (2変数)

| カラム | 定義 | 方向 |
|--------|------|------|
| `bpi_coef` | BPIカーブ係数 | 低いほど個人差大 |
| `cpi_kojinsa` | `cpi_exhard − cpi_hard` | 高いほど個人差大 |

#### BPI算出式

定義: http://norimiso.web.fc2.com/aboutBPI.html

```
PGF(x) = 0.5 / (1 - x)     # x = score / max_score

m   = notes × 2             # 理論最大スコア
S/K = (m - avg) / (m - score)
Z/K = (m - avg) / (m - wr)

# score >= avg (皆伝平均以上) のとき
BPI = 100 × ln(S/K)^coef / ln(Z/K)^coef

# score < avg (皆伝平均未満) のとき
BPI = -100 × ln(K/S)^coef / ln(Z/K)^coef

# 下限クランプ
BPI = max(BPI, -15.0)
```

---

## 特徴量

`src/score_analyzer.py` が textage.cc のスコアデータから算出する15変数（チャート特徴量）。

| カテゴリ | 変数名 | 説明 |
|----------|--------|------|
| 譜面特性 | `rand` | ランダム対応度 |
| | `doji` | 同時押し割合 |
| | `kdan` | 階段割合 |
| | `tril` | トリル割合 |
| | `tate` | 縦連割合 |
| | `sara` | 皿複合割合 |
| | `cnbs` | CN (チャージノート) 割合 |
| ノーツ量 | `total_notes` | 総ノーツ数 |
| | `duration` | 曲時間（秒） |
| 密度 | `peak_density` | ピーク密度（notes/sec） |
| | `mean_density` | 平均密度（notes/sec） |
| | `peak_scratch_density` | ピーク皿密度 |
| BPM | `bpm_min` | 最低BPM |
| | `bpm_max` | 最高BPM |
| | `bpm_ratio` | bpm_max / bpm_min |

### Approach A: クロスソース個人差特徴量

BPI目標とCPI目標で異なるデータソースの個人差指標を相互に特徴量として追加する。

| 目的変数 | 追加特徴量 | 根拠 |
|----------|-----------|------|
| BPI@AAA, BPI@94.44% | `cpi_kojinsa` | CPI個人差スプレッドがBPI予測を補完 |
| CPI HARD, CPI EXHARD | `bpi_coef` | BPIカーブ形状がCPI予測を補完 |

---

## モデル構成

各目的変数に対して5種のモデルを5-fold CVで評価し、最良モデルを採用。

```python
# ベースライン
Ridge(alpha=1.0)
RandomForestRegressor(n_estimators=200, max_depth=8)
GradientBoostingRegressor(n_estimators=300, max_depth=4, lr=0.05, subsample=0.8)

# Optunaチューニング (20 trials each)
LightGBMRegressor  # num_leaves, lr, subsample, colsample, reg_alpha, reg_lambda
XGBRegressor       # max_depth, lr, subsample, colsample, reg_alpha, reg_lambda
```

評価指標: R²（主）、5-fold CV平均

---

## 実験結果

### 難易度モデル性能（Approach A）

| 目的変数 | n | 採用モデル | R² | 旧R²（参考） | 改善 |
|----------|---|-----------|-----|------------|------|
| `bpi_at_aaa` | 532 | XGBoost | **0.651** ± 0.067 | 0.486 | +0.165 |
| `bpi_at_9444` | 532 | XGBoost | **0.718** ± 0.050 | 0.496 | +0.222 |
| `cpi_hard` | 542 | XGBoost | **0.449** ± 0.046 | 0.394 | +0.055 |
| `cpi_exhard` | 542 | XGBoost | **0.505** ± 0.049 | 0.474 | +0.031 |

旧R²は個人差特徴量なし・GBMのみの結果。

### 個人差モデル性能（Approach B）

| 目的変数 | n | 採用モデル | R² | 解釈 |
|----------|---|-----------|-----|------|
| `bpi_coef` | 542 | RF | **0.082** | チャート特徴量からほぼ予測不能 |
| `cpi_kojinsa` | 555 | XGBoost | **0.555** | そこそこ予測可能 |

### 重要特徴量

| 目的変数 | 1位 | 2位 | 3位 | 4位 | 5位 |
|----------|-----|-----|-----|-----|-----|
| bpi_at_aaa | **cpi_kojinsa** | peak_density | doji | bpm_max | bpm_ratio |
| bpi_at_9444 | **cpi_kojinsa** | bpm_ratio | peak_density | kdan | bpm_max |
| cpi_hard | peak_density | bpm_ratio | sara | peak_scratch_density | bpm_max |
| cpi_exhard | bpm_ratio | peak_density | sara | peak_scratch_density | bpm_max |
| cpi_kojinsa | **bpm_ratio** | sara | bpm_max | peak_scratch_density | peak_density |

**発見**: `cpi_kojinsa` がBPI予測の最重要特徴量（重要度 0.33〜0.37）。BPIとCPIのデータが相互補完的。

### 予測値間の相関

| 組み合わせ | 相関係数 |
|------------|---------|
| CPI-HARD vs CPI-EXHARD | 0.932 |
| BPI@AAA vs CPI-EXHARD | 0.752 |
| BPI@AAA vs CPI-HARD | 0.675 |
| **−bpi_coef vs cpi_kojinsa** | **0.085** |

BPI個人差とCPI個人差の相関が0.085とほぼ無相関 → 両者は異なる概念を測定している。

---

## アンサンブル

### 難易度スコア

4モデルの予測値をz-score正規化して等重み平均。

```python
difficulty = (zscore(pred_aaa) + zscore(pred_9444)
            + zscore(pred_hard) + zscore(pred_exhard)) / 4.0
```

### 個人差スコア

bpi_coefは低いほど個人差大なので反転して合成。

```python
kojinsa = (zscore(-pred_coef) + zscore(pred_kojinsa)) / 2.0
```

---

## 結果一覧

### 難易度上位10曲

| 曲名 | difficulty | kojinsa |
|------|-----------|---------|
| Mare Nectaris | 3.38 | -0.59 |
| ディスコルディア | 3.36 | 0.79 |
| XHRONOXAPSULΞ | 3.12 | 0.26 |
| 冥 | 2.78 | 0.96 |
| Somnidiscotheque | 2.78 | 0.43 |
| SμG@R RU$# | 2.72 | 0.44 |
| n/a | 2.54 | 0.42 |
| 恋愛=精度×認識力 | 2.49 | 1.16 |
| 卑弥呼 | 2.35 | 0.25 |
| Level 5 | 2.34 | 1.15 |

### 個人差上位10曲

| 曲名 | kojinsa | difficulty |
|------|---------|-----------|
| The Chase | 2.12 | 1.83 |
| 灼熱 Lost Summer Dayz | 2.08 | 2.18 |
| SAMURAI-Scramble | 2.04 | 0.89 |
| SCREW // owo // SCREW | 2.00 | 1.47 |
| 音楽 | 1.96 | 1.96 |
| 199024club -Re:BounceKiller- | 1.87 | 1.78 |
| 雪上断火 | 1.85 | 2.08 |
| GAME ON | 1.72 | 0.20 |
| Level 3 | 1.71 | 1.77 |
| Snake Stick | 1.69 | 0.92 |

---

## 備考・課題

- `bpi_coef`（BPI個人差）はチャート特徴量から予測不能（R²=0.082）。譜面構造と独立した要素（癖・ランダム運要素）が支配的と考えられる
- `cpi_kojinsa`（CPI個人差）はBPM変化・皿複合で説明可能（R²=0.555）
- 個人差が大きい曲（The Chase、灼熱、SAMURAI-Scramble等）はコミュニティの認識と一致
- `n/a`（Blacklolita）はタイトルが "n/a" という文字列のためpandasがNaNと誤読みする — CSV読み込みに `keep_default_na=False, na_values=['']` が必要
- 同一譜面のANOTHER/LEGGENDARIA両方が収録されているケース（Beat Radiance/Beat Radiance†など）は現状重複して入っている
