import requests
import re
from py_mini_racer import MiniRacer

# TextageDecoder (v6) with per-measure count
class TextageDecoder:
    def __init__(self):
        self.B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

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

    def decode_cn(self, cn_data, side=1):
        side_key = "c1" if side == 1 else "c2"
        result = {}
        for measure, entries in cn_data[side_key].items():
            result[measure] = []
            for e in entries:
                if e["flag"] in (1, 3, 7):
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

    def decode_hash_format(self, sdd, ln_n=384):
        import math as _math
        CMDS_T0 = {"C": (192,  0), "c": (192, 96), "R": ( 96,  0), "r": ( 96, 48), "P": ( 48,  0), "p": ( 48, 24)}
        CMDS_T1 = {"B": (192,  0), "b": (192, 96), "Q": ( 96,  0), "q": ( 96, 48), "O": ( 48,  0), "o": ( 48, 24),
                   "X": ( 24,  0), "x": ( 24, 12), "Z": ( 12,  0), "z": ( 12,  6), "S": ( 64,  0), "s": ( 64, 32),
                   "T": ( 32,  0), "t": ( 32, 16), "U": ( 16,  0), "u": ( 16,  8), "V": (  8,  0), "v": (  8,  4),
                   "W": (  4,  0), "w": (  4,  2)}
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
                v2t = 0
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
                v2t = 1
            elif char in "1234567":
                v2o = sdd[sft : sft + 3]
                sft += 3
                v2t = 2
            elif char == "8" or char == "9":
                v2o = "1" + sdd[sft+2:sft+4] if char == "9" else ""
                b64_val = self._b64_to_val(sdd[sft+1]) if sft+1 < len(sdd) else -1
                if b64_val != -1:
                    for i2 in range(6):
                        if b64_val & (1 << i2):
                            v2o += str(i2+2) + sdd[sft+2:sft+4]
                sft += 4
                v2t = 2
            elif char == "-":
                v2c = 1
                sft += 1
                continue
            elif char == "_":
                v2o = "AA" if sft == len(sdd) - 1 else sdd[sft + 1:]
                v2c = 2
                v2t = 2
            else:
                sft += 1
                continue
            if sft > 0 and sft-1 < len(sdd) and sdd[sft-1] == "-":
                continue
            if v2t != 2:
                v2i = 0
                i2 = v2s
                while i2 < ln_n and v2i < len(v2k):
                    ob2_c = v2k[v2i]
                    if ob2_c and ob2_c != "0":
                        lane = 0 if v2c else int(ob2_c)
                        notes.append({"pos": i2, "lane": lane, "type": f"v2t{v2t}"})
                    v2i += 1
                    i2 += v2p
            else:
                i2 = 0
                while i2 < len(v2o):
                    if v2c == 0:
                        ob2_char = v2o[i2]
                        i2 += 1
                    else:
                        ob2_char = "0"
                    if i2+1 < len(v2o):
                        ch1  = v2o[i2]
                        ch2  = v2o[i2+1]
                        v2h = self._b64_to_val(ch1) * 64 + self._b64_to_val(ch2)
                        try:
                            lane = 0 if v2c else int(ob2_char)
                        except:
                            lane = 8
                        if lane < 8:
                            notes.append({"pos": v2h, "lane": lane, "type": "v2t2"})
                        i2 += 2
                    else:
                        break
            if v2c == 2:
                break
            v2c = 0
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
            while idx < len(sdd) and sdd[idx] == "@":
                try:
                    div += int(sdd[idx+1:idx+3], 16) * 2
                except:
                    pass
                idx += 3
            if idx >= len(sdd):
                break
            if idx + 2 <= len(sdd):
                try:
                    val = int(sdd[idx:idx+2], 16)
                    pos = ((nbar * div) // sft_len) * 3
                    for lane in self.expand_lanes(val):
                        notes.append({"pos": pos, "lane": lane, "type": "hex"})
                except:
                    pass
            idx += 2
            div += 2
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

    def deduplicate_notes(self, normal_dict):
        result = {}
        for measure, notes in normal_dict.items():
            filtered_notes = [n for n in notes if n.get("type") != "cn_end"]
            unique_notes = set()
            for n in filtered_notes:
                unique_notes.add((n["pos"], n["lane"]))
            result[measure] = len(unique_notes)
        return result

    def parse_url(self, html):
        text = html
        measure_lens = {}
        for m in re.finditer(r'ln\[(\d+)\]=(\d+);', text):
            measure_lens[int(m.group(1))] = int(m.group(2))

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
            ln_n = measure_lens.get(measure_num, 384)

            m_data = ""
            if p.startswith('"'):
                m_data = p.strip('"')
            elif p.startswith('sp['):
                ref_idx = int(re.search(r'\d+', p).group())
                m_data = results_raw.get(ref_idx, "")
            
            results_raw[measure_num] = m_data
            
            if m_data:
                if m_data.startswith('#'):
                    results["normal"][measure_num] = self.decode_hash_format(m_data, ln_n)
                else:
                    results["normal"][measure_num] = self.decode_hex_format(m_data, ln_n)
            else:
                results["normal"][measure_num] = []

        cn = self.parse_cn_arrays(text)
        cn_notes = self.decode_cn(cn, side=1)
        for measure, notes in cn_notes.items():
            if measure not in results["normal"]:
                results["normal"][measure] = []
            results["normal"][measure].extend(notes)

        return results


def run_js(html):
    # Extract JS payload
    comment_start = html.find('<!--')
    func_hd_call = html.find('hd();')
    js_payload = html[comment_start + 4 : func_hd_call]

    with open("references/bars_function.txt", "r") as f:
        bars_js = f.read()

    # NOTE: Set kuro=1, a=1 to parse Leggendaria exactly
    js_code = """
    var document = { write: function(){} };
    var window = {};
    var s = "1XC00";
    var LNDEF = 384;
    var stat_on = 0, off = 0, prt = 0, ty = 1, d = 0, gap = 1, hsa = 1, hs = 1, DEFHSA = 1, back = 6;
    var barnotes = 0, db = 0, flp = 0, os = 0, legacy = 0, hcn = 0, m = 0;
    var ty = 1;
    var dw = [200, 200];
    var dr = [200, 200];
    var sides = [0, 1, 2];
    var df = [200, 200];
    var imgdir = "";
    var csd = ["left", "right", "left"];
    var ms = ["0", "0"];
    var co = ["", "", "", "", "", "", "", "", ""];
    var cob = ["", "", "", "", "", "", "", "", ""];
    var dstr = "";
    var coy = 0;
    var ttl = 0, ttlcn = 0, cncnt = 0, bsscnt = 0;
    var npos = [], p1o = 0;
    var kc = [[0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0]];
    var nmergin = {};
    var objres = {1:[0,0], 2:[0,0]};
    var objtab = {};
    var kuro = 1, k = 1, a = 1, l = 1, notes = 0, stat_pos = 0;
    
    var ln=[],sp=[],dp=[],tc=[],c1=[],c2=[],cn=[];
    var sc32=[],sc32base=[],sc32loop=[],sd=[],hids=0,alls=0,sran=0,key=7,ky=7,conum=1;
    """ + js_payload + """

    sd = [null, sp, dp, [], []];
    cn = [null, c1, c2];
    var measure = sp.length - 1;

    var obr = [[0,1,2,3,4,5,6,7], [0,1,2,3,4,5,6,7]];
    var dpalls = [[0,1,2,3,4,5,6,7], [0,1,2,3,4,5,6,7]];
    var b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    var cnc = [0, 0, 0];
    
    function set_co(h) {}
    function stat_insert() {}
    function dragOn() {}
    function cn_sort(a, b) { return a[1] - b[1]; }

    """ + bars_js + """
    
    }

    var true_notes_per_measure = {};
    for (var n = 1; n < sp.length; n++) {
        var start_ttl = ttl;
        var start_ttlcn = ttlcn;
        bars_(n, undefined);
        true_notes_per_measure[n] = {
           ttl_diff: ttl - start_ttl,
           ttlcn_diff: ttlcn - start_ttlcn
        };
    }
    
    JSON.stringify({ttl: ttl, ttlcn: ttlcn, measures: true_notes_per_measure});
    """
    ctx = MiniRacer()
    import json
    return json.loads(ctx.eval(js_code))


def main():
    url = "https://textage.cc/score/21/verflcht.html?1XC00"
    html = requests.get(url).text
    
    # 1. Get JS output
    js_data = run_js(html)
    js_ttl = js_data["ttl"]
    js_measures = js_data["measures"]
    
    # 2. Get Python output
    decoder = TextageDecoder()
    py_data = decoder.parse_url(html)
    py_measures = decoder.deduplicate_notes(py_data["normal"])
    py_ttl = sum(py_measures.values())
    
    print(f"Total Notes -> JS: {js_ttl}, Python: {py_ttl}")
    diff_count = 0
    
    for m in sorted(py_measures.keys()):
        p_val = py_measures[m]
        j_val = js_measures[str(m)]["ttl_diff"]
        if p_val != j_val:
            print(f"Measure {m}: JS={j_val}, Python={p_val} (diff={p_val - j_val})")
            diff_count += 1
            
    if diff_count == 0:
        print("PERFECT MATCH FOR ALL MEASURES!")

if __name__ == "__main__":
    main()
