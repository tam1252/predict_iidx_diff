import requests
import re

url = 'https://textage.cc/score/21/verflcht.html?1XC00'
r = requests.get(url)
r.encoding = r.apparent_encoding
html = r.text

script_m = re.search(r'<script type="text/javascript">\s*<!--\s*(.*?)//-->\s*</script>', html, re.DOTALL)
if script_m:
    text = script_m.group(1)
    idx = text.find('if(kuro)')
    if idx != -1:
        print("--- KURO BLOCK START ---")
        print(text[idx:idx+800])
