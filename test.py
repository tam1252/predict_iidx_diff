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
        純粋なビット展開方式に絞る。
        bit0:1鍵, bit1:2鍵, bit2:3鍵, bit3:4鍵, bit4:5鍵, bit5:6鍵, bit6:7鍵
        """
        if val == 0: return []
        # 1-7 は単発（互換性のため維持）
        if 1 <= val <= 7: return [val]
        
        res = []
        # bit0〜bit6 までをチェック
        for i in range(7):
            if (val >> i) & 1:
                res.append(i + 1)
        return res

    def decode_hash_format(self, sdd, ln_n=384):
        notes = []
        idx = 1
        v2c = 0; v2p = 192; v2s = 0; cur_pos = 0
        
        config = {
            "C": (192, 0), "c": (192, 96), "D": (48, 0), "d": (48, 24),
            "R": (48, 0), "r": (48, 24), "V": (64, 0), "v": (64, 32),
            "P": (64, 0), "p": (64, 32)
        }

        while idx < len(sdd):
            char = sdd[idx]
            
            # 1. 密度コマンド
            if char in config:
                v2p, v2s = config[char]
                idx += 1
                # 敷き詰めロジック (R1a などの形式)
                if idx < len(sdd) and sdd[idx] in "123456789":
                    lane = int(sdd[idx]); idx += 1
                    if idx < len(sdd) and sdd[idx] not in "CcDdRrVvPpX123456789-_":
                        for pos in range(v2s, ln_n, v2p):
                            notes.append({"pos": pos, "lane": lane})
                        idx += 1
                        continue
                cur_pos = v2s
                continue

            # 2. 座標直接指定
            elif char == "X":
                if idx + 3 < len(sdd) and sdd[idx+2] in self.B64:
                    lane_val = self._b64_to_val(sdd[idx+1])
                    v2h = self._b64_to_val(sdd[idx+2]) * 64 + self._b64_to_val(sdd[idx+3])
                    pos = (v2h * ln_n) // 384
                    for l in self.expand_lanes(lane_val):
                        notes.append({"pos": pos, "lane": 0 if v2c else l})
                    cur_pos = pos + v2p
                    idx += 4
                elif idx + 2 < len(sdd):
                    v2h = self._b64_to_val(sdd[idx+1]) * 64 + self._b64_to_val(sdd[idx+2])
                    pos = (v2h * ln_n) // 384
                    notes.append({"pos": pos, "lane": 1})
                    cur_pos = pos + v2p
                    idx += 3
                else: idx += 1
                if v2c == 1: v2c = 0
                continue

            elif char in "1234567":
                if idx + 2 < len(sdd):
                    lane = int(char)
                    v2h = self._b64_to_val(sdd[idx+1]) * 64 + self._b64_to_val(sdd[idx+2])
                    pos = (v2h * ln_n) // 384
                    notes.append({"pos": pos, "lane": lane})
                    cur_pos = pos + v2p
                    idx += 3
                else: idx += 1
                continue

            elif char in "89":
                if idx + 3 < len(sdd):
                    mask = self._b64_to_val(sdd[idx+1])
                    v2h = self._b64_to_val(sdd[idx+2]) * 64 + self._b64_to_val(sdd[idx+3])
                    if char == "9": v2h += 4096
                    pos = (v2h * ln_n) // 384
                    for l in self.expand_lanes(mask):
                        notes.append({"pos": pos, "lane": l})
                    cur_pos = pos + v2p
                    idx += 4
                else: idx += 1
                continue

            # 3. 特殊フラグ
            elif char == "-":
                v2c = 1; idx += 1
            elif char == "_":
                v2o = sdd[idx+1:]
                for i in range(0, len(v2o), 2):
                    if i+1 < len(v2o):
                        v2h = self._b64_to_val(v2o[i]) * 64 + self._b64_to_val(v2o[i+1])
                        notes.append({"pos": (v2h * ln_n) // 384, "lane": 0})
                break

            # 4. 救済ロジック
            else:
                val = self._b64_to_val(char)
                if val > 0:
                    for l in self.expand_lanes(val):
                        notes.append({"pos": cur_pos % ln_n, "lane": l})
                cur_pos += v2p
                idx += 1
                if v2c == 1: v2c = 0
        
        return notes

    # decode_hex_format と parse_url は 2032ノーツを出したときと同じものを使用
    def decode_hex_format(self, sdd, ln_n=384):
        notes = []
        idx = 4 if sdd.startswith('x') else 0
        div = 0; step = 24 
        while idx < len(sdd):
            if sdd[idx] == "@":
                try: div += int(sdd[idx+1:idx+3], 16) * 2; idx += 3
                except: idx += 1
                continue
            try:
                val = int(sdd[idx:idx+2], 16)
                for lane in range(8):
                    if (val >> lane) & 1: notes.append({"pos": div, "lane": lane})
                idx += 2; div += step
            except: idx += 1
        return notes

    def parse_url(self, url):
        res = requests.get(url)
        res.encoding = 'shift_jis'
        text = res.text
        sp_match = re.search(r'sp=\[,(.*?)]', text, re.DOTALL)
        if not sp_match: return None
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
        return results

if __name__ == "__main__":
    url = "https://textage.cc/score/21/verflcht.html?1XC00"
    decoder = TextageDecoder()
    data = decoder.parse_url(url)
    if data:
        total = sum(len(notes) for notes in data["normal"].values())
        print(f"合計ノーツ数: {total}")
        print("--- 小節別ノーツ数チェック ---")
        for m in sorted(data["normal"].keys()):
            if len(data["normal"][m]) > 0:
                print(f"Measure {m:02}: {len(data['normal'][m])} notes")