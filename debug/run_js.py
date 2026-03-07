import requests
import re
from py_mini_racer import MiniRacer

def main():
    url = "https://textage.cc/score/21/verflcht.html?1XC00"
    res = requests.get(url)
    res.encoding = 'shift_jis'
    html = res.text

    # Extract JS payload
    comment_start = html.find('<!--')
    func_hd_call = html.find('hd();')
    js_payload = html[comment_start + 4 : func_hd_call]

    with open("references/bars_function.txt", "r") as f:
        bars_js = f.read()

    js_code = """
    // Dummy environment
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
    var kuro = 0, a = 1, l = 1, k = 1, notes = 0, stat_pos = 0;
    
    // JS Payload from page definition
    var ln=[],sp=[],dp=[],tc=[],c1=[],c2=[],cn=[];
    var sc32=[],sc32base=[],sc32loop=[],ms=[],sd=[],hids=0,alls=0,sran=0,key=7,ky=7,conum=1;
    """ + js_payload + """

    sd = [null, sp, dp, [], []];
    cn = [null, c1, c2];
    var measure = sp.length - 1;

    // missing arrays emulation
    var obr = [[0,1,2,3,4,5,6,7], [0,1,2,3,4,5,6,7]];
    var dpalls = [[0,1,2,3,4,5,6,7], [0,1,2,3,4,5,6,7]];
    var b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    var cnc = [0, 0, 0];
    
    function set_co(h) {}
    function stat_insert() {}
    function dragOn() {}

    var debug_output = [];
    var my_count_hex = 0;
    var my_count_hash = 0;

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
    
    var total_ttl = ttl;
    var total_ttlcn = ttlcn;
    JSON.stringify({ttl: total_ttl, ttlcn: total_ttlcn, measures: true_notes_per_measure});
    """

    ctx = MiniRacer()
    try:
        res = ctx.eval(js_code)
        print("JS Eval returned:")
        print(res)
    except Exception as e:
        print("Error evaluating JS:", e)

if __name__ == "__main__":
    main()
