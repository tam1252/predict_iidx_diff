"""
make_difficulty_md.py — Generate unofficial SP difficulty tables as Markdown.

Outputs:
  docs/difficulty_table_sp12.md  — ☆12 SP (11.5–13.0)
  docs/difficulty_table_sp11.md  — ☆11 SP (11.0–13.0)
"""

import io
import os
import pandas as pd


def _load_sp12():
    df = pd.read_csv('data/difficulty_table.csv', keep_default_na=False, na_values=[''])
    df['estimated'] = df['source'].str.startswith('cpi_only')
    df['kojinsa_disp'] = df['kojinsa']

    uf = pd.read_csv('data/difficulty_table_unmatched.csv', keep_default_na=False, na_values=[''])
    uf['estimated'] = True
    uf['kojinsa_disp'] = '—'

    merged = pd.concat([
        df[['title', 'chart_type', 'level', 'kojinsa_disp', 'estimated']],
        uf[['title', 'chart_type', 'level', 'kojinsa_disp', 'estimated']],
    ], ignore_index=True)
    return merged.sort_values(['level', 'title'], ascending=[False, True])


def _load_sp11():
    df = pd.read_csv('data/difficulty_table_sp11.csv', keep_default_na=False, na_values=[''])
    df['estimated'] = df['source'] == 'chart_features_only'
    df['kojinsa_disp'] = df['kojinsa']
    return df[['title', 'chart_type', 'level', 'kojinsa_disp', 'estimated']]\
        .sort_values(['level', 'title'], ascending=[False, True])


def _build_md(df, title_str, level_range_str, note_str=''):
    buf = io.StringIO()
    buf.write(f'# {title_str}\n\n')
    buf.write('BPI・CPI データをもとにモデルで算出した非公式難易度です。\n\n')
    buf.write(f'- レベル範囲: **{level_range_str}**（0.1 刻み）\n')
    buf.write('- 個人差: **高** / **中** / **低** / **—**（データなし）\n')
    buf.write('- `*` マークはモデル予測のみ（BPI/CPI 実データなし）\n')
    if note_str:
        buf.write(f'- {note_str}\n')
    buf.write('\n---\n\n')

    for lvl in sorted(df['level'].unique(), reverse=True):
        sub = df[df['level'] == lvl]
        spa = sub[sub['chart_type'] == 'SPA'].sort_values('title')
        spl = sub[sub['chart_type'] == 'SPL'].sort_values('title')

        buf.write(f'## {lvl:.1f}  （{len(sub)} 曲）\n\n')

        for label, rows in [('SPA', spa), ('SPL', spl)]:
            if rows.empty:
                continue
            buf.write(f'### {label}\n\n')
            buf.write('| 曲名 | 個人差 |\n')
            buf.write('|------|--------|\n')
            for _, row in rows.iterrows():
                mark = ' *' if row['estimated'] else ''
                buf.write(f'| {row["title"]}{mark} | {row["kojinsa_disp"]} |\n')
            buf.write('\n')

    return buf.getvalue()


def main():
    os.makedirs('docs', exist_ok=True)

    # ── ☆12 ──────────────────────────────────────────────────────────────────
    sp12 = _load_sp12()
    total12 = len(sp12)
    est12 = int(sp12['estimated'].sum())
    md12 = _build_md(sp12, '☆12 SP 非公式難易度表', '11.5 〜 13.0')
    with open('docs/difficulty_table_sp12.md', 'w', encoding='utf-8') as f:
        f.write(md12)
    print(f'Written: docs/difficulty_table_sp12.md  ({total12} songs, {est12} estimated *)')

    # ── ☆11 ──────────────────────────────────────────────────────────────────
    sp11 = _load_sp11()
    total11 = len(sp11)
    est11 = int(sp11['estimated'].sum())
    md11 = _build_md(sp11, '☆11 SP 非公式難易度表', '11.0 〜 13.0',
                     note_str='☆12 モデルを ☆11 譜面特徴量に適用した推定値のため精度は低め')
    with open('docs/difficulty_table_sp11.md', 'w', encoding='utf-8') as f:
        f.write(md11)
    print(f'Written: docs/difficulty_table_sp11.md  ({total11} songs, {est11} estimated *)')


if __name__ == '__main__':
    main()
