import math

B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def decode_measure(sdd: str, ln_n: int = 192):
    notes = [] # list of dicts: {'pos': int, 'key': int}
    
    if not sdd or sdd == "00":
        return notes

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
                elif ch == 'S': v2s, v2p = 0, 64
                elif ch == 's': v2s, v2p = 32, 64
                elif ch == 'T': v2s, v2p = 0, 32
                elif ch == 't': v2s, v2p = 16, 32
                elif ch == 'U': v2s, v2p = 0, 16
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
                # handle loop in JS: case 8 or fallthrough from 9
                b64_val = B64.find(sdd[sft+1]) if sft+1 < len(sdd) else -1
                if b64_val != -1:
                    for i2 in range(6):
                        if b64_val & (1 << i2):
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
                # sft is not updated here, the break happens in JS if v2c==2
            else:
                # unknown or error
                break
                
            if sft > 0 and sft-1 < len(sdd) and sdd[sft-1] == "-":
                continue
                
            v2k = ""
            if v2t == 1:
                # v2o are chars from B64
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
                # Decode from v2k mask
                v2i = 0
                i2 = v2s
                while i2 < ln_n and v2i < len(v2k):
                    ob2 = v2k[v2i]
                    if ob2 != "0":
                        notes.append({'pos': i2, 'key': ob2})
                    v2i += 1
                    i2 += v2p
            else:
                # v2t == 2
                i2 = 0
                while i2 < len(v2o):
                    if v2c == 0:
                        ob2 = v2o[i2]
                        i2 += 1
                    else:
                        ob2 = "0"
                    if ob2 == "0" and False: # hids mapping (skipped)
                        pass
                    if i2+1 < len(v2o):
                        # decode time pos from base64 string pairs
                        ch1, ch2 = v2o[i2], v2o[i2+1]
                        v2h = B64.find(ch1)*64 + B64.find(ch2)
                        notes.append({'pos': v2h, 'key': ob2})
                    i2 += 2
                    
            if v2c == 2:
                break
                
    else:
        # Standard hex format
        sft = 0
        if sdd.startswith("x"):
            # x + 3 chars hex length length (e.g. x010)
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
                y = int(sdd[sft:sft+2], 16)
                for j in range(8):
                    if (y >> j) == 0:
                        break
                    if (y >> j) & 1:
                        # nbar * div * 3 / len equivalent?
                        # wait, mathematically: time_pos = (ln_n * div) / (length * 2) 
                        # In JS: nbar*div*3/len ... nbar is ln[n]/3, so (ln[n]/3 * div * 3) / len = ln_n * div / len
                        # actually: time_pos = int((ln_n * div) / length)  <-- this maps 0~len to 0~ln_n
                        time_pos = int(ln_n * div / length)
                        notes.append({'pos': time_pos, 'key': j})
            sft += 2
            div += 2

    return notes

if __name__ == "__main__":
    test_str = "x010cb@02d5@02a700"  # Hex string test
    test_str2 = "#R1R3XEV3U6m+sq9o_" # B64 compressed test
    
    print("Test Hex:", decode_measure(test_str, 192))
    print("Test B64:", decode_measure(test_str2, 192))
