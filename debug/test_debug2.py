import sys
import os
sys.path.append(os.getcwd())
from src.scraper.textage_parser import decode_textage_sp
import re
import requests

url = "https://textage.cc/score/21/verflcht.html?1XC00"
html = requests.get(url).text
script_m = re.search(r'genre\s*=\s*.*?;(.*?)<', html, re.DOTALL)
if not script_m:
    script_m = re.search(r'<script type="text/javascript">\s*<!--\s*(.*?)//-->\s*</script>', html, re.DOTALL)
script_content = script_m.group(1) if script_m else ""

# ... we saw that script_content length was 12506 from the other script
