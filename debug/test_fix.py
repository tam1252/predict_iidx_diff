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
        if val == 0:
            return []
        return [j for j in range(8) if (val >> j) & 1]

    def _expand_note(self, note):
        if note <= 9:
            return [note]
        lanes = []
        while note > 0:
            lanes.append(note % 10)
            note //= 10
        return lanes

    def parse_cn_arrays(self, text):
        cn = {1: {}, 2: {}}
        for m in re.finditer(r'(c[12])\[(\d+)\]=((?:\[(?:\[.*?\])\])+);', text):
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
        result = {}
        for measure, entries in cn[side].items():
            notes = []
            for entry in entries:
                note, start, length, flag = entry
                pos = start * 3
                if flag & 1:
                    for lane in self._expand_note(note):
                        notes.append({"pos": pos, "lane": lane, "type": "cn_start"})
                if note == 0 and (flag & 2):
                    end_pos = pos + length * 3
                    notes.append({"pos": end_pos, "lane": 0, "type": "cn_end"})
            if notes:
                result[measure] = notes
        return result

    def decode_hash_format(self, sdd, ln_n=384):
        import math as _math
        CMDS_T0 = {
            "C": (192,  0), "c": (192, 96),
            "R": ( 96,  0), "r": ( 96, 48),
            "P": ( 48,  0), "p": ( 48, 24),
        }
        CMDS_T1 = {
            "B": (192,  0), "b": (192, 96),
            "Q": ( 96,  0), "q": ( 96, 48),
            "O": ( 48,  0), "o": ( 48, 24),
            "X": ( 24,  0), "x": ( 24, 12),
            "Z": ( 12,  0),
            "S": ( 64,  0), "s": ( 64, 32),
            "T": ( 32,  0), "t": ( 32, 16),
            "U": ( 16,  0),
            "u": ( 16,  8),
        }
        notes = []
        sft   = 1
        v2c   = 0
        while sft < len(sdd):
            v2o  = ""
            v2v  = (1 if v2c else 3) * ln_n // 6
            char = sdd[sft]
            v2s = 0; v2p = 0; v2t = 0
            
            if char in CMDS_T0:
                v2p, v2s = CMDS_T0[char]
                if not v2c:
                    sft += 1
                    v2o = sdd[sft] if sft < len(sdd) else ""
                sft += 1
                v2k = ""
                i2 = v2s
                while i2 < ln_n:
                    v2k += "1" if v2c else v2o
                    i2 += v2p
                # process v2k
                v2i = 0
                i2 = v2s
                while i2 < ln_n:
                    ob2_c = v2k[v2i] if v2i < len(v2k) else ""
                    if ob2_c and ob2_c != "0":
                        lane = 0 if v2c else int(ob2_c)
                        notes.append({"pos": i2, "lane": lane})
                    v2i += 1
                    i2 += v2p
                v2c = 0
                
            elif char in CMDS_T1:
                v2p, v2s = CMDS_T1[char]
                v2b = _math.ceil(v2v / v2p) + 1
                v2o = sdd[sft + 1 : sft + v2b]
                sft += v2b
                v2k = ""
                for ch in v2o:
                    v2x = self._b64_to_val(ch)
                    if v2c == 0:
                        v2k += str(v2x // 8) + str(v2x % 8)
                    else:
                        for i3 in range(5, -1, -1):
                            v2k += "1" if (v2x >> i3) & 1 else "0"
                v2i = 0
                i2  = v2s
                while i2 < ln_n:
                    ob2_c = v2k[v2i] if v2i < len(v2k) else ""
                    if ob2_c and ob2_c != "0":
                        lane = 0 if v2c else int(ob2_c)
                        notes.append({"pos": i2, "lane": lane})
                    v2i += 1
                    i2  += v2p
                v2c = 0
                
            elif char in "1234567":
                v2o = sdd[sft : sft + 3]
                sft += 3
                ob2 = int(v2o[0])
                v2h = (self._b64_to_val(v2o[1]) * 64 + self._b64_to_val(v2o[2])) if len(v2o) >= 3 else 0
                if v2c == 0:
                    notes.append({"pos": v2h, "lane": ob2})
                v2c = 0
                
            elif char == "8":
                mask = self._b64_to_val(sdd[sft + 1]) if sft + 1 < len(sdd) else 0
                v2h  = (self._b64_to_val(sdd[sft + 2]) * 64 + self._b64_to_val(sdd[sft + 3])) if sft + 3 < len(sdd) else 0
                sft += 4
                for i2 in range(6):
                    if mask & (1 << i2) and v2c == 0:
                        notes.append({"pos": v2h, "lane": i2 + 2})
                v2c = 0
                
            elif char == "9":
                mask = self._b64_to_val(sdd[sft + 1]) if sft + 1 < len(sdd) else 0
                v2h  = (self._b64_to_val(sdd[sft + 2]) * 64 + self._b64_to_val(sdd[sft + 3])) if sft + 3 < len(sdd) else 0
                sft += 4
                if v2c == 0:
                    notes.append({"pos": v2h, "lane": 1})
                for i2 in range(6):
                    if mask & (1 << i2) and v2c == 0:
                        notes.append({"pos": v2h, "lane": i2 + 2})
                v2c = 0
                
            elif char == "-":
                v2c = 1
                sft += 1
                continue
                
            elif char == "_":
                v2o = "AA" if sft == len(sdd) - 1 else sdd[sft + 1:]
                i2 = 0
                while i2 + 1 < len(v2o):
                    v2h = (self._b64_to_val(v2o[i2]) * 64 + self._b64_to_val(v2o[i2 + 1]))
                    notes.append({"pos": v2h, "lane": 0})
                    i2 += 2
                break
            else:
                sft += 1

        return notes

    def decode_hex_format(self, sdd, ln_n=384):
        notes = []
        nbar = -(-ln_n // 3)

        if sdd.startswith('x'):
            sft_len = int(sdd[1:4], 16)
            idx = 4
        else:
            sft_len = len(sdd)
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
                length    = vals[2] if len(vals) > 2 else 30
                flag      = vals[3] if len(vals) > 3 else 3
                start_pos = start_raw * 3
                end_pos   = (start_raw + length) * 3
                for lane in self.expand_cn_lanes(lane_raw):
                    result[side][measure].append({
                        "lane": lane, "start_pos": start_pos,
                        "end_pos": end_pos, "flag": flag,
                    })
        return result

    def decode_cn(self, cn_data, side=1):
        side_key = "c1" if side == 1 else "c2"
        result = {}
        for measure, entries in cn_data[side_key].items():
            result[measure] = []
            for e in entries:
                if e["flag"] in (1, 3):
                    result[measure].append({
                        "pos":  e["start_pos"],
                        "lane": e["lane"],
                        "type": "cn_start",
                        "end":  e["end_pos"],
                    })
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
        total = sum(
            1 for notes in data["normal"].values()
            for n in notes if n.get("type") != "cn_end"
        )
        print(f"合計ノーツ数: {total}  (公式: 2401)")
