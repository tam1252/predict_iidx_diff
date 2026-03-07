import math
import re
import requests
from bs4 import BeautifulSoup
import json

B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def decode_textage_sp(sp_array, measure_lens):
    """
    sp_array: list of strings (raw sp[n] from JS)
    measure_lens: list or dict of measure lengths. Default is 192 if not specified.
    Returns a list of dicts: {'measure': int, 'pos': int, 'key': int}
    """
    notes = []
    
    for n, sdd in enumerate(sp_array):
        # measure_lens might be incomplete, default to 192 (LNDEF)
        ln_n = measure_lens.get(n, 192) if isinstance(measure_lens, dict) else (measure_lens[n] if n < len(measure_lens) else 192)
        
        if not sdd or sdd == "00":
            continue
            
        if sdd.startswith("#"):
            sft = 1
            v2c = 0
            while sft < len(sdd):
                v2o = ""
                v2v = (1 if v2c else 3) * ln_n / 6
                ch = sdd[sft]
                v2s = 0; v2p = 0; v2t = 0
                
                if ch in "CcRrPp":
                    if ch == 'C': v2s, v2p = 0, 192
                    elif ch == 'c': v2s, v2p = 96, 192
                    elif ch == 'R': v2s, v2p = 0, 96
                    elif ch == 'r': v2s, v2p = 48, 96
                    elif ch == 'P': v2s, v2p = 0, 48
                    elif ch == 'p': v2s, v2p = 24, 48
                    v2t = 0
                    if not v2c:
                        sft += 1
                        if sft < len(sdd): v2o = sdd[sft]
                    sft += 1
                    
                elif ch in "BbQqOoXxZzSsTtUu":
                    if ch == 'B': v2s, v2p = 0, 192
                    elif ch == 'b': v2s, v2p = 96, 192
                    elif ch == 'Q': v2s, v2p = 0, 96
                    elif ch == 'q': v2s, v2p = 48, 96
                    elif ch == 'O': v2s, v2p = 0, 48
                    elif ch == 'o': v2s, v2p = 24, 48
                    elif ch == 'X': v2s, v2p = 0, 24
                    elif ch == 'x': v2s, v2p = 12, 24
                    elif ch == 'Z': v2s, v2p = 0, 12
                    elif ch == 'z': v2s, v2p = 6, 12
                    elif ch == 'S': v2s, v2p = 0, 64
                    elif ch == 's': v2s, v2p = 32, 64
                    elif ch == 'T': v2s, v2p = 0, 32
                    elif ch == 't': v2s, v2p = 16, 32
                    elif ch == 'U': v2s, v2p = 0, 16
                    elif ch == 'u': v2s, v2p = 8, 16
                    else: v2p = 192 # fallback to prevent ZeroDivisionError
                    v2t = 1
                    v2b = math.ceil(v2v / v2p) + 1
                    v2o = sdd[sft+1:sft+v2b]
                    sft += v2b
                    
                elif ch in "1234567":
                    v2o = sdd[sft:sft+3]
                    v2t = 2
                    sft += 3
                    
                elif ch == "9" or ch == "8":
                    if ch == "9":
                        v2o = "1" + sdd[sft+2:sft+4]
                    else:
                        v2o = ""
                    b64_val = B64.find(sdd[sft+1]) if sft+1 < len(sdd) else -1
                    if b64_val != -1:
                        for i2 in range(6):
                            if b64_val & (1 << i2):
                                # append key logic (i2+2)
                                v2o += str(i2+2) + sdd[sft+2:sft+4]
                    v2t = 2
                    sft += 4
                    
                elif ch == "-":
                    v2c = 1
                    sft += 1
                    continue
                elif ch == "_":
                    v2o = "AA" if sft == len(sdd)-1 else sdd[sft+1:]
                    v2c = 2
                    v2t = 2
                else:
                    break
                    
                if sft > 0 and sft-1 < len(sdd) and sdd[sft-1] == "-":
                    continue
                    
                v2k = ""
                if v2t == 1:
                    for i2 in range(len(v2o)):
                        if v2c == 0:
                            v2x = B64.find(v2o[i2])
                            v2k += str(v2x // 8) + str(v2x % 8)
                        elif v2c == 1:
                            v2x = B64.find(v2o[i2])
                            for i3 in range(5, -1, -1):
                                v2k += "1" if (v2x >> i3) & 1 else "0"
                elif v2t == 0:
                    i2 = v2s
                    while i2 < ln_n:
                        v2k += "1" if v2c else v2o
                        i2 += v2p
                        
                if v2t != 2:
                    v2i = 0
                    i2 = v2s
                    while i2 < ln_n and v2i < len(v2k):
                        ob2 = v2k[v2i]
                        if ob2 != "0" and ob2 != "-":
                            if v2c:
                                key_val = 0
                            else:
                                try:
                                    key_val = int(ob2)
                                except ValueError:
                                    key_val = 8 # ignore invalid key
                                    
                            if key_val < 8:
                                notes.append({'measure': n, 'pos': i2, 'key': key_val})
                        v2i += 1
                        i2 += v2p
                else:
                    i2 = 0
                    while i2 < len(v2o):
                        if v2c == 0:
                            ob2 = v2o[i2]
                            i2 += 1
                        else:
                            ob2 = "0"
                        if i2+1 < len(v2o):
                            ch1, ch2 = v2o[i2], v2o[i2+1]
                            v2h = B64.find(ch1)*64 + B64.find(ch2)
                            try:
                                key_val = 0 if v2c else int(ob2)
                            except ValueError:
                                key_val = 8
                            if key_val < 8:
                                notes.append({'measure': n, 'pos': v2h, 'key': key_val})
                        i2 += 2
                        
                if v2c == 2:
                    break
                    
        else:
            sft = 0
            if sdd.startswith("x"):
                if len(sdd) >= 4:
                    length = int(sdd[1:4], 16)
                else:
                    length = len(sdd)
                sft = 4
            else:
                length = len(sdd)
                
            div = 0
            while sft < len(sdd):
                while sft < len(sdd) and sdd[sft] == "@":
                    val = int(sdd[sft+1:sft+3], 16) * 2
                    div += val
                    sft += 3
                if sft+2 <= len(sdd):
                    # Sometimes textage uses small missing blocks, guard against it
                    try:
                        y = int(sdd[sft:sft+2], 16)
                    except ValueError:
                        y = 0
                        
                    for j in range(8):
                        if (y >> j) == 0:
                            break
                        if (y >> j) & 1:
                            time_pos = int(ln_n * div / length)
                            notes.append({'measure': n, 'pos': time_pos, 'key': j})
                sft += 2
                div += 2

    return notes


def get_score_data(url: str, diff_query: str = "A"):
    """
    diff_query: 'L' (Leggendaria), 'A' (Another), 'H' (Hyper), 'N' (Normal)
    url params override this, but we parse everything from DOM.
    """
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    html_text = res.text
    
    script_content = ""
    start_idx = html_text.find("genre")
    if start_idx != -1:
        # Search backwards to find <script
        script_start = html_text.rfind("<script", 0, start_idx)
        if script_start != -1:
            script_end = html_text.find("</script>", start_idx)
            if script_end != -1:
                script_content = html_text[script_start:script_end]
    
    if not script_content:
        script_content = html_text
    
    # measure lengths
    measure_lens = {}
    for m in re.finditer(r'ln\[(\d+)\]=(\d+);', script_content):
        measure_lens[int(m.group(1))] = int(m.group(2))
        
    sp_matches = list(re.finditer(r'sp\s*=\s*\[(.*?)\];', script_content, re.DOTALL))
    all_sp_arrays = []
    for m in sp_matches:
        raw_elements = m.group(1).split(',')
        cleaned = []
        for e in raw_elements:
            e = e.strip()
            if not e: cleaned.append(None)
            elif e.startswith('"') or e.startswith("'"): cleaned.append(e[1:-1])
            else: cleaned.append(e)
        all_sp_arrays.append(cleaned)
        
    # Textage usually ordered: L(if kuro), A(if a), N, H ...
    # We heuristically find the best array: 
    # If L, it tends to be the first one with max notes. Or we can just count items.
    
    target_sp = []
    if all_sp_arrays:
        # Just sort by amount of non-null blocks as a proxy for difficulty if we map A/L
        all_sp_arrays.sort(key=lambda arr: len([x for x in arr if x]), reverse=True)
        # Default to hardest
        target_sp = all_sp_arrays[0]
        
    notes = decode_textage_sp(target_sp, measure_lens)
    
    return notes


if __name__ == "__main__":
    url = "https://textage.cc/score/21/verflcht.html?1XC00"
    notes = get_score_data(url)
    print(f"Decoded {len(notes)} notes.")
    if notes:
        print("First 10 notes:", notes[:10])
        print("Last 10 notes:", notes[-10:])
