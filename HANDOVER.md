# HANDOVER.md — Claude Code 引き継ぎ書

> このファイルは Claude Code セッション開始時に最初に読むこと。

---

## プロジェクト概要

beatmania IIDX の譜面サイト textage.cc から譜面データを取得・解析し、
BPI・CPI を教師データとして ☆11/☆12 SP の非公式難易度表を生成するツール。

---

## 現在の状態（2026-03-09 時点）

### フェーズ進捗

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 | textage パーサー | ✅ 完了 |
| Phase 2 | 分析エンジン | ✅ 完了 |
| Phase 3 | 難易度推定モデル・難易度表生成 | ✅ 完了 |
| Phase 4 | UI・リリース | 未着手 |

### データ概要

| ファイル | 内容 | 行数 |
|---------|------|------|
| `data/features_sp12.csv` | ☆12 SP 特徴量（BPI+CPI） | 525曲 |
| `data/features_sp11.csv` | ☆11 SP 特徴量（CPI有無混在） | 673曲 |
| `data/raw/bpi_raw_dump.json` | BPI生データ（605エントリ） | — |
| `data/raw/cpi_raw_dump.json` | CPI生データ | — |
| `data/unmatched_sp12.txt` | CPI未マッチの☆12曲リスト（手動管理） | 80曲 |

### 難易度表出力

| ファイル | 内容 |
|---------|------|
| `docs/difficulty_table_sp12.md` | ☆12 SP 難易度表（582曲、うち100曲は `*` 推定） |
| `docs/difficulty_table_sp11.md` | ☆11 SP 難易度表（638曲、全曲推定） |
| `docs/difficulty_table.md` | ☆12+☆11 合算（1220曲） |

---

## ディレクトリ構成

```
predict_iidx_diff/
├── data/
│   ├── raw/                  # 生データ（BPI/CPI JSON）
│   ├── features_sp12.csv     # ☆12 特徴量
│   ├── features_sp11.csv     # ☆11 特徴量
│   ├── difficulty_table.csv  # ☆12 難易度スコア
│   ├── difficulty_table_sp11.csv
│   ├── difficulty_table_unmatched.csv
│   └── unmatched_sp12.txt    # CPI未マッチ曲リスト（タブ区切り）
├── docs/
│   ├── difficulty_table_sp12.md
│   ├── difficulty_table_sp11.md
│   └── difficulty_table.md
└── src/
    ├── collect_data.py        # ☆12 特徴量収集（textage + CPI マッチング）
    ├── collect_sp11.py        # ☆11 特徴量収集
    ├── merge_bpi.py           # BPI列を features_sp12.csv にマージ
    ├── make_difficulty_table.py  # ☆12 難易度表生成
    ├── predict_unmatched.py   # CPI未マッチ☆12曲の難易度予測
    ├── predict_sp11.py        # ☆11 難易度予測
    ├── make_difficulty_md.py  # Markdown 生成
    ├── model_utils.py         # モデル選択ユーティリティ（★新規）
    ├── score_analyzer.py      # 分析エンジン
    ├── train_model.py         # 実験用（Optuna チューニング）
    └── textage/
        └── textage_parser.py  # textage HTML → ノーツ JSON
```

---

## パイプライン実行順序

```bash
# 特徴量再収集が必要な場合（textageへのアクセスが発生）
uv run python src/collect_data.py       # ☆12 特徴量収集（約30分）
uv run python src/merge_bpi.py          # BPI列マージ（必須）
uv run python src/collect_sp11.py      # ☆11 特徴量収集（約20分）

# 難易度表生成（通常はここから）
uv run python src/make_difficulty_table.py   # ☆12 難易度表
uv run python src/predict_unmatched.py       # CPI未マッチ☆12の予測（textageアクセスあり）
uv run python src/predict_sp11.py            # ☆11 難易度予測
uv run python src/make_difficulty_md.py      # Markdown 生成
```

---

## 主要な設計・実装メモ

### textage_parser.py の重要な挙動

- `if(a){}` ブロック内に `if(kuro){}` が**ネスト**されている
- `kuro` = LEGGENDARIA チャート固有データ
- **SPA パース時**: kuro ブロックを除外してパース → kuro のデータが混入しない
- **SPL パース時**: kuro ブロックのデータで sp[] を上書き（`.update()`）
- `sp[ n ]` のように括弧内にスペースがある場合あり → regex は `sp\[\s*(\d+)\s*\]` を使用
- CN 配列も同様に SPA/SPL で異なるブロックを参照

### score_analyzer.py の密度計算

- `peak_density` / `mean_density` は**鍵盤ノーツのみ**（key 1〜7）
- `peak_scratch_density` は皿のみ（key 0）
- 以前は皿が密度に混入して皿曲が過大評価されていた（修正済み）

### 特徴量の注意点

- `sara`（皿スコア）は textage 互換式で最大 264 まで到達しうる
- 読み込み時に `clip(upper=100.0)` を適用してモデルに渡す（CSV は生値保存）
- GBM はスケール不変だが、将来の線形モデル移行に備えてのクリップ

### モデル選択（model_utils.py）

- GBM / LightGBM / XGBoost / RandomForest を 5-fold CV で比較
- `select_best_model(X, y, label)` が最良モデルをフィットして返す
- 現状の結果: BPI ターゲットは GBM 最良（R²≈0.65〜0.70）、cpi_hard のみ XGB が上回ることあり

### BPI データのマージ（merge_bpi.py）

- `collect_data.py` 再実行後は `merge_bpi.py` も必ず実行すること
- `bpi_at_aaa` / `bpi_at_9444` は git 履歴の旧 CSV から取得（算出式不明のため）
- 旧 CSV にない新規曲（4曲程度）は BPI なし（CPI-only 扱い）

### unmatched_sp12.txt の管理

- タブ区切り: `タイトル\t難易度(A/X)\tURL`
- コメント行は `#` で始める
- CPI データと一致しなかった曲を手動で管理
- `predict_unmatched.py` が textage から特徴量を取得して難易度を推定

---

## 既知の問題・制約

- **SP のみ対応**（DP 未実装）
- `sara` の算出式（textage 互換）は皿を過大評価する傾向あり → 100 クリップで暫定対応中
- BPI の `at_aaa` / `at_9444` の計算式が不明なため再計算不可（git 履歴から取得）
- `L.E.D. & HuΣeR\,` や `八戸亀生羅\,` のタイトル末尾 `\` は textage の正式表記（バグではない）

---

## 参考リンク

- textage.cc: https://textage.cc
- lmtak ブログ（解析メモ1）: https://lmtak.hateblo.jp/entry/2022/04/30/180000
- lmtak ブログ（解析メモ2）: https://lmtak.hateblo.jp/entry/2022/05/20/090000
