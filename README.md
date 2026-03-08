# predict_iidx_diff

beatmania IIDXの譜面難易度を推定するプロジェクト。
[textage.cc](https://textage.cc) から譜面データを取得・解析し、各種指標をもとに難易度を推定する。

---

## プロジェクト構成

```
predict_iidx_diff/
├── main.py
├── README.md
└── src/
    ├── __init__.py
    ├── score_analyzer.py
    └── textage/
        ├── __init__.py
        └── textage_parser.py
```

---

## モジュール概要

### `src/textage/textage_parser.py`

textage.cc のHTMLを解析してノーツデータに変換する。

```python
from src.textage.textage_parser import get_score_data, parse_html

# URLから取得（難易度はURLクエリから自動判定）
data = get_score_data("https://textage.cc/score/21/verflcht.html?1XC00")

# HTMLファイルから直接パース
with open("score.html") as f:
    data = parse_html(f.read(), difficulty='A')
```

**戻り値 (`dict`)**

| キー | 型 | 内容 |
|------|----|------|
| `title` | `str` | 曲名 |
| `notes` | `list[dict]` | 全ノーツ（`measure`, `pos`, `key`, `type`） |
| `total_notes` | `int` | 総ノーツ数 |
| `measure_lens` | `dict` | 小節ごとの長さ (`ln[n]`) |
| `lndef` | `int` | デフォルト小節長（通常384、曲により288等） |
| `bpm_base` | `str` | BPM文字列（例: `"157"`, `"10～166"`） |
| `bpm_changes` | `list[dict]` | ソフランイベント（`measure`, `pos`, `bpm`） |

**ノーツの `key` 番号**

| key | レーン |
|-----|--------|
| 0 | スクラッチ |
| 1〜7 | 鍵盤 |

**ノーツの `type`**

| type | 内容 |
|------|------|
| `normal` | 通常ノーツ |
| `cn_start` | チャージノーツ始端 |
| `cn_end` | チャージノーツ終端 |

**難易度指定 (`difficulty`)**

| 値 | 難易度 |
|----|--------|
| `P` | BEGINNER |
| `N` | NORMAL |
| `H` | HYPER |
| `A` | ANOTHER |
| `X` | LEGGENDARIA |

---

### `src/score_analyzer.py`

`textage_parser` の出力を受け取り、各種分析指標を計算する。

```python
from src.textage.textage_parser import get_score_data
from src.score_analyzer import analyze_density, detect_patterns, calc_textage_scores

data = get_score_data(url)

density  = analyze_density(data)
patterns = detect_patterns(data)
scores   = calc_textage_scores(data)
```

#### `analyze_density(parse_result, window_sec=5.0, step_sec=1.0)`

実時間ベースのノーツ密度を計算（BPM・ソフラン補正済み）。

**戻り値**

| キー | 内容 |
|------|------|
| `duration` | 曲長（秒） |
| `timeline` | `[{time, density, scratch_density}, ...]`（グラフ用時系列） |
| `peak_density` | ピーク密度（notes/sec） |
| `peak_time` | ピーク時刻（秒） |
| `peak_scratch_density` | スクラッチのピーク密度 |
| `mean_density` | 平均密度 |

#### `detect_patterns(parse_result, trill_min=4, stairs_min=4, jacks_min=2)`

譜面パターンを検出する。

**戻り値**

| キー | 内容 |
|------|------|
| `chords` | 同時押し一覧 |
| `scratch_chords` | 皿複合一覧 |
| `trills` | トリル区間一覧 |
| `stairs` | 階段区間一覧 |
| `jacks` | 縦連打区間一覧 |
| `summary` | 各パターンの件数・総ノーツ数 |

**パターン検出の定義**

- **同時押し**: 2鍵以上が同じposに重なる
- **皿複合**: スクラッチ（key=0）を含む同時押し
- **トリル**: 2鍵交互を `trill_min` 連以上、BPM120の8分間隔以内
- **階段**: 3種以上の異なる鍵盤が `stairs_min` 連以上、同間隔制約
- **縦連打**: 同レーンにBPM120の16分間隔より短い間隔で `jacks_min` 連以上

#### `calc_textage_scores(parse_result)`

textage.cc の統計表示と互換のスコアポイントを計算する。
bms2jsh.js の `stat_check_*` + `stat_result()` を再現。

**戻り値**

| キー | 内容 |
|------|------|
| `rand` | 乱打 pt |
| `doji` | 同時 pt |
| `kdan` | 階段 pt |
| `tril` | トリル pt |
| `tate` | 縦連 pt |
| `sara` | 皿 pt |
| `cnbs` | ＣＮ pt |
| `total` | 合計 pt |
| `notes` | ノーツ数 |
| `oabmb` | 補正ノーツ数（スコア計算の分母） |

スコアは `ceil(1000 * stat_value / oabmb) / 10` で計算され、各指標は概ね0〜100ptの範囲。

---

## 非公式難易度表

BPI・CPI データおよびモデル予測で算出した非公式難易度です。

| レベル | リンク | 曲数 | レベル範囲 |
| --- | --- | --- | --- |
| ☆12 SP | [docs/difficulty_table_sp12.md](docs/difficulty_table_sp12.md) | 611曲 | 11.5 〜 13.0 |
| ☆11 SP | [docs/difficulty_table_sp11.md](docs/difficulty_table_sp11.md) | 668曲 | 11.0 〜 13.0 |

- 個人差: **高** / **中** / **低** の3段階
- `*` マークはモデル予測のみ（BPI/CPI 実データなし）

---

## 開発フェーズ

- [x] **Phase 1** — textageデコーダー実装
  - SP譜面（通常ノーツ・チャージノーツ・MSS）のパース
  - 難易度ブロック分離・親ブロック参照解決
  - ソフラン情報（BPM変化）の抽出
- [x] **Phase 2** — 譜面分析エンジン
  - 実時間ベースの密度分析（BPM・ソフラン補正）
  - パターン検出（同時押し・皿複合・トリル・階段・縦連打）
  - textage互換スコアポイント計算
- [x] **Phase 3** — 難易度推定モデル
  - BPI・CPI を目的変数とした GBM / XGBoost / LightGBM アンサンブル
  - 個人差スコア（高/中/低）の推定
  - ☆12 SP 全611曲への難易度割り当て（11.5〜13.0）
- [ ] **Phase 4** — UI・リリース

---

## 参考

- [textage.cc](https://textage.cc) — 譜面データソース
- [lmtakブログ（解析メモ1）](https://lmtak.hateblo.jp/entry/2022/04/30/180000)
- [lmtakブログ（解析メモ2）](https://lmtak.hateblo.jp/entry/2022/05/20/090000)