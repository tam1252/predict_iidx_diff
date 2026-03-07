import requests
import re

class TextageDecoder:
    def __init__(self):
        self.B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        self.LNDEF = 384

    def _b64_to_val(self, char):
        val = self.B64.find(char)
        return val if val != -1 else 0

    def expand_lanes(self, val):
        """
        ✅ 修正: ビットずれを修正。
        bit0=レーン0(ターンテーブル), bit1=1鍵, ..., bit7=7鍵
        """
        if val == 0:
            return []
        # range(8), j をそのままレーン番号として返す
        return [j for j in range(8) if (val >> j) & 1]

    def _expand_note(self, note):
        """
        note >= 10 は各桁をレーン番号として展開。
        例: 57 → [7, 5],  135 → [5, 3, 1]
        lmtakブログ: "57 は 5 鍵と 7 鍵の同時押しチャージノーツ"
        """
        if note <= 9:
            return [note]
        lanes = []
        while note > 0:
            lanes.append(note % 10)
            note //= 10
        return lanes

    def parse_cn_arrays(self, text):
        """
        JSテキストから c1/c2 配列を抽出してPython辞書に変換。
        戻り値: {side: {measure: [[note, start, length, flag], ...]}}
          side=1: SP/DP-1P側,  side=2: DP-2P側
        """
        import re
        cn = {1: {}, 2: {}}
        for m in re.finditer(r'(c[12])\[(\d+)\]=(\[\[.*?\]\])', text):
            side    = 1 if m.group(1) == 'c1' else 2
            measure = int(m.group(2))
            raw     = m.group(3)
            entries = re.findall(r'\[([^\[\]]+)\]', raw)
            cn[side][measure] = []
            for entry in entries:
                parts  = [int(x.strip()) for x in entry.split(',')]
                note   = parts[0]
                start  = parts[1] if len(parts) > 1 else 0
                length = parts[2] if len(parts) > 2 else 30
                flag   = parts[3] if len(parts) > 3 else 3
                cn[side][measure].append([note, start, length, flag])
        return cn

    def decode_cn(self, cn, side=1):
        """
        c1/c2辞書からノーツリストを生成。
        ノーツカウント対象は始端 (flag & 1 == 1) のみ。
        終端 (cn_end) は type で区別するがカウント対象外。

        lmtakブログより:
          始端: flag & 1 == 1  (flag=1,3,7)
          終端: note==0 and flag & 2 == 2  (TT限定)
          start の単位: 4分音符1つ=32 (nbarスケール)
          → pos(0〜384) = start * 3
        """
        result = {}
        for measure, entries in cn[side].items():
            notes = []
            for entry in entries:
                note, start, length, flag = entry
                pos = start * 3   # nbarスケール → 0〜384スケールに変換

                # 始端ノーツ配置
                if flag & 1:
                    for lane in self._expand_note(note):
                        notes.append({"pos": pos, "lane": lane, "type": "cn_start"})

                # 終端ノーツ配置 (TT=0 限定、カウント対象外)
                if note == 0 and (flag & 2):
                    end_pos = pos + length * 3
                    notes.append({"pos": end_pos, "lane": 0, "type": "cn_end"})

            if notes:
                result[measure] = notes
        return result

    def decode_hash_format(self, sdd, ln_n=384):
        """
        '#' 始まりの小節データをデコード。
        bms2jsh.js の switch 文を完全に再現。

        コマンド一覧 (bms2jsh.js ソース確定):
          v2t=0 (次の1文字がレーン番号、等間隔繰り返し配置):
            C(v2p=192,v2s=0)  c(192,96)
            R(96,0)  r(96,48)  P(48,0)  p(48,24)
          v2t=1 (B64文字列→8進数2桁展開→各桁=レーン番号):
            B(192,0) b(192,96) Q(96,0) q(96,48) O(48,0) o(48,24)
            X(24,0)  x(24,12)  Z(12,0)
            S(64,0)  s(64,32)  T(32,0) t(32,16) U(16,0)
          v2t=2 (絶対位置指定):
            1〜7: lane(文字) + pos(B64 2文字)
            8   : bitmask(B64 1文字) + pos(B64 2文字) → lane 2〜7
            9   : lane=1固定 + 8と同じfall-through
          特殊:
            -: v2c=1(チャージ範囲マーク)、次コマンドはノーツ非生成
            _: 残り全部TT(ターンテーブル)を絶対位置で配置
        """
        import math as _math

        # v2t=0 コマンド: (v2p, v2s)
        CMDS_T0 = {
            "C": (192,  0), "c": (192, 96),
            "R": ( 96,  0), "r": ( 96, 48),
            "P": ( 48,  0), "p": ( 48, 24),
        }
        # v2t=1 コマンド: (v2p, v2s)
        CMDS_T1 = {
            "B": (192,  0), "b": (192, 96),
            "Q": ( 96,  0), "q": ( 96, 48),
            "O": ( 48,  0), "o": ( 48, 24),
            "X": ( 24,  0), "x": ( 24, 12),
            "Z": ( 12,  0),
            "S": ( 64,  0), "s": ( 64, 32),
            "T": ( 32,  0), "t": ( 32, 16),
            "U": ( 16,  0),
        }

        notes = []
        sft   = 1      # '#' の次
        v2c   = 0      # 0=通常, 1=チャージ範囲フラグ, 2=TT強制(_後)

        while sft < len(sdd):
            # v2v: v2oから読む文字数の基準値
            # JS: v2v = (v2c ? 1 : 3) * ln[n] / 6
            v2v  = (1 if v2c else 3) * ln_n // 6
            char = sdd[sft]

            # ── v2t=0: 次の1文字がレーン番号、等間隔に繰り返し配置 ──
            if char in CMDS_T0:
                v2p, v2s = CMDS_T0[char]
                if not v2c:
                    sft += 1
                    v2o = sdd[sft] if sft < len(sdd) else ""
                sft += 1
                # v2c=0 のとき、レーン番号文字 v2o を v2s, v2s+v2p, ... に配置
                if not v2c and v2o.isdigit() and int(v2o) != 0:
                    lane = int(v2o)
                    for i2 in range(v2s, ln_n, v2p):
                        notes.append({"pos": i2, "lane": lane})
                v2c = 0

            # ── v2t=1: B64文字列→8進数2桁展開→各桁がレーン番号 ────
            elif char in CMDS_T1:
                v2p, v2s = CMDS_T1[char]
                # JS: v2b = Math.ceil(v2v/v2p)+1; v2o = sdd.substring(sft+1, sft+v2b)
                v2b = _math.ceil(v2v / v2p) + 1
                v2o = sdd[sft + 1 : sft + v2b]
                sft += v2b

                # v2k 生成: B64値を8進数2桁(v2c=0)またはビット列(v2c=1)に展開
                v2k = ""
                for ch in v2o:
                    v2x = self._b64_to_val(ch)
                    if v2c == 0:
                        v2k += str(v2x // 8) + str(v2x % 8)
                    else:  # v2c == 1
                        for i3 in range(5, -1, -1):
                            v2k += "1" if (v2x >> i3) & 1 else "0"

                # v2k を1文字ずつ読んで配置
                # JS: if((ob2=v2k.charAt(v2i)) != 0) { ... ttl++ ... }
                # "0" のときスキップ、"1"〜"7" がレーン番号
                v2i = 0
                i2  = v2s
                while i2 < ln_n:
                    ob2_c = v2k[v2i] if v2i < len(v2k) else "0"
                    if ob2_c != "0" and ob2_c.isdigit() and v2c == 0:
                        notes.append({"pos": i2, "lane": int(ob2_c)})
                    v2i += 1
                    i2  += v2p
                v2c = 0

            # ── v2t=2 数字 "1"〜"7": lane + 絶対pos(B64 2文字) ──────
            elif char in "1234567":
                # JS: v2o=sdd.substring(sft,sft+3); v2t=2; sft+=3;
                v2o = sdd[sft : sft + 3]
                sft += 3
                ob2 = int(v2o[0])
                v2h = (self._b64_to_val(v2o[1]) * 64 +
                       self._b64_to_val(v2o[2])) if len(v2o) >= 3 else 0
                if v2c == 0:
                    notes.append({"pos": v2h, "lane": ob2})
                v2c = 0

            # ── v2t=2 "8": bitmask → lane 2〜7 ──────────────────────
            elif char == "8":
                mask = self._b64_to_val(sdd[sft + 1]) if sft + 1 < len(sdd) else 0
                v2h  = (self._b64_to_val(sdd[sft + 2]) * 64 +
                        self._b64_to_val(sdd[sft + 3])) if sft + 3 < len(sdd) else 0
                sft += 4
                for i2 in range(6):
                    if mask & (1 << i2) and v2c == 0:
                        notes.append({"pos": v2h, "lane": i2 + 2})
                v2c = 0

            # ── v2t=2 "9": lane=1 強制 + fall-through to "8" ─────────
            elif char == "9":
                mask = self._b64_to_val(sdd[sft + 1]) if sft + 1 < len(sdd) else 0
                v2h  = (self._b64_to_val(sdd[sft + 2]) * 64 +
                        self._b64_to_val(sdd[sft + 3])) if sft + 3 < len(sdd) else 0
                sft += 4
                if v2c == 0:
                    notes.append({"pos": v2h, "lane": 1})
                for i2 in range(6):
                    if mask & (1 << i2) and v2c == 0:
                        notes.append({"pos": v2h, "lane": i2 + 2})
                v2c = 0

            # ── "-": v2c=1 フラグ (次コマンドはチャージ範囲、描画なし) ─
            elif char == "-":
                v2c = 1
                sft += 1
                # JS: if(sdd.charAt(sft-1)=="-") continue; → ループ先頭へ
                continue

            # ── "_": 残り全部TT (v2c=v2t=2) ────────────────────────
            elif char == "_":
                # JS: v2o=(sft==sdd.length-1)?"AA":sdd.substring(sft+1); v2c=v2t=2;
                v2o = "AA" if sft == len(sdd) - 1 else sdd[sft + 1:]
                # v2c=2 → ob2=0(TT固定), 2文字ずつ pos を読む
                i2 = 0
                while i2 + 1 < len(v2o):
                    v2h = (self._b64_to_val(v2o[i2]) * 64 +
                           self._b64_to_val(v2o[i2 + 1]))
                    notes.append({"pos": v2h, "lane": 0})
                    i2 += 2
                # JS: if(v2c==2) break;
                break

            else:
                # default: 未知コマンド → スキップ
                sft += 1

        return notes

    def decode_hex_format(self, sdd, ln_n=384):
        """
        ✅ 修正: step固定値(24)をやめ、lmtakブログ準拠の位置計算に変更。

        lmtakブログの該当JS:
            if(sdd.charAt(0)=="x"){ len=parseInt(sdd.substring(1,4),16); sft=4; }
            else len=sdd.length;
            for(;sft<sdd.length;sft+=2,div+=2){
                y = parseInt(sdd[sft:sft+2], 16)
                top = nbar*hs - floor(nbar*div/len) + coy   ← ここがpos計算
            }
        nbar = ceil(ln_n/3) = 128 (ln_n=384のとき)
        pos(0〜ln_n) = floor(nbar * div / sft_len) * 3
        """
        notes = []
        nbar = -(-ln_n // 3)   # ceil(ln_n / 3)

        if sdd.startswith('x'):
            # x以降3文字が16進数のlen (文字数スケールの分母)
            sft_len = int(sdd[1:4], 16)
            idx = 4
        else:
            sft_len = len(sdd)  # 文字数そのまま
            idx = 0

        div = 0
        while idx < len(sdd):
            if sdd[idx] == "@":
                try:
                    div += int(sdd[idx+1:idx+3], 16) * 2
                    idx += 3
                except:
                    idx += 1
                continue
            try:
                val = int(sdd[idx:idx+2], 16)
                pos = ((nbar * div) // sft_len) * 3
                for lane in self.expand_lanes(val):
                    notes.append({"pos": pos, "lane": lane})
                idx += 2
                div += 2
            except:
                idx += 1
        return notes

    def expand_cn_lanes(self, val):
        """
        CNのレーン指定を展開する。
        0:    ターンテーブル
        1〜7: 単発鍵盤
        10以上: 各桁が独立したレーン番号 (例: 57→[5,7], 135→[1,3,5])
        """
        if val == 0:
            return [0]
        if 1 <= val <= 7:
            return [val]
        lanes = []
        while val >= 10:
            lanes.append(val % 10)
            val = val // 10
        lanes.append(val)
        return sorted(set(lanes))

    def parse_cn_arrays(self, text):
        """
        c1/c2配列をパースしてチャージノーツ情報を返す。

        位置単位: CN生座標は「4分音符1つ=32」の単位系
                  通常ノーツposは ln_n=384 スケール → raw * 3 で統一

        flag の意味 (lmtakブログより):
            0 = 前小節から継続・次小節に継続 (中間)
            1 = この小節で開始・次小節に継続 (始端、複数小節CN)
            2 = 前小節から継続・この小節で終端
            3 = この小節で開始して終端 (単小節完結) ← デフォルト
            7 = MSS (Multi Spin Scratch)
        """
        result = {"c1": {}, "c2": {}}
        pattern = r'(c[12])\[(\d+)\]=((?:\[(?:\[.*?\])\])+);'
        for side, measure_str, data_str in re.findall(pattern, text, re.DOTALL):
            measure = int(measure_str)
            if measure not in result[side]:
                result[side][measure] = []
            for entry_str in re.findall(r'\[(\d+(?:,\d+)*)\]', data_str):
                vals = [int(x) for x in entry_str.split(',')]
                lane_raw  = vals[0]
                start_raw = vals[1] if len(vals) > 1 else 0
                length    = vals[2] if len(vals) > 2 else 30  # 省略時=30
                flag      = vals[3] if len(vals) > 3 else 3   # 省略時=3
                start_pos = start_raw * 3
                end_pos   = (start_raw + length) * 3
                for lane in self.expand_cn_lanes(lane_raw):
                    result[side][measure].append({
                        "lane": lane, "start_pos": start_pos,
                        "end_pos": end_pos, "flag": flag,
                    })
        return result

    def decode_cn(self, cn_data, side=1):
        """
        parse_cn_arrays の結果をノーツリストに変換する。

        ノーツカウントの方針:
            flag=1,3 → 始端あり → {"type":"cn_start"} として1ノーツ計上
            flag=0,2 → 始端なし (継続・終端のみ) → {"type":"cn_end"} としてカウント外
        両方とも返すことで、後段でCN範囲の可視化にも使える。
        """
        side_key = "c1" if side == 1 else "c2"
        result = {}
        for measure, entries in cn_data[side_key].items():
            result[measure] = []
            for e in entries:
                if e["flag"] in (1, 3):  # 始端あり → ノーツ1個
                    result[measure].append({
                        "pos":  e["start_pos"],
                        "lane": e["lane"],
                        "type": "cn_start",
                        "end":  e["end_pos"],
                    })
                # flag=0,2 は始端なし → カウント外として記録
                result[measure].append({
                    "pos":  e["end_pos"],
                    "lane": e["lane"],
                    "type": "cn_end",
                })
        return result

    def parse_url(self, url):
        res = requests.get(url)
        res.encoding = 'shift_jis'
        text = res.text

        # --- 通常ノーツ (sp配列) ---
        sp_match = re.search(r'sp=\[,(.*?)\];', text, re.DOTALL)
        if not sp_match:
            return None
        content = sp_match.group(1)
        raw_parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', content)
        results = {"normal": {}}
        results_raw = {}
        for i, p in enumerate(raw_parts):
            p = p.strip()
            measure_num = i + 1
            m_data = ""
            if p.startswith('"'):
                m_data = p.strip('"')
            elif p.startswith('sp['):
                ref_idx = int(re.search(r'\d+', p).group())
                m_data = results_raw.get(ref_idx, "")
            results_raw[measure_num] = m_data
            if m_data:
                if m_data.startswith('#'):
                    results["normal"][measure_num] = self.decode_hash_format(m_data)
                else:
                    results["normal"][measure_num] = self.decode_hex_format(m_data)
            else:
                results["normal"][measure_num] = []

        # --- チャージノーツ (c1/c2配列) ---
        cn = self.parse_cn_arrays(text)
        cn_notes = self.decode_cn(cn, side=1)
        for measure, notes in cn_notes.items():
            if measure not in results["normal"]:
                results["normal"][measure] = []
            results["normal"][measure].extend(notes)

        return results

if __name__ == "__main__":
    url = "https://textage.cc/score/21/verflcht.html?1XC00"
    decoder = TextageDecoder()
    data = decoder.parse_url(url)
    if data:
        # cn_end はノーツカウント対象外
        total = sum(
            1 for notes in data["normal"].values()
            for n in notes if n.get("type") != "cn_end"
        )
        print(f"合計ノーツ数: {total}  (公式: 2401)")
        print("--- 小節別ノーツ数チェック ---")
        for m in sorted(data["normal"].keys()):
            count = sum(1 for n in data["normal"][m] if n.get("type") != "cn_end")
            if count > 0:
                print(f"Measure {m:02}: {count} notes")