import math

# --- From JS original implementation ---
# if(v2t==1){
#     for(i2=0;i2<v2o.length;i2++){
#         if(v2c==0){
#             v2x=b64.indexOf(v2o.charAt(i2));
#             v2k+=Math.floor(v2x/8)+""+v2x%8;
#         }else if(v2c==1){
#             v2x=b64.indexOf(v2o.charAt(i2));
#             for(i3=5;i3>=0;i3--)v2k+=(v2x>>i3)&1 ? 1:0;
#         }
#     }
# }else if(v2t==0){
#     for(i2=v2s;i2<ln[n];i2+=v2p)v2k+=(v2c ? "1":v2o);
# }
# if(v2t!=2){
#     for(v2i=0,i2=v2s;i2<ln[n];v2i++,i2+=v2p){
#         if(hids && v2c)continue;
#         if((ob2=v2k.charAt(v2i))!=0){ /* ... */ }
#     }
# }else{
#     for(i2=0;i2<v2o.length;){
#         if(v2c==0){ob2=v2o.charAt(i2);i2++;}else ob2=0;
#         v2h=b64.indexOf(v2o.charAt(i2))*64+b64.indexOf(v2o.charAt(i2+1))*1;
#         // ...
#     }
# }

def decode_snippet():
    B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    sdd = "#R1R3XEV3U6m+sq9o_"
    ln_n = 192
    notes = []
    
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
            else: v2p = 192
            v2t = 1
            v2b = math.ceil(v2v / v2p) + 1
            v2o = sdd[sft+1:sft+v2b]
            sft += v2b
        elif ch in "1234567":
            v2o = sdd[sft:sft+3]
            v2t = 2
            sft += 3
        elif ch == "8" or ch == "9":
            v2o = "1" + sdd[sft+2:sft+4] if ch == "9" else ""
            b64_val = B64.find(sdd[sft+1]) if sft+1 < len(sdd) else -1
            if b64_val != -1:
                for idx in range(6):
                    if b64_val & (1 << idx):
                        v2o += str(idx+2) + sdd[sft+2:sft+4]
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
            for char in v2o:
                if v2c == 0:
                    v2x = B64.find(char)
                    # Use string conversion properly. Math.floor(v2x/8) + "" + v2x%8
                    v2k += str(v2x // 8) + str(v2x % 8)
                elif v2c == 1:
                    v2x = B64.find(char)
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
                ob2_char = v2k[v2i]
                if ob2_char != "0" and ob2_char != "-":
                    # In JS: ob2=v2k.charAt(v2i)
                    # Actually JS code does: `objtab[i2] |= (1<<ob2);`
                    # Which implies `ob2` is parsed as integer automatically by JS bitwise operator
                    # `ob2` is a string "1" through "7". `1 << "4"` becomes `16`.
                    # What if ob2 is "m"? Wait, v2k is composed of `v2x//8` and `v2x%8`, so it's always "0"-"7".
                    key_val = 0 if v2c else int(ob2_char)
                    notes.append({'pos': i2, 'key': key_val, 'type': 'v2t!=2'})
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
                    ch1, ch2 = v2o[i2], v2o[i2+1]
                    v2h = B64.find(ch1) * 64 + B64.find(ch2)
                    
                    # Similar to JS: ob2 is `v2o.charAt(i2)`
                    # Wait!!
                    # If `ob2_char` is `m`, `1 << "m"` is 1 in JS !!
                    # But if it's "1"-"7", it's 2-128.
                    # Textage sometimes uses `1` or `2` or `7`, but does it use letters?
                    # Let's see what happens to `parseInt(ob2_char)`
                    try: key_val = 0 if v2c else int(ob2_char)
                    except ValueError: key_val = 8
                    
                    if key_val < 8:
                        notes.append({'pos': v2h, 'key': key_val, 'type': 'v2t==2'})
                    i2 += 2
                    
        if v2c == 2:
            break
            
    return notes

print(f"Decoded {len(decode_snippet())} notes in M4")
