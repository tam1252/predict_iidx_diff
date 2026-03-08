# HANDOVER.md — Claude Code 引き継ぎ書

> このファイルは Claude Code セッション開始時に最初に読むこと。
> プロジェクト全体像は `README.md`、textage 解読の詳細は `TEXTAGE_DECODING.md` を参照。

---

## プロジェクト概要（一言）

beatmania IIDX の譜面サイト textage.cc から譜面データを取得・解析し、難易度を推定するツール。

---

## 現在の状態

### 完成済み

**`src/textage/textage_parser.py`** — textage HTML → ノーツJSON変換
- SP譜面（通常・チャージノーツ・MSS）のパース完了
- 難易度ブロック分離・親ブロック参照解決済み
- ソフラン情報（BPM変化）の抽出済み
- 検証済み曲: Verflucht SP-L（2401✅）、惑星鉄道 SP-A（1633✅）、叙情 SP-A（836✅）

**`src/score_analyzer.py`** — 分析エンジン
- `build_time_map()` — ノーツに実時間付与（ソフラン補正済み）
- `analyze_density()` — スライディングウィンドウで密度計算
- `detect_patterns()` — 同時押し・トリル・階段・縦連打・皿の検出
- `calc_textage_scores()` — textage.cc 統計表示と互換のスコアポイント計算（bms2jsh.js の stat_check_* を完全再現）

### 未着手

- **Phase 3**: 難易度推定モデル（複数曲のデータ収集 → 特徴量設計 → モデル学習）
- **Phase 4**: UI・リリース

---

## ディレクトリ構成

```
predict_iidx_diff/
├── main.py               # エントリポイント（現在は実験用）
├── README.md             # プロジェクト全体のドキュメント
├── TEXTAGE_DECODING.md   # textage 解読の試行錯誤記録
├── HANDOVER.md           # このファイル
└── src/
    ├── __init__.py
    ├── score_analyzer.py
    └── textage/
        ├── __init__.py
        └── textage_parser.py
```

---

## 主要な関数と使い方

```python
from src.textage.textage_parser import get_score_data, parse_html
from src.score_analyzer import analyze_density, detect_patterns, calc_textage_scores

# URLから取得（難易度はURLクエリから自動判定）
data = get_score_data("https://textage.cc/score/21/verflcht.html?1XC00")

# data の構造:
# {
#   'title': str,
#   'notes': list[{measure, pos, key, type}],  # type: normal/cn_start/cn_end
#   'total_notes': int,
#   'measure_lens': dict,      # ln[n] の値
#   'lndef': int,              # デフォルト小節長（通常384、曲によって288等）
#   'bpm_base': str,           # "157" or "10～166"
#   'bpm_changes': list[dict], # {measure, pos, bpm}
# }

density  = analyze_density(data)        # ピーク密度・平均密度・タイムライン
patterns = detect_patterns(data)        # パターン検出
scores   = calc_textage_scores(data)    # textage互換スコアポイント
# scores: {'rand', 'doji', 'kdan', 'tril', 'tate', 'sara', 'cnbs', 'total', 'notes', 'oabmb'}
```

---

## 次にやること（Phase 3 の始め方）

### ゴール
複数曲の `calc_textage_scores()` の結果と実際の難易度（☆1〜12）を使って、難易度推定モデルを作る。

### 具体的なステップ

**1. データ収集**
textage.cc のURLリストを作成して複数曲を一括取得し、特徴量を CSV に保存する。
URLの形式: `https://textage.cc/score/{version}/{filename}.html?1{char2}C00`

```python
# 例: データ収集スクリプトのイメージ
songs = [
    ("https://textage.cc/score/21/verflcht.html?1XC00", 12),  # ☆12
    ("https://textage.cc/score/.../....html?1AC00", 10),       # ☆10
    ...
]
rows = []
for url, level in songs:
    data = get_score_data(url)
    scores = calc_textage_scores(data)
    density = analyze_density(data)
    rows.append({**scores, 'peak_density': density['peak_density'], 'level': level})
```

**2. 特徴量候補**
- `rand`, `doji`, `kdan`, `tril`, `tate`, `sara`, `cnbs`（textage スコア）
- `peak_density`, `mean_density`（密度）
- `total_notes`, `duration`
- ソフラン変動幅（bpm_max / bpm_min）

**3. モデル**
まずは線形回帰やランダムフォレストで試す。難易度は☆1〜12の順序スケールなので回帰 or 順序分類。

---

## 注意事項・既知の制約

- **SP のみ対応**。DPは未実装（`side` パラメータで2Pは切り替えられるが、DP配置の解釈は未確認）
- **ネットワーク**: textage.cc への過度なリクエストに注意。曲数が多い場合はスリープを入れること
- **textage の HTML 構造**: ほぼ全曲で動作確認済みだが、稀なエッジケースがある可能性は残る
- `calc_textage_scores()` は bms2jsh.js の `stat_check_*` を Python で再現したもの。textage.cc の統計表示と照合して精度を確認することを推奨

---

## 参考リンク

- textage.cc: https://textage.cc
- lmtak ブログ（解析メモ1）: https://lmtak.hateblo.jp/entry/2022/04/30/180000
- lmtak ブログ（解析メモ2）: https://lmtak.hateblo.jp/entry/2022/05/20/090000
