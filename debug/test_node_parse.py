import sys
import os
import requests
import subprocess
import re

url = "https://textage.cc/score/21/verflcht.html?1XC00"
res = requests.get(url)
res.encoding = res.apparent_encoding
html = res.text

# Extract the script definition
comment_start = html.find('<!--')
comment_end = html.rfind('//-->')
func_hd_call = html.find('hd();')

if comment_start > 0 and func_hd_call > 0 and func_hd_call < comment_end:
    text_notes = html[comment_start + 4 : func_hd_call]
else:
    print("Failed to find boundaries")
    sys.exit(1)

js_part1 = """
let ln=[],sp=[],dp=[],tc=[],c1=[],c2=[],cn=[];
let genre="",title="",artist="",bpm="",opt="",lnse="",lnhs="";
let key=7,ky=7,back=7,hs=1,gap=1,ty=1,k=1;
let cncnt=0,bsscnt=0,legacy=0,prt=0,pty=0;
let soflan=0,level=0,notes=0,measure=0,a=0,l=0,m=0,g=0,db=0,p1o=0,hps=0,flp=0,off=0,lnln=0,lnst=0,lned=0,alls=0,hids=0,sran=0,kuro=0,sftkey=0,os=0,hcn=0,ttl=0;
let LNDEF=384;
let def=0; // Sometimes used
"""

js_part2 = """
const OUTPUT_ARRAYS = {'sp': sp, 'dp': dp, 'c1': c1, 'c2': c2};
for (const ARRAY_NAME in OUTPUT_ARRAYS) {
    let ARRAY = OUTPUT_ARRAYS[ARRAY_NAME];
    if (ARRAY) {
        for (let ix = 0; ix < ARRAY.length; ix++) {
            let DATA = ARRAY[ix];
            if (DATA === undefined || DATA === null) continue;
            let DATALINE = '';
            if (Array.isArray(DATA)) {
                DATALINE += '[';
                for (let jx = 0; jx < DATA.length; jx++) {
                    if (jx > 0) DATALINE += ', ';
                    let element = DATA[jx];
                    if (Array.isArray(element)) {
                         DATALINE += '[' + element.toString() + ']';
                    } else {
                         DATALINE += element;
                    }
                }
                DATALINE += ']';
            } else {
                DATALINE = DATA;
            }
            if(DATALINE !== "00" && DATALINE !== "") {
                console.log(ARRAY_NAME + "\\t" + ix + "\\t" + DATALINE);
            }
        }
    }
}
"""

full_js = js_part1 + "\n" + text_notes + "\n" + js_part2

# Run via node
p = subprocess.Popen(['node', '-e', full_js], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = p.communicate()
if p.returncode != 0:
    print("Node JS Error:")
    print(stderr)
else:
    print("Node JS OK. Output lines:", len(stdout.splitlines()))
    lines = stdout.splitlines()
    for l in lines[:10]:
        print(l)
    print("...")
    for l in lines[-10:]:
        print(l)
