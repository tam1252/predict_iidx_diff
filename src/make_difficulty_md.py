"""
make_difficulty_md.py — Generate unofficial ☆12 SP difficulty table as Markdown.

Combines data/difficulty_table.csv (531 songs with CPI/BPI data)
and data/difficulty_table_unmatched.csv (80 songs, chart-features-only prediction).

Output: docs/difficulty_table.md
"""

import io
import pandas as pd

KOJINSA_LABEL = {'高': '高', '中': '中', '低': '低', '—': '—'}


def load_tables():
    df = pd.read_csv('data/difficulty_table.csv', keep_default_na=False, na_values=[''])
    df['estimated'] = df['source'].str.startswith('cpi_only')
    df['kojinsa_disp'] = df['kojinsa']

    uf = pd.read_csv('data/difficulty_table_unmatched.csv', keep_default_na=False, na_values=[''])
    uf['estimated'] = True
    uf['kojinsa_disp'] = '—'

    merged = pd.concat([
        df[['title', 'chart_type', 'level', 'kojinsa_disp', 'estimated']],
        uf[['title', 'chart_type', 'level', 'kojinsa_disp', 'estimated']].rename(
            columns={'kojinsa_disp': 'kojinsa_disp'}),
    ], ignore_index=True)

    merged = merged.sort_values(['level', 'title'], ascending=[False, True])
    return merged


def build_md(df):
    buf = io.StringIO()

    buf.write('# ☆12 SP 非公式難易度表\n\n')
    buf.write('BPI・CPI データをもとにモデルで算出した非公式難易度です。\n\n')
    buf.write('- レベル範囲: **11.5 〜 13.0**（0.1 刻み）\n')
    buf.write('- 個人差: **高** / **中** / **低** / **—**（データなし）\n')
    buf.write('- `*` マークはモデル予測のみ（BPI/CPI 実データなし）\n\n')
    buf.write('---\n\n')

    levels = sorted(df['level'].unique(), reverse=True)
    for lvl in levels:
        sub = df[df['level'] == lvl].copy()
        spa = sub[sub['chart_type'] == 'SPA'].sort_values('title')
        spl = sub[sub['chart_type'] == 'SPL'].sort_values('title')

        buf.write(f'## {lvl:.1f}  （{len(sub)} 曲）\n\n')

        if not spa.empty:
            buf.write('### SPA\n\n')
            buf.write('| 曲名 | 個人差 |\n')
            buf.write('|------|--------|\n')
            for _, row in spa.iterrows():
                mark = ' *' if row['estimated'] else ''
                buf.write(f'| {row["title"]}{mark} | {row["kojinsa_disp"]} |\n')
            buf.write('\n')

        if not spl.empty:
            buf.write('### SPL\n\n')
            buf.write('| 曲名 | 個人差 |\n')
            buf.write('|------|--------|\n')
            for _, row in spl.iterrows():
                mark = ' *' if row['estimated'] else ''
                buf.write(f'| {row["title"]}{mark} | {row["kojinsa_disp"]} |\n')
            buf.write('\n')

    return buf.getvalue()


def main():
    import os
    os.makedirs('docs', exist_ok=True)

    df = load_tables()
    md = build_md(df)

    with open('docs/difficulty_table.md', 'w', encoding='utf-8') as f:
        f.write(md)

    total = len(df)
    estimated = df['estimated'].sum()
    print(f'Written: docs/difficulty_table.md')
    print(f'Total: {total} songs ({total - estimated} with data, {estimated} estimated *)')


if __name__ == '__main__':
    main()
