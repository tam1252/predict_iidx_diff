// bms2js header.js Version 3.02@Awai-Shichigatsu
//   0       1       2       3       4       5       6       7
b64="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
s=location.search,LNDEF=384,cob=["s","w","b","w","b","w","b","w"];
obr=[[0,1,2,3,4,5,6,7],[0,1,2,3,4,5,6,7]];kc=[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]];
dpalls=[[0,1,2,3,4,5,6,7],[0,7,6,5,4,3,2,1]];imgdir="../";diftype="";twstr="";memo="";
ln=[],sp=[],dp=[],tc=[],c1=[],c2=[],cn=[],sides=["",2,2],csd=["","left","right"];cnc=[0,0,0];
dw=[134,121],dr=[38,4],df=[134,119],ms=["",""," class=m1"," class=m2"];tm=new Date();hsa=8;
genre=title=artist=bpm=opt=lnse=lnhs="",key=ky=back=7,hs=gap=ty=k=1;cncnt=bsscnt=legacy=prt=pty=0;
soflan=level=notes=measure=a=l=m=g=db=p1o=hps=flp=off=lnln=lnst=lned=alls=hids=sran=kuro=sftkey=os=hcn=ttl=0;
sc32=[],sc32base=[],sc32loop=[];npos=[];nmergin=[];objres=[[0,0],[0,0],[0,0]];
lv=["☆？","★１","★２","★３","★４","★５","★６","★７","★８","★９",
	"★10","★11","★12","★７".fontcolor("red"),"★８".fontcolor("red")];
DEFNOTE="01234567";MIRNOTE="07654321";DEFHSA=8;
coad1=["_a/_dr3","_a/_dw2","_a/_db0","_a/_dw1","_a/_db3","_a/_dw2","_a/_db0","_a/_dw1"];
coad2=["_a/_dr1","_a/_dw3","_a/_db2","_a/_dw0","_a/_db1","_a/_dw3","_a/_db2","_a/_dw0"];
coap =["_a/_pr" ,"_a/_pw" ,"_a/_pb" ,"_a/_pw" ,"_a/_pb" ,"_a/_pw" ,"_a/_pb" ,"_a/_pw" ];
coar =["_a/_rr" ,"_a/_rw" ,"_a/_rb" ,"_a/_rw" ,"_a/_rb" ,"_a/_rw" ,"_a/_rb" ,"_a/_rw" ];
coaj1=["_a/_jr0","_a/_jw0","_a/_jb0","_a/_jw0","_a/_jb0","_a/_jw0","_a/_jb0","_a/_jw0"];
coaj2=["_a/_jr1","_a/_jw1","_a/_jb1","_a/_jw1","_a/_jb1","_a/_jw1","_a/_jb1","_a/_jw1"];
coaj3=["_a/_jr2","_a/_jw2","_a/_jb2","_a/_jw2","_a/_jb2","_a/_jw2","_a/_jb2","_a/_jw2"];
coat =["_a/_tr" ,"_a/_tw" ,"_a/_tb" ,"_a/_tw" ,"_a/_tb" ,"_a/_tw" ,"_a/_tb" ,"_a/_tw" ];
coam1=["_a/_mr3","_a/_mw2","_a/_mb0","_a/_mw1","_a/_mb3","_a/_mw2","_a/_mb0","_a/_mw1"];
coam2=["_a/_mr1","_a/_mw3","_a/_mb2","_a/_mw0","_a/_mb1","_a/_mw3","_a/_mb2","_a/_mw0"];
coax1=["_a/_dr3","_a/_pw" ,"_a/_rb" ,"_a/_jw0","_a/_jb1","_a/_jw2","_a/_tb" ,"_a/_mw1"];
coax2=["_a/_mr1","_a/_tw" ,"_a/_jb2","_a/_jw1","_a/_jb0","_a/_rw" ,"_a/_pb" ,"_a/_dw0"];
co = cob;
coy=-5;
conum=0;
document.onkeydown=scrl;
conlock=1;
nowd=new Date();
lockd=new Date(2013,3,1,12,0,0);
//if (nowd.getTime() > lockd.getTime()) conlock = 1;
for(i=0;i<=999;i++)nmergin[i]=0;

flag = false;
editmode = 0;
imgName = "";
window.document.onmousemove = dragImg;
window.document.onmouseup = dragOff;
y_old = 0;
function dragOn(n){
  if(!editmode) return;
  flag = true;
  imgName = n;
  y_old = event.y - parseInt(document.images[imgName].style.top);
 // alert(y_old);
}
function dragOff(){
  flag = false;
}
function dragImg(){
  if(!flag) return;
  if(!editmode) return;
 // 
  tmppx = document.images[imgName].style.top;
  document.images[imgName].style.top = event.y - y_old;
//  document.images[imgName].style.top = parseInt(tmppx) + event.y - y_old;
 // alert(event.y+"/"+y_old+"/"+document.images[imgName].style.top+"/"+(parseInt(document.images[imgName].style.top) + event.y - y_old));
  //y_old = event.y;
  return false;
}

function set_conum()
{
	if(conlock)return 0;
	var pathname = location.pathname;
	var sppos = pathname.lastIndexOf("/");
	var eppos = pathname.lastIndexOf(".");
	var tagname = pathname.substring(sppos+1, eppos);
	var tagval = a*7+l*4+k*1;
	for (tagi=0; tagi<tagname.length; tagi++) tagval += tagname.charCodeAt(tagi);
	return tagval % 10;
}

function set_co(coside)
{
	if(char1=="2")coside=2;
	if      (conum==1) {coy = -8; co = (coside==1) ? coad1 : coad2;}
	else if (conum==2) {coy = -6; co = coap;}
	else if (conum==3) {coy = -8; co = coar;}
	else if (conum==4) {coy =-11; co = coaj1;}
	else if (conum==5) {coy =-13; co = coaj2;}
	else if (conum==6) {coy =-13; co = coaj3;}
	else if (conum==7) {coy = -8; co = coat;}
	else if (conum==8) {coy =-11; co = (coside==1) ? coam1 : coam2;}
	else if (conum==9) {coy =-11; co = (coside==1) ? coax1 : coax2;}
}

stat_arr=[[[],[],[],[],[],[],[],[]],[[],[],[],[],[],[],[],[]],[[]]];
stat_list=[[],[]];
stat_on=stat_pos=0;
stat_tate=[0,0];stat_tril=[0,0];stat_doji=[0,0];stat_sara=[0,0];
stat_rand=[0,0];stat_kdan=[0,0];stat_cnbs=[0,0];
stat_restr="";
stat_plays=384000;
stat_playe=0;
stat_playt=0;


char1=s.charAt(1);
char2=s.charAt(2);
level=s.charAt(3)? s.charAt(3):0;
char2lower=char2.toLowerCase();
if(char2==char2lower){prt=1;imgdir="../prt/";}
char2=char2.toUpperCase();

if(char2=="X"){a=1;kuro=1;}
if(char2=="A")a=1;
if(char2=="L")l=1;
if(char2=="N"){l=1;hps=1;}
if(char2=="H")hps=1;
if(char2=="B"){l=1;g=1;}
if(char2=="G" || char2=="R"){l=1;hps=1;g=1;}
if(char2=="P"){l=1;hps=1;pty=1;g=1;}
if(char1=="1")sides[1]=1;
if(char1=="D"){k=0;key=14;}
if(char1=="L"){k=0;key=14;os=1;sides[1]=1;}
if(char1=="R"){k=0;key=14;os=2;}
if(char1=="F"){flp=1;k=0;key=14;}
if(char1=="M"){m=1;k=0;key=14;}
if(char1=="B"){db=1;key=14;}
//conum = set_conum();
c4tmp=parseInt(s.charAt(4),16);
d=(c4tmp&1)? 1:0;
hs=((c4tmp&6)+4)/4;
legacy=(c4tmp&8)? 1:0;
if(hs==2.5)hs=5/8;
dstr=(d&&conum==0)?"_":"";
lnln=s.charAt(5) ? parseInt(s.charAt(5),36):0;

exp="";
barnotes=0;
if(s.indexOf("+")>0) {
	exp=s.substr(s.indexOf("+"));
	s=s.substr(0,s.indexOf("+"));
	if(exp.indexOf("N")>0) barnotes=1;
}
if(s.indexOf("=")>0) {
	lnhs=s.substr(s.indexOf("="),3);
	hsa=eval(lnhs.substr(1,2));
	hs=hsa/DEFHSA;
}
if(s.indexOf("~")>0 && s.indexOf("~")<s.indexOf("-")){
	lnse=s.substring(s.indexOf("~"));
	lnst=eval(s.substring(s.indexOf("~")+1,s.indexOf("-")));
	lned=eval(s.substring(s.indexOf("-")+1));
	if(lnln=="0")lnln=4;
}

if(s.indexOf("0000000000000000")>=0){
	alls=1;
	sran=1;

}else if(s.indexOf("9999999999999999")>=0){
	sran=1;

}else if(s.indexOf("8888888888888888")>=0){
	hids=1;
	alls=1;
	sran=1;

}else if(s.length-lnse.length-lnhs.length==23){
	for(ri=0;ri<8;ri++){
		obr[0][ri]=8;
		obr[1][ri]=8;
	}
	for(ri=0;ri<8;ri++){
		if(s.charAt(ri+ 7)<8)obr[0][s.charAt(ri+ 7)]=ri;
		if(s.charAt(ri+15)<8)obr[1][s.charAt(ri+15)]=ri;
	}
}

document.write("<meta name='viewport' content='width=device-width,initial-scale=1.0,user-scalable=yes,maximum-scale=3.0' />"+
	"<style type=text/css><!-- div,span,div img{position:absolute;}"+
	" a.anchor{display:block; padding-top:100px; margin-top:-100px;}"+((m)?
	"img.m1{filter:Alpha(Style=1,Opacity=10,FinishOpacity=90,StartX=100,FinishX=0);}"+
	"img.m2{filter:Alpha(Style=1,Opacity=10,FinishOpacity=90);}":"")+
	"td,th{font-size:16px;"+((prt)? "}body{color:black;background:white;}"
	:"}body{color:white;background:black;}")
	+" --></style><meta name='description' content='beatmaniaIIDX 譜面集 for javascript/CSS'>");
	
if (location.href.indexOf("textage.cc")>=0) {
	document.write('<script async src="https://www.googletagmanager.com/gtag/js?id=G-T0NZ5HXFBD"></script>');
	document.write('<script>window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);}');
	document.write("gtag('js', new Date()); gtag('config', 'G-T0NZ5HXFBD');</script>");
}


function scrollToTop() {
  scrollTo(0, window.pageYOffset);
 }
function scrollToButtom() {
  scrollTo(document.documentElement.scrollWidth, window.pageYOffset);
 }


function encode_url()
{
	var pathname = location.pathname;
	var sppos = pathname.lastIndexOf("/");
	var eppos = pathname.lastIndexOf(".");
	var tagname = pathname.substring(sppos+1, eppos);
	window.open("../shorturl.html?"+tagname+","+s.substring(1),"","width=500,height=100,location=no");
}

function scrl(inkey){
	incode=(inkey)? inkey.keyCode : event.keyCode;
	scrl_body(incode);
}
function scrl_body(incode){
	//alert(incode);
	isrand = (s.charAt(6)=="R");
	mirold1 = isrand ? s.substring( 7,15) : DEFNOTE;
	mirold2 = isrand ? s.substring(15,23) : DEFNOTE;
	switch(incode){
		case 27:		// [ESC]
			editmode ^= 1;
			if (editmode) alert("editモードになります");
			else		  alert("editモードを解除します");
			break;
		case 16:	// [SHIFT]
			sftkey ^= 1;
			break;
		case 74:	// url copy [j]
			if (window.confirm("クリップボードにリンクをコピーします。")) {
				clipboardData.setData("Text", "<a href='"+location.href+"' target='_blank'>"+title+diftype+"</a>");
			}
			break;
		case  66:	// [b]ar clip
			rstr=prompt("BAR CLIP:(ex.25-32)","");
			barclip(rstr);
			break;
		case 72:	// [H]i-Speed
			hstr=prompt("Hi-Speed:2～50(default:"+DEFHSA+")",DEFHSA);
			rndjump(mirold1,mirold2,"h",hstr);
			break;
		case  70:	// [f]lip
			rndjump(mirold1,mirold2,"f");	break;
		case  79:	// [o]neside
			rndjump(mirold1,mirold2,"o");	break;
		case  80:	// [p]rint
			rndjump(mirold1,mirold2,"p");	break;
		case  81:	// all scratch [q]
			rndjump("00000000","00000000");	break;
		case  83:	// [s]-random
			rndjump("99999999","99999999");	break;
		case  68:	// [d]efault
			rndjump(DEFNOTE,DEFNOTE);		break;
		case  86:	// short url [v]
			encode_url();					break;
		case  76:	// [l]egacy
			if(cncnt||bsscnt) rndjump(mirold1,mirold2,"l");			break;
		case 48:case 49:case 50:case 51:case 52:case 53:case 54:case 55:case 56:case 57:
			rndjump(mirold1,mirold2,incode - (sftkey==1 ? 38:48));	break;
		case  77: case 87: case 188: case 69: case 190:	// 1P [m]irror [w] [<] [e] [>]
			mirmov = (incode==87||incode==188) ? 1 : 6;
			mirnew = mirold1.charAt(0);
			for(mi=0;mi<7;mi++)mirnew+=mirold1.charAt(1+(incode==77 ? 6-mi:mirmov+mi)%7);
			rndjump(mirnew,mirold2);
			break;
		case  73: case 89: case 219: case 85: case 221:	// 2P m[i]rror [y] [{] [u] [}]
			if (key!=14) break;
			mirmov = (incode==89||incode==219) ? 1 : 6;
			mirnew = mirold2.charAt(0);
			for(mi=0;mi<7;mi++)mirnew+=mirold2.charAt(1+(incode==73 ? 6-mi:mirmov+mi)%7);
			rndjump(mirold1,mirnew);
			break;
		case  82:	// [r]andom
			if(key==14){
				rstr=prompt("RANDOM:12345671234567→","12345671234567");
				rndjump("0"+rstr.substring(0,7),"0"+rstr.substring(7,14));
			}else{
				rstr=prompt("RANDOM:1234567→","1234567");
				rndjump("0"+rstr.substring(0,7),DEFNOTE);
			}
			break;
		case  65:	// [a]uto random
		case  97:	// dp left
		case  98:	// dp right
			rstr=["0","0"];
			for (ari=0; ari<2; ari++) {
				tmprnd=[1,2,3,4,5,6,7];
				for (ri=0; ri<7; ri++) {
					arpos=Math.floor(Math.random()*(7-ri))+ri;
					rstr[ari]+=tmprnd[arpos];
					tmprnd[arpos]=tmprnd[ri];
				}
			}
			if (incode==65){rndjump(rstr[0],rstr[1]);}
			if (incode==97){if(key!=14)break;if(mirold2=="99999999")mirold2="01234567";rndjump(rstr[0],mirold2);}
			if (incode==98){if(key!=14)break;if(mirold1=="99999999")mirold1="01234567";rndjump(mirold1,rstr[1]);}
			break;
		case 84:	// [t]weet
			if (location.href.indexOf("textage.cc")>=0) {
				window.open("http://twitter.com/intent/tweet?text="+
		 					encodeURIComponent(location.href+" "+twstr+" "), "_blank");
			}
			break;
		case  75:	// [k]ey info
			kcstr="",kcnum=0;kctmp=0;
			for(kcj=0; kcj<(key==7? 1:2); kcj++){
				kcstr+="["+(kcj+1)+"P]\n"
				for(kci=kcj; kci<8+kcj; kci++){
					if(kcj==1 && kci==8) kci=0;
					kcnum+=kc[kcj][kci];
					kcstr+=(kci ? kci:"S")+" ";
					kck=0;
					for (; kck<kc[kcj][kci]; kck++){
						kcstr+="l";
						kck+=9;
					}
					kcstr+="   "+kc[kcj][kci]+" ("+Math.round(kc[kcj][kci]/notes*10000)/100+"%)\n";
					if(kcj==1 && kci==0)break;
				}
			}
			kcstr+="\n[TOTAL] "+kcnum+" ("+Math.round(kcnum/notes*10000)/100+"%)";
			alert(kcstr);
			break;
        case 78:	// [N]otesIndex
			nstr=prompt("NotesIndex (1～"+notes+")","");
			notes_index(nstr);
			break;
		case 71:	// [g]raph
			if(lnse!="")break;
			if (stat_on==0) {
				stat_on = 1;
				if(bpm.indexOf("～")<0) stat_arr[2][0][0]=[0,eval(bpm)];
				else					stat_arr[2][0][0]=[0,120];
				b(1-gap,measure);
				stat_calc_time();
				stat_create_list();
				stat_result();
			}
			alert(stat_restr);
			break;
		case 88:	// [x]chord count
			cstr=prompt("同時押しパターン検索\r\n(ex.147, 147+, 147s, 147S, 1Sd)","");
			chord_count(cstr);
			break;
		default:
			break;
	}
}

function w(str){
	if(!off)document.write(str);
}


function hd(){
	w("<nobr>");
	if(!prt&&lnse==""){
		document.write('<a href="#end" style="color:yellow">></a> ');
	}
	opt=(k)?"[SP ":"[DP ";
	if  (kuro)opt+="LEGGENDARIA]";
	else if(a)opt+="ANOTHER]";
	else if(pty)opt+="BEGINNER]";
	else if(g)opt+="BEGINNER]";
	else if(l)opt+="NORMAL]";
	else      opt+="HYPER]";
	diftype=opt;
	if(k){diftype+=(char1=="1")?"(1P)":"(2P)"}

	opt+="<font color="+(prt?"black":"yellow")+">";
	if(db){notes*=2;opt+="+BATTLE";}
	if(flp)opt+="+FLIP";
	if(m){key=ky=7;opt+="+BUSTER'S";}
	if(legacy)opt+="+LEGACY";

	if(s.charAt(6)=="R"){
		if     (alls)opt+="+ALL-SCRATCH";
		else if(sran)opt+="+S-RANDOM";
		else if(key==7){
			if     (s.substring(7,15)==MIRNOTE)opt+="+MIRROR";
			else if(s.substring(7,15)!=DEFNOTE)opt+="+RANDOM("+s.substring( 8,15)+")";
		}else{
			if     (s.substring( 7,15)==MIRNOTE)opt+="+1P MIR";
			else if(s.substring( 7,15)!=DEFNOTE)opt+="+1P RAN("+s.substring( 8,15)+")";
			if     (s.substring(15,23)==MIRNOTE)opt+="+2P MIR";
			else if(s.substring(15,23)!=DEFNOTE)opt+="+2P RAN("+s.substring(16,23)+")";
		}
	}
	if(os==1)opt+=" (1P SIDE)";
	if(os==2)opt+=" (2P SIDE)";
	opt+="<\/font>";
	
	optcol=prt?"black":"orange";
	if(lnse!="")w("<b>"+title+"<\/b> "+opt.fontcolor(optcol)+
				  " bpm:"+bpm+" - "+lv[parseInt(level,16)]+"<\/nobr>");
	else w("\""+genre+"\""+opt.fontcolor(optcol)+" <b>"+title+"<\/b> / "+
		artist+" bpm:"+bpm+" - "+lv[parseInt(level,16)]+" Notes:"+notes+"<\/nobr>");

	twstr = title + " " + diftype;

	sd=[[],sp,dp];
	cn=[[],c1,c2];

	if(lnln!=0){
		if(ln[measure]==24)ln[measure]=LNDEF;
		premsr= (lnst>0) ? lnst-gap:1-gap;

		if(tc!=null){
			if(tc[premsr]==null || (tc[premsr]!=null && tc[premsr][0].charAt(3)!="0")){
				for(tcp=premsr-1; tcp>=0; tcp--){
					if(tc[tcp]!=null){
						tmptc = tc[tcp][tc[tcp].length-1].substring(0,3)+"0";
						if(!tc[premsr])tc[premsr]=[tmptc];
						else tc[premsr][tc[premsr].length]=tmptc;
						break;
					}
				}
			}
		}
		if(tc[premsr]==null && tc[premsr+1]!=null){
			tc[premsr]=tc[premsr+1];
			tc[premsr+1]=null;
		}else if(tc[premsr]==null && tc[premsr+1]==null && tc[premsr+2]!=null){
			tc[premsr]=tc[premsr+2];
			tc[premsr+2]=null;
		}
	}

	if(lnln==1){
		b(1-gap,measure);
		off=1;
	}else if(lnln!=0){
		dispmax=384*lnln/hs;
		mtmp=(lned>0)? lned-gap:measure;

		w("<table><tr>");
		for(li=premsr,dispnow=0; li<=mtmp; li++){
			lntmp=ln[li] ? ln[li]:LNDEF;
			if(dispnow!=0 && dispnow+lntmp>dispmax){
				w("<td valign=bottom>");
				b(premsr,li-1);
				w("<\/td>");
				premsr=li;
				dispnow=0;
			}
			if(li==mtmp){
				w("<td valign=bottom>");
				b(premsr,mtmp);
				w("<\/td>");
			}
			dispnow+=lntmp;
		}
		if(!prt&&lnse==""){
			document.write('<td><div style="position:absolute;top:8px;"><a href="#" style="position:relative;left:-20px;color:yellow"><</a><a id=end class=anchor></div></td>');
		}
		document.write("<\/tr><\/table>")
		off=1;
	}
}

function npos_sort(a,b){
	return a - b;
}


function ft(){
	sc=kc[0][0]+kc[1][0];
	if(!off){
		if(!prt&&lnse==""){
			document.write('<td><div style="position:absolute;top:8px;"><a href="#" style="position:relative;left:-20px;color:yellow"><</a><a id=end class=anchor></div></td>');
		}
		document.write("<\/tr><\/table>");
	}
	tmpURL = document.URL;
	tmpURL = tmpURL.replace(/\\/g,"/");
	tmpURL.match(/\/score\/([0-9sx]{1,2})\//);
	tmpVer = RegExp.$1;

	if(lnse.length==0){
		document.write("<font size=-1>MAX:"+Math.ceil(notes*18/9)+
		", MAX-:"+Math.ceil(notes*17/9)+", AAA:"+Math.ceil(notes*16/9)+" (SCR="+sc);
		//document.write("<font size=-1>AAA:"+Math.ceil(notes*16/9)+
		//", AA:"+Math.ceil(notes*14/9)+", A:"+Math.ceil(notes*12/9)+" (SCR="+sc);
		if(hcn){
			if(cncnt) document.write(" <font color=red>HCN<\/font>="+cncnt);
			if(bsscnt)document.write(" <font color=red>HBSS<\/font>="+bsscnt);
		}else{
			if(cncnt) document.write(" CN="+cncnt);
			if(bsscnt)document.write(" BSS="+bsscnt);
		}
		if(os)document.write(") ("+p1o+")");
		else document.write(")"+(!k&&!m ? " ("+p1o+" / "+(notes-p1o)+")":"")+"<\/font>");

		npos.sort(npos_sort);
		//document.write(npos);
	}

	pathname = location.pathname;
	htmlname = pathname.substring(pathname.lastIndexOf("/")+1);
	tagname  = htmlname.substring(0, htmlname.indexOf("."));
	document.write("<img src='../log/log.php?tag="+tagname+"' width=0 height=0>");

	str="";
	str+=" <input type=button value='[D]efault'    onclick='scrl_body(68);'>";
	str+=" <input type=button value='[H]i-Speed'   onclick='scrl_body(72);'>";
	if (k) {
		str+=" <input type=button value='[M]IRROR' onclick='scrl_body(77);'>";
		str+=" <input type=button value='R-RAN [W,&lt;]' onclick='scrl_body(188);'>";
		str+=" <input type=button value='R-RAN [E,&gt;]' onclick='scrl_body(190);'>";
		str+=" <input type=button value='[R]ANDOM'     onclick='scrl_body(82);'>";
		str+=" <input type=button value='[A]UTO-RAN'   onclick='scrl_body(65);'>";
		str+=" <input type=button value='[S]-RAN'      onclick='scrl_body(83);'>";
	} else {
		str+=" <input type=button value='1P [M]IR' onclick='scrl_body(77);'>";
		str+=" <input type=button value='W,&lt;'   onclick='scrl_body(188);'>";
		str+=" <input type=button value='E,&gt;'   onclick='scrl_body(190);'>";
		str+=" <input type=button value='2P M[I]R' onclick='scrl_body(73);'>";
		str+=" <input type=button value='Y,{'      onclick='scrl_body(219);'>";
		str+=" <input type=button value='U,}'      onclick='scrl_body(221);'>";
		str+=" <input type=button value='[R]ANDOM'     onclick='scrl_body(82);'>";
		str+=" <input type=button value='[A]UTO-RAN'   onclick='scrl_body(65);'>";
		str+=" <input type=button value='A-RAN(L) [n1]'   onclick='scrl_body(97);'>";
		str+=" <input type=button value='A-RAN(R) [n2]'   onclick='scrl_body(98);'>";
		str+=" <input type=button value='[S]-RAN'      onclick='scrl_body(83);'>";
	}
	str+=" <input type=button value='[F]LIP'       onclick='scrl_body(70);'>";
	str+=" <input type=button value='[B]arClip'    onclick='scrl_body(66);'>";
	if(lnse=="")str+=" <input type=button value='[K]eyInfo'    onclick='scrl_body(75);'>";
	if(lnse=="")str+=" <input type=button value='[N]otesIndex' onclick='scrl_body(78);'>";
	if(lnse=="")str+=" <input type=button value='[X]ChordCount' onclick='scrl_body(88);'>";
	if(lnse=="")str+=" <input type=button value='[G]raph' onclick='scrl_body(71);'>";
	if (location.href.indexOf("textage.cc")>=0) {
	str+=" <input type=button value='[T]weet'      onclick='scrl_body(84);'>";
	}

	document.write(str);
//+(new Date()-tm);

	/* 広告判定 */
	var url = "textage.cc" + location.pathname;
	if (   location.href.indexOf(url)>=0			/* ローカルでない */
		&& prt == 0									/* 印刷でない */
		&& (document.referrer).indexOf(url) < 0) {	/* １つ前が同一ページでない */
		
		var str="";
		var pgwid = document.documentElement.scrollWidth;
		var clhei = document.documentElement.clientHeight;
		var adstr = '<ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-2065219587369012" data-ad-slot="3542337728"></ins>';
		if (clhei > 800) {
			adstr = '<ins class="adsbygoogle" style="display:inline-block;width:336px;height:280px" data-ad-client="ca-pub-2065219587369012" data-ad-slot="3215920117"></ins>';
		}
			
		if (pgwid > 750) {
			str='<br>　<br><div style="position:absolute; left:10px;"><span style="font-size:8pt">スポンサーリンク</span><br>';
			str+='<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2065219587369012" crossorigin="anonymous"></script>';
			str+=adstr;
			str+='<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>';
			str+='</div>';
		}
		
		if (pgwid > 2750) {
			str+='<div style="position:absolute; left:'+(pgwid-750)+'px;"><span style="font-size:8pt">　</span><br>';
			str+='<ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-2065219587369012" data-ad-slot="3542337728"></ins>';
			str+='<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>';
			str+='</div>';
		}
		if (pgwid > 4750) {
			str+='<div style="position:absolute; left:'+(Math.floor(pgwid/2)-375)+'px;"><span style="font-size:8pt">　</span><br>';
			str+='<ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-2065219587369012" data-ad-slot="3542337728"></ins>';
			str+='<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>';
			str+='</div>';
		}
		if (pgwid > 750) {
			document.write(str);
		}
		
		
		//str='<p>　<p><span style="font-size:8pt">スポンサーリンク</span><br>';
		//str+='<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2065219587369012" crossorigin="anonymous"></script>';
		//str+='<ins class="adsbygoogle" style="display:block" data-ad-format="autorelaxed"';
		//str+='data-ad-client="ca-pub-2065219587369012" data-ad-slot="4230461807"></ins>';
		//str+='<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>';
		//document.write(str);
	}
	vertbl=["Consumer only","1st style","2nd style","3rd style","4th style",
		"5th style","6th style","7th style","8th style","9th style","10th style",
		"IIDX RED","HAPPY SKY","DistorteD","GOLD","DJ TROOPERS","EMPRESS",
		"SIRIUS","Resort Anthem","Lincle","tricoro","SPADA","PENDUAL",
		"copula","SINOBUZ","CANNON BALLERS","Rootage","HEROIC VERSE",
		"BISTROVER","CastHour","RESIDENT"];
		verstr=(tmpVer=="s") ? "substream" : vertbl[tmpVer];
		
	str="Version:"+verstr+" / Artist:"+artist+" / ScoreType:"+diftype+" / bpm:"+bpm+" / Notes:"+notes;

	document.title += " - beatmaniaIIDX 譜面集 for javascript/CSS"
	document.querySelector('meta[name="description"]').setAttribute("content", str);
}

function im(hy){
	if(!off)document.write("<img width=1 height="+(hy*hs)+">");
}

function barclip(rstr){
	if(rstr==0){bcst=1;bced=measure+gap;}
	else if(rstr.indexOf("-")!=rstr.lastIndexOf("-"))return;
	else{
		bcst=new Number(rstr.substring(0,rstr.indexOf("-")));
		bced=new Number(rstr.substring(rstr.indexOf("-")+1));
	//	if(bced>measure+gap)bced=measure+gap;
		if(bcst<1)bcst=bced;
		if(isNaN(bcst) || isNaN(bced) || bcst>bced)return;
	}
	stmp=(s.indexOf("~")>0)? s.substring(0,s.indexOf("~")):s;
	if(stmp.charAt(5)=="0")stmp=stmp.substring(0,5)+"4"+stmp.substring(6);
	if(bcst==1 && bced==measure+gap)
		location.replace(stmp.substring(0,5)+"0"+stmp.substring(6)+exp);
	else location.replace(stmp+"~"+bcst+"-"+bced+exp);
	return;
}

function notes_index(idx){
	if (!(1 <= idx && idx <= notes)) {
		return;
	}
	posnum = npos[Math.floor(idx)-1];
	mesnum = Math.floor(posnum / 10000000);
	vernum = Math.floor((posnum % 10000000)/100);
	//if (vernum >= ln[mesnum]/3) vernum = hs*ln[mesnum]/3 - 1;
	beatnum = Math.floor(1 + (vernum / 32 / hs));
	
	alert(""+Math.floor(idx)+"番目のノーツは、"+mesnum+"小節目 "+beatnum+"拍目");
}

function chord_count(cstr){
	if (cstr.length==0) return;
	npos.sort(npos_sort);
	c_ret = 0;
	c_bit = 0;	// 同時押しbit
	c_biz = 0;	// 同時押しbit
	c_ork = 0;	// ＋鍵盤
	c_ors = 0;	// ＋スクラッチ
	c_sym = 0;	// DP対称
	c_str = "";
	
	if (cstr.indexOf("S") >= 0) {c_bit |= (1<<0); c_biz |= (1<<0); c_str+="S"};
	if (cstr.indexOf("1") >= 0) {c_bit |= (1<<1); c_biz |= (1<<7); c_str+="1"}
	if (cstr.indexOf("2") >= 0) {c_bit |= (1<<2); c_biz |= (1<<6); c_str+="2"}
	if (cstr.indexOf("3") >= 0) {c_bit |= (1<<3); c_biz |= (1<<5); c_str+="3"}
	if (cstr.indexOf("4") >= 0) {c_bit |= (1<<4); c_biz |= (1<<4); c_str+="4"}
	if (cstr.indexOf("5") >= 0) {c_bit |= (1<<5); c_biz |= (1<<3); c_str+="5"}
	if (cstr.indexOf("6") >= 0) {c_bit |= (1<<6); c_biz |= (1<<2); c_str+="6"}
	if (cstr.indexOf("7") >= 0) {c_bit |= (1<<7); c_biz |= (1<<1); c_str+="7"}
	if (cstr.indexOf("+") >= 0) {c_ork = 1; c_str+="を含む";}
	if (cstr.indexOf("s") >= 0) {c_ors = 1; c_str+="(Sの有無は問わず)";}
	if (cstr.indexOf("d") >= 0) {c_sym = 1; c_str+="(DP右側はMIRROR)";}
	
	c_now = 0;
	c_pos = 0;
	for (c_i=0; c_i<npos.length; c_i++) {
		c_pos = Math.floor(npos[c_i]/10);
		sidnum = Math.floor((npos[c_i] % 100) / 10);
		c_now |= (1 << npos[c_i] % 10);
		
		if (c_i == npos.length-1 || c_pos != Math.floor(npos[c_i+1]/10)) {
			c_chk =  (c_sym && sidnum==2) ? c_biz : c_bit;
			
			if (c_ork) {
				if (!c_ors && ((c_chk & 1)==0) && ((c_now & 1)!=0)) {}
				else if ((c_now & c_chk) == c_chk) c_ret++;
				else if (c_ors && (c_now & (c_chk |= 1)) == (c_chk |= 1)) c_ret++;
			} else {
				if (c_now == c_chk) c_ret++;
				else if (c_ors && (c_now == (c_chk |= 1))) c_ret++;
			}
			c_now = 0;
		}
	}
	
	alert(c_str + "同時押しの数 : " + c_ret);
}
	
function rndjump(rstr1,rstr2,rndopt,rndval){
	c4cnvtab="0123456789ABCDEFGHIJ";
	md=s.charAt(1);
	stp=s.charAt(2);
	ldisp=c4cnvtab.charAt(lnln);
	rndhs=hsa;
	
	if(rndopt=="p"){
		if (prt) stp=stp.toUpperCase();
		else	 stp=stp.toLowerCase();
	}else if(rndopt=="h"){
		if(rndval.length<=0||rndval.length>2)return;
		rndhs=eval(rndval);
		if (rndhs<2||rndhs>50)return;
	}else if(rndopt=="l"){
		if (c4tmp>=8) c4tmp-=8;
		else		  c4tmp+=8;
	}else if(rndopt=="o"){
		switch(md){
			case "D":md="L";break;
			case "L":md="R";break;
			case "R":md="D";break;
			default:return;
		}
	}else if(rndopt=="f"){
		switch(md){
			case "1":md="2";break;
			case "2":md="1";break;
			case "D":md="F";break;
			case "F":md="D";break;
			default:return;
		}
	}else if(rndopt==0){
		ldisp=0;
	}else if(rndopt){
		ldisp=c4cnvtab.charAt(rndopt);
	}
	c4cnv = c4cnvtab.charAt(c4tmp);
	rephd = "?"+md+stp+s.substring(3,4)+c4cnv+ldisp;
	hsastr= (rndhs==DEFHSA) ? "":"="+(rndhs<10 ? "0":"")+rndhs;

	if(rstr1==DEFNOTE && rstr2==DEFNOTE){
		location.replace(rephd+hsastr+(ldisp==1 ?"":lnse)+exp);return;}
	if(rstr1=="00000000" || rstr1=="99999999" || rstr1=="88888888"){
		location.replace(rephd+"R"+rstr1+rstr1+hsastr+(ldisp==1 ?"":lnse)+exp);
		return;}

	for(ri=0;ri<8;ri++)
		if(rstr1.indexOf(""+ri)<0 ||
		   rstr2.indexOf(""+ri)<0){alert("入力が正しくありません。");return;}
	location.replace(rephd+"R"+rstr1+rstr2+hsastr+(ldisp==1 ?"":lnse)+exp);
}

function cn_sort(a,b)
{
	alen = (a[2]==undefined) ? 30 : a[2];
	blen = (b[2]==undefined) ? 30 : b[2];
	aend = a[1] + alen;
	bend = b[1] + blen;
	if (aend == bend) return alen - blen;
	return aend - bend;
	
/*
	if(a[3]==1||a[3]==0) return 1;
	if(b[3]==1||b[3]==0) return -1;
	alen = (a[2]==undefined) ? 30 : a[2];
	blen = (b[2]==undefined) ? 30 : b[2];
	return alen - blen;
*/
}

function bars_(n,mn){
	if(off&&!stat_on)return;
	o="";
	if(s.charAt(5)!="0" && n==-1)n=999;
	else if(n<0 || n>measure)return;
	if(!ln[n])ln[n]=LNDEF;
	nbar=Math.ceil(ln[n]/3);
	if(nbar<4)nbar=4;
	if(hs>1)mn=void(0);
	else if(sc32[n]>=0)mn=sc32[n];
	mnbase=sc32base[n];
	if(sc32base[n]==undefined)mnbase=8;
	mnloop=sc32loop[n];
	if(sc32loop[n]==undefined)mnloop=mnbase;
	ttlstart=ttl;
	ttlcn=0;

	if(db){sd[2]=sp;cn[2]=c1;}
	if(os==2||flp){sd[0][n]=sd[1][n];
			sd[1][n]=sd[2][n];
			sd[2][n]=sd[0][n];
			cn[0][n]=cn[1][n];
			cn[1][n]=cn[2][n];
			cn[2][n]=cn[0][n];}
	o+="<table cellpadding=0 cellspacing=0 width="+(ty*dw[d]+dr[d]-4)+
		" style='border:1px "+(prt? "black":"white")+" solid' height="+(nbar*hs)+"><tr>";
	for(h=1;h<=2;h++){
		set_co(h);
		objtab=[];
		if (objres[h][0]==n) {
			if (objres[h][1]){
				for(ori=0;ori<=9;ori++)	objtab[ln[n]-ori]=objres[h][1];
			}
		}
		objres[h]=[n-1,0];
		if(h==2){
			if(d==0)o+="<\/div><\/td><th width=32 bgcolor="+
				(prt ? "white style='border-left:1px black solid;"+
				(ty==2 ? "border-right:1px black solid;padding:0px'" : "'")
				:"gray")+"><a id='mes"+n+"'>"+((nbar*hs>=32) ? (n==999 ? 1:n+gap)+"<\/a><\/th>":
				"<img width=1 height=1><\/th>");
			if(ty==1)break;
			if(d==1)o+="<\/div><\/td><td width=2 bgcolor="+(prt ? "black":"white")+"><\/td>";
		}
		o+="<td width="+df[d]+" valign=top style='background-image:url(\""+
			imgdir+(hsa==DEFHSA ? (hs==5/8 ? 5 : back-4+4*hs) : 1)+d+".gif\");"+
			"background-position:"+((2-sides[h])*(23-7*d))+"px "+
			(nbar*hs-1)+"px'><div style='width:"+df[d]+"px;height:"+(nbar*hs)+"px'>";
		if(hsa!=DEFHSA){
			for(nbari=1; ;nbari++){
				nbarh=Math.ceil(nbari*hsa*(back==6 ? 2/3:1));
				if(nbarh >= nbar*hs) break;
				o+="<img src="+imgdir+(nbarh%(hsa*4)==0 ? "x1":"x2")+
					".gif height=1 width="+df[d]+" style='top:"+(nbarh-2)+"px;'>";
			}
		}
		if(d && ty-h<1 && nbar*hs>=32){
			o+="<span id='mes"+n+"' style='bottom:0px;"+(barnotes ? "z-index:5;":"")+
			csd[sides[h]]+":0px;color:gray;font:16px impact'>"+(n==999 ? 1:n+gap)+"<\/span>";
		}
		if(tc[n]&&h==1){
			for (tci=tc[n].length-1; tci>=0; tci--){
				cb=tc[n][tci];
				tp=nbar-cb.substring(3)-2;
				stat_insert(2, 0, stat_pos + eval(cb.substring(3))*3, cb.substring(0,3));
				o+="<img src="+imgdir+"t.gif height=2 width="+((d)?dw[d]*ty-2:dw[d])+
					" style='top:"+((tp+2)*hs-2)+"px'>";
				if(!barnotes){
					o+="<span style='z-index:5;font-size:10px;top:"+((tp+2)*hs-7-d*4)+
						"px;font-weight:bold;width:20px;text-align:center;"+
						((!d) ? "background:"+(prt?"white":"gray")+";left:14":csd[sides[1]]+":")+
						"0px;color:"+(prt ? "black":"palegreen")+";'>"+cb.substring(0,3)+"<\/span>";
				}
				if(!d && ty==2){
					o+="<img src="+imgdir+"t.gif height=2 width=134 style='top:"+((tp+2)*hs-2)+"px;left:166px'>";
				}
			}
		}

		for(mm=0; mm<=m; mm++){
			sdd=sd[h+mm][n];
			if(!sdd)sdd="00";//continue;
			sh=sides[h];
			msc=ms[m*2+mm];
			sft=div=0;


		if(cn[h][n]) {
			cn[h][n].sort(cn_sort);
			//document.write(""+n+":"+cn[h][n]);
			for(cni=cn[h][n].length-1; cni>=0; cni--){
				cnz = cn[h][n][cni][0];
				cnp = Math.floor(cn[h][n][cni][1]*hs);
				cnhtmp = cn[h][n][cni][2];
				if (cnhtmp == undefined) cnhtmp=30;
				cnh = Math.floor(cnhtmp*hs);
				cnf = cn[h][n][cni][3];
				if (cnf == undefined) cnf = 3;
				if (!cn[h][n][cni][h+3]) cn[h][n][cni][h+3] = [];
				cnsrd = cn[h][n][cni][h+3][n];
				
				for (cnj=0; cnj<(cnz<10 ? 1:2); cnj++) {
					tmpjpos = (cnj==0) ? cnz%10 : Math.floor(cnz/10);
					jpos = obr[h-1][tmpjpos];
					if (hids && tmpjpos==0) continue;
					if (jpos==8) continue;

					if(sran){
						if(cnsrd) {
							jpos = cnsrd;
						}else if(jpos) {
							cnorig = jpos;
							cn[h][n][cni][h+3][n] = cnorig;
							
							if(alls&&key==14){
								for (dpalli=1; dpalli<8; dpalli++) {
									jpos=dpalls[h-1][dpalli];
									if (!(   (objtab[cnp*3]&(1<<jpos))
										  || (objtab[(cnp+cnh+2)*3]&(1<<jpos)))) break;
								}
							} else {
								srancnt=0;
								do {
									if(++srancnt>=10000){
										alert("S-RAN生成失敗により強制終了");
										break;
									}
									jpos = Math.floor(Math.random()*7)+1;
								} while(   (objtab[cnp*3]&(1<<jpos))
										|| (objtab[(cnp+cnh+2)*3]&(1<<jpos)));
							}
							if(!(cnf&1)){
								cnend = 0;
								for(cnmes=n-1; ; cnmes--) {
									for (cnnow=cn[h][cnmes].length-1; cnnow>=0; cnnow--) {
										cnpos = cn[h][cnmes][cnnow];
										if (cnpos[0]==cnorig) {
											if (!cnpos[h+3])cnpos[h+3] = [];
											cnpos[h+3][cnmes] = jpos;
											if (cnpos[3]&1) cnend = 1;
											break;
										}
									}
									if (cnend==1) break;
								}
							}
							if(!(cnf&2)){
								cnend = 0;
								for(cnmes=n+1; ; cnmes++) {
									for (cnnow=0; cnnow<cn[h][cnmes].length; cnnow++) {
										cnpos = cn[h][cnmes][cnnow];
										if (cnpos[0]==cnorig) {
											if (!cnpos[h+3])cnpos[h+3] = [];
											cnpos[h+3][cnmes] = jpos;
											if (cnpos[3]&2) cnend = 1;
											break;
										}
									}
									if (cnend==1) break;
								}
							}
						}
						for(cno=cnp*3;cno<=(cnp+cnh+2)*3;cno++){
							if (!objtab[cno])objtab[cno]=0;
							objtab[cno]|=(1<<jpos);
							//memo=objtab[cno];
						}
					}
					if(!legacy) {
						// obj!
						stat_insert(h-1, jpos, stat_pos + cnp*3, cnh*3);
						objstr=imgdir+(!prt&&hcn ? "h":"l")+cob[jpos]+dstr;
						o+="<img src="+objstr+".gif"+msc+" style='top:"+
							(nbar*hs-cnp-cnh-1)+"px;left:"+
							(jpos? jpos*(14-d)-sh*(37-d*8)+61-d*15:(sh-1)*(98-d*7)+2)+
							"px;height:"+cnh+"px;width:"+(jpos ? 11-d : 32-d*8)+"px'>";
					}
					if (cnf&1) {
						if (jpos) cncnt++;
						else	  bsscnt++;
						cnc[h]++;
						// obj!
						ttlcn++;
						if(legacy)stat_insert(h-1, jpos, stat_pos + cnp*3, 0);
						mss = (!legacy && cnf&4) ? "m":"";
						objstr=imgdir+(!legacy&&!prt&&hcn ? "hh":"")+co[jpos]+mss+dstr
						o+="<img src="+objstr+".gif"+msc+" style='top:"+
							(nbar*hs-cnp+coy)+"px;left:"+
							(jpos? jpos*(14-d)-sh*(37-d*8)+60-d*15:(sh-1)*(98-d*7))+"px;'>";
						if(stat_on==0){if(h==1)p1o++;kc[h-1][jpos]++;npos.push((n+gap)*10000000+(cnp+nmergin[n+gap])*100+(h*10+jpos));}
					}
					if (cnf&2 && !legacy) {
						// obj!
						ttlcn++;
						mss = (!legacy && cnf&4) ? "m":"";
						objstr=imgdir+(!prt&&hcn ? "hh":"")+co[jpos]+mss+dstr;
						o+="<img src="+objstr+".gif"+msc+" style='top:"+
							(nbar*hs-cnp-cnh+coy)+"px;left:"+
							(jpos? jpos*(14-d)-sh*(37-d*8)+60-d*15:(sh-1)*(98-d*7))+"px;'>";
						if(stat_on==0){if(h==1)p1o++;kc[h-1][jpos]++;npos.push((n+gap)*10000000+(cnp+cnh+nmergin[n+gap]-1)*100+(h*10+9));}
					}
				}
			}
		}

if(sdd.charAt(0)=="#"){
	sft++;
	v2c=0;
	while(sft<sdd.length){
		v2o="";
		v2v=(v2c? 1:3)*ln[n]/6;
		switch(sdd.charAt(sft)){
			case "C":v2s= 0;v2p=192;v2t=0;if(!v2c)v2o=sdd.charAt(++sft);sft++;break;
			case "c":v2s=96;v2p=192;v2t=0;if(!v2c)v2o=sdd.charAt(++sft);sft++;break;
			case "R":v2s= 0;v2p= 96;v2t=0;if(!v2c)v2o=sdd.charAt(++sft);sft++;break;
			case "r":v2s=48;v2p= 96;v2t=0;if(!v2c)v2o=sdd.charAt(++sft);sft++;break;
			case "P":v2s= 0;v2p= 48;v2t=0;if(!v2c)v2o=sdd.charAt(++sft);sft++;break;
			case "p":v2s=24;v2p= 48;v2t=0;if(!v2c)v2o=sdd.charAt(++sft);sft++;break;

			case "B":v2s= 0;v2p=192;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "b":v2s=96;v2p=192;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "Q":v2s= 0;v2p= 96;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "q":v2s=48;v2p= 96;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "O":v2s= 0;v2p= 48;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "o":v2s=24;v2p= 48;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "X":v2s= 0;v2p= 24;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "x":v2s=12;v2p= 24;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "Z":v2s= 0;v2p= 12;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
                                                                                               
			case "S":v2s= 0;v2p= 64;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "s":v2s=32;v2p= 64;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "T":v2s= 0;v2p= 32;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "t":v2s=16;v2p= 32;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;
			case "U":v2s= 0;v2p= 16;v2t=1;v2b=Math.ceil(v2v/v2p)+1;v2o=sdd.substring(sft+1,sft+v2b);sft+=v2b;break;

			case "1":case "2":case "3":case "4":case "5":case "6":case "7":
				v2o=sdd.substring(sft,sft+3);v2t=2;sft+=3;break;
			case "9":v2o="1"+sdd.substring(sft+2,sft+4);
			case "8":for(i2=0;i2<6;i2++){
						if(b64.indexOf(sdd.charAt(sft+1))&(1<<i2))v2o+=(i2+2)+sdd.substring(sft+2,sft+4);
					}v2t=2;sft+=4;break;

			case "-":v2c=1;sft++;break;
			case "_":v2o=(sft==sdd.length-1)? "AA":sdd.substring(sft+1);v2c=v2t=2;break;

			default:w("<font color=red>error<\/font>");return;
		}
		if(sdd.charAt(sft-1)=="-")continue;

		v2k="";
		if(v2t==1){
			for(i2=0;i2<v2o.length;i2++){
				if(v2c==0){
					v2x=b64.indexOf(v2o.charAt(i2));
					v2k+=Math.floor(v2x/8)+""+v2x%8;
				}else if(v2c==1){
					v2x=b64.indexOf(v2o.charAt(i2));
					for(i3=5;i3>=0;i3--)v2k+=(v2x>>i3)&1 ? 1:0;
				}
			}
		}else if(v2t==0){
			for(i2=v2s;i2<ln[n];i2+=v2p)v2k+=(v2c ? "1":v2o);
		}
		if(v2t!=2){
			for(v2i=0,i2=v2s;i2<ln[n];v2i++,i2+=v2p){
				if(hids && v2c)continue;
				if((ob2=v2k.charAt(v2i))!=0){
					if(alls&&key==14){
						for (dpalli=0; dpalli<8; dpalli++) {
							ob2=dpalls[h-1][dpalli];
							if (!(objtab[i2] & (1<<ob2))) break;
						}
					}else if(v2c&&!alls){
						ob2=0;
						if(conum==0)co[0]=((Math.floor(i2/6/mnbase)%mnloop)==mn)? "r":"s";
					}else if(sran) {
						if     (alls) ob2=0;
						else if (ob2) ob2=Math.floor(Math.random()*7)+1;
						srancnt=0;
						while(objtab[i2] & (1<<ob2)) {
							if(++srancnt>=10000){
								alert("S-RAN生成失敗により強制終了");
								break;
							}
							ob2=Math.floor(Math.random()*7)+1;
						}
					}
					if(h==1 && stat_on==0)p1o++;
					objtab[i2] |= (1<<ob2);
					jpos=obr[h-1][ob2];
					if(jpos==8)continue;
					if(stat_on==0){kc[h-1][jpos]++;npos.push((n+gap)*10000000+(Math.floor(i2*hs/3)+nmergin[n+gap])*100+(h*10+jpos));}
					// obj!
					stat_insert(h-1, ob2, stat_pos + i2, 0);
					objstr=imgdir+co[jpos]+dstr;
					ttl++;
					o+="<img src="+objstr+".gif"+msc+" name=ttl"+ttl+
						" onMousedown=dragOn('ttl"+ttl+"') style='top:"+
						(nbar*hs-Math.floor(i2*hs/3)+coy)+"px;left:"+
						(ob2 ? jpos*(14-d)-sh*(37-d*8)+60-d*15
						:(sh-1)*(98-d*7))+"px'>";
				}
			}
		}else{
			for(i2=0;i2<v2o.length;i2+=2){

				if(v2c==0){ob2=v2o.charAt(i2);i2++;}else ob2=0;
				if(hids && ob2==0)continue;
				v2h=b64.indexOf(v2o.charAt(i2))*64+b64.indexOf(v2o.charAt(i2+1))*1;
				if(alls&&key==14){
					for (dpalli=0; dpalli<8; dpalli++) {
						ob2=dpalls[h-1][dpalli];
						if (!(objtab[v2h] & (1<<ob2))) break;
					}
				}else if(mn!=void(0)&&!alls){
					if(conum==0)co[0]=((Math.floor(v2h/6/mnbase)%mnloop)==mn)? "r":"s";
				}else if(sran) {
					if     (alls) ob2=0;
					else if (ob2) ob2=Math.floor(Math.random()*7)+1;
					srancnt=0;
					while(objtab[v2h] & (1<<ob2)){
						if(++srancnt>=10000){
							alert("S-RAN生成失敗により強制終了");
							break;
						}
						ob2=Math.floor(Math.random()*7)+1;
					}
				}
				if(h==1 && stat_on==0)p1o++;
				objtab[v2h] |= (1<<ob2);
				jpos=obr[h-1][ob2];
				if(jpos==8)continue;
				if(stat_on==0){kc[h-1][jpos]++;npos.push((n+gap)*10000000+(Math.floor(v2h*hs/3)+nmergin[n+gap])*100+(h*10+jpos));}
				// obj!
				stat_insert(h-1, ob2, stat_pos + v2h, 0);
				objstr=imgdir+co[jpos]+dstr;
				ttl++;
				o+="<img src="+objstr+".gif"+msc+" name=ttl"+ttl+
					" onMousedown=dragOn('ttl"+ttl+"')  style='top:"+
					(nbar*hs-Math.floor(v2h*hs/3)+coy)+"px;left:"+
					(ob2 ? jpos*(14-d)-sh*(37-d*8)+60-d*15
					:(sh-1)*(98-d*7))+"px'>";
			}
		}
		if(v2c==2)break;
	}
}else{
	if(sdd.charAt(0)=="x"){
		len=parseInt(sdd.substring(1,4),16);
		sft=4;
	}else len=sdd.length;
	for(;sft<sdd.length;sft+=2,div+=2){
		while(sdd.charAt(sft)=="@"){
			div+=parseInt(sd[h+mm][n].substring(sft+1,sft+3),16)*2;
			sft+=3;
		}
		if(mn!=void(0)&&conum==0)co[0]=((Math.floor(nbar*div/(len*2*mnbase))%mnloop)==mn)?"r":"s";
		y=parseInt(sdd.substring(sft,sft+2),16);
		for(j=0;j<=ky;j++){
			if(y>>j==0)break;
			if(hids && j==0)continue;
			if(y>>j&1){
				if(h==1 && stat_on==0)p1o++;
				jpos = obr[h-1][j];
				if(jpos==8)continue;
				if(alls&&key==14){
					for (dpalli=0; dpalli<8; dpalli++) {
						jpos=dpalls[h-1][dpalli];
						if (!(objtab[Math.floor(nbar*div*3/len)] & (1<<jpos))) break;
					}
				}else if (sran) {
					if      (alls) jpos=0;
					else if (jpos) jpos=Math.floor(Math.random()*7)+1;
					srancnt=0;
					while(objtab[Math.floor(nbar*div*3/len)] & (1<<jpos)) {
						if(++srancnt>=10000){
							alert("S-RAN生成失敗により強制終了");
							break;
						}
						jpos=Math.floor(Math.random()*7)+1;
					}
				}
				if(stat_on==0){kc[h-1][jpos]++;npos.push((n+gap)*10000000+(Math.floor(nbar*div*hs/len)+nmergin[n+gap])*100+(h*10+jpos));}
				objtab[Math.floor(nbar*div*3/len)] |= (1<<jpos);
				// obj!
				stat_insert(h-1, jpos, stat_pos + nbar*div*3/len, 0);
				objstr=imgdir+co[jpos]+dstr;
				ttl++;
				o+="<img src="+objstr+".gif"+msc+" name=ttl"+ttl+
					" onMousedown=dragOn('ttl"+ttl+"') style='top:"+
					(nbar*hs-Math.floor(nbar*div*hs/len)+coy)+"px;left:"+
					(jpos? jpos*(14-d)-sh*(37-d*8)+60-d*15:(sh-1)*(98-d*7))+"px'>";
			}
		}
	}
}
		}
		objres[h][1]=objtab[0];
		//document.write(objres[h]);
	}
	if(d || ty==2)o+="<\/div><\/td>";
	if(stat_on==0)document.write(o+"<\/tr><\/table>");
	else          stat_pos += ln[n];
	if(conum==0)co[0]="s";

	nmergin[n+gap]+=nbar*hs;
	
	if(stat_on==0 && (nbar*hs>=32) && barnotes) {
		document.getElementById("mes"+n).innerHTML="<font color=yellow>"+(ttl-ttlstart+ttlcn)+"<\/font>";
	}
}

function b(st,en){
	if(off&&!stat_on)return;
	if(os==0&&key==14){ty=2;sides[1]=m+1;sides[2]=2;}
	if(st==null){st=0;en=measure;}
	if(en==null)en=st;
	if(stat_on){for(bb=st;bb<=en;bb++)bars_(bb);}
	else       {for(bb=en;bb>=st;bb--)bars_(bb);}
}

function stat_insert(s_side, s_key, s_num, s_len)
{
	if(stat_on==0)return;
	sdata=[s_num, s_len];
	spos=stat_arr[s_side][s_key];
	if(spos.length==0)spos[0]=sdata;
	else {
		for (si=spos.length-1; si>=0; si--) {
			if (spos[si][0] == s_num) {
				spos[si] = sdata;
				break;
			}
			if (spos[si][0] < s_num) {
				if(s_side<2 && spos[si][0]+spos[si][1]==s_num)spos[si][1]+=s_len;
				else spos.splice(si+1, 0, sdata);
				break;
			}
			if (si==0) spos.splice(0, 0, sdata);
		}
	}
}

function stat_calc_time()
{
	snow=stat_arr[2][0];
	snow[0][2] = 0;
	snow_pos=[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]];
	snow[snow.length] = [384000, 1];

	for (sn=1; sn<snow.length; sn++) {
		snow[sn][2] = snow[sn-1][2]+(5*(snow[sn][0]-snow[sn-1][0]))/(8 * snow[sn-1][1]);

		for (sh=0; sh<2; sh++) {
			for (so=0; so<8; so++) {
				snoy=stat_arr[sh][so];
				for (sy=snow_pos[sh][so]; sy<snoy.length; sy++) {
					if (snoy[sy][0] >= snow[sn][0]) break;
					snoy[sy][2] = snow[sn-1][2]+(5*(snoy[sy][0]-snow[sn-1][0]))/(8*snow[sn-1][1]);
					snoy[sy][3] = (5*snoy[sy][1])/(8*snow[sn-1][1]);
					snoy[sy][4] = snow[sn-1][1];
					snow_pos[sh][so]++;
				}
			}
		}
	}
}

function stat_create_list()
{
	for (sh=0; sh<2; sh++) {
		stat_list[sh][0]={'key':-1,'time':-1, 'wide':0,'bpm':1,'prev':null,'next':1};
		stat_list[sh][1]={'key':-1,'time':999,'wide':0,'bpm':1,'prev':0,   'next':null};

		for (so=0; so<8; so++) {
			snow = stat_arr[sh][so];
			slpos = stat_list[sh][0].next;
			for (sn=0; sn<snow.length; sn++) {
				while(stat_list[sh][slpos].time <= snow[sn][2]){
					slpos = stat_list[sh][slpos].next;
				}
				inpos = stat_list[sh].length;
				prpos = stat_list[sh][slpos].prev;
				stat_list[sh][inpos] = {'key':so, 'time':snow[sn][2], 'wide':snow[sn][3],
										'bpm':snow[sn][4], 'prev':prpos, 'next':slpos};
				stat_list[sh][slpos].prev = inpos;
				stat_list[sh][prpos].next = inpos;
				slpos = inpos;
				if (stat_plays > snow[sn][2]) stat_plays = snow[sn][2];
				if (stat_playe < snow[sn][2] + snow[sn][3]) stat_playe = snow[sn][2] + snow[sn][3];
			}
		}
	}
	stat_playt = stat_playe - stat_plays;
}

// トリル
function stat_check_tril()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key == 0) continue;
			if (ck_dat.tate && ck_dat.doji) continue;

			for (var ck_key=1; ck_key<=7; ck_key++) {
				if (ck_key == ck_dat.key) continue;
				var ck_search = stat_search_ahead(sh, ck_key, slpos, stat_calc_diff(ck_dat.bpm));
				if (ck_search) {
					var ck_depth = stat_check_tril_depth(1, sh, ck_search, ck_dat.key);
					if (ck_depth >= 3) {
						if (!ck_dat.tril)ck_dat.tril = 3;
					}
				}
			}
		}
	}
}
function stat_check_tril_depth(ck_depth, ck_sh, ck_base, ck_key)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff(ck_dat.bpm));
	if (ck_search) {
		ck_depth = stat_check_tril_depth(ck_depth+1, ck_sh, ck_search, ck_dat.key);
	}
	if (ck_depth >= 3) ck_dat.tril = 0.5 + ck_depth*0.125;
	return ck_depth;
}

// 階段
function stat_check_kdan()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key == 0) continue;
			if (ck_dat.tate && ck_dat.doji) continue;

			if (ck_dat.key >= 3) {
				for (var ck_key=ck_dat.key-1; ck_key>1; ck_key--) {
					var ck_search = stat_search_ahead(sh, ck_key, slpos, stat_calc_diff(ck_dat.bpm));
					if (ck_search) {
						var ck_depth = stat_check_kdan_depth_left(1, sh, ck_search);
						if (ck_depth >= 2) {
							ck_dat.kdan = 1;
						}
						break;
					}
				}
			}
			if (ck_dat.key <= 5) {
				for (var ck_key=ck_dat.key+1; ck_key<7; ck_key++) {
					var ck_search = stat_search_ahead(sh, ck_key, slpos, stat_calc_diff(ck_dat.bpm));
					if (ck_search) {
						var ck_depth = stat_check_kdan_depth_right(1, sh, ck_search);
						if (ck_depth >= 2) {
							ck_dat.kdan = 1;
						}
						break;
					}
				}
			}
		}
	}
}
function stat_check_kdan_depth_left(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	for (var ck_key=ck_dat.key-1; ck_key>=1; ck_key--) {
		var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff(ck_dat.bpm));
		if (ck_search) {
			ck_depth = stat_check_kdan_depth_left(ck_depth+1, ck_sh, ck_search);
			break;
		}
	}
	if (ck_depth >= 2) ck_dat.kdan = 0.75;
	return ck_depth;
}
function stat_check_kdan_depth_right(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	for (var ck_key=ck_dat.key+1; ck_key<=7; ck_key++) {
		var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff(ck_dat.bpm));
		if (ck_search) {
			ck_depth = stat_check_kdan_depth_right(ck_depth+1, ck_sh, ck_search);
			break;
		}
	}
	if (ck_depth >= 2) ck_dat.kdan = 0.75;
	return ck_depth;
}

// 縦連打
function stat_check_tate()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key == 0) continue;
			if (ck_dat.tate) continue;

			var ck_search = stat_search_ahead(sh, ck_dat.key, slpos, stat_calc_diff(ck_dat.bpm));
			if (ck_search) {
				var ck_depth = stat_check_tate_depth(1, sh, ck_search, ck_dat.key);
				if (ck_depth >= 1) {
					ck_dat.tate = 2 + (ck_depth+1)/2;
				}
			}
		}
	}
}
function stat_check_tate_depth(ck_depth, ck_sh, ck_base, ck_key)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff(ck_dat.bpm));
	if (ck_search) {
		ck_depth = stat_check_tate_depth(ck_depth+1, ck_sh, ck_search, ck_dat.key);
	}
	if (ck_depth >= 1) ck_dat.tate = (ck_depth+1)/2;
	return ck_depth;
}

// 縦連打サブ
function stat_check_tsub()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key == 0) continue;
			if (ck_dat.tate) continue;

			var ck_search = stat_search_ahead(sh, ck_dat.key, slpos, stat_calc_diff_t(ck_dat.bpm));
			if (ck_search) {
				var ck_depth = stat_check_tsub_depth(1, sh, ck_search, ck_dat.key);
				if (ck_depth >= 1) {
					ck_dat.tsub = 1 + (ck_depth+1)/4;
				}
			}
		}
	}
}
function stat_check_tsub_depth(ck_depth, ck_sh, ck_base, ck_key)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff_t(ck_dat.bpm));
	if (ck_search) {
		ck_depth = stat_check_tsub_depth(ck_depth+1, ck_sh, ck_search, ck_dat.key);
	}
	if (ck_depth >= 1) ck_dat.tsub = (ck_depth+1)/4;
	return ck_depth;
}

// 乱打
function stat_check_rand()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key == 0) continue;
			if (ck_dat.tril) continue;

			if (ck_dat.key >= 2) {
				for (var ck_key=ck_dat.key-1; ck_key>=1; ck_key--) {
					var ck_search = stat_search_ahead(sh, ck_key, slpos, stat_calc_diff(ck_dat.bpm));
					if (ck_search) {
						var ck_depth = stat_check_rand_depth_right(1, sh, ck_search);
						if (ck_depth >= 2) {
							ck_dat.rand = 1;
						}
						break;
					}
				}
			}
			if (ck_dat.key <= 6) {
				for (var ck_key=ck_dat.key+1; ck_key<=7; ck_key++) {
					var ck_search = stat_search_ahead(sh, ck_key, slpos, stat_calc_diff(ck_dat.bpm));
					if (ck_search) {
						var ck_depth = stat_check_rand_depth_left(1, sh, ck_search);
						if (ck_depth >= 2) {
							ck_dat.rand = 1;
						}
						break;
					}
				}
			}
		}
	}
}
function stat_check_rand_depth_left(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	for (var ck_key=ck_dat.key-1; ck_key>=1; ck_key--) {
		var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff(ck_dat.bpm));
		if (ck_search) {
			ck_depth = stat_check_rand_depth_right(ck_depth+1, ck_sh, ck_search);
			break;
		}
	}
	if (ck_depth >= 2) ck_dat.rand = 0.75;
	return ck_depth;
}
function stat_check_rand_depth_right(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	for (var ck_key=ck_dat.key+1; ck_key<=7; ck_key++) {
		var ck_search = stat_search_ahead(ck_sh, ck_key, ck_base, stat_calc_diff(ck_dat.bpm));
		if (ck_search) {
			ck_depth = stat_check_rand_depth_left(ck_depth+1, ck_sh, ck_search);
			break;
		}
	}
	if (ck_depth >= 2) ck_dat.rand = 0.75;
	return ck_depth;
}





// 同時
function stat_check_doji()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key == 0) continue;
			if (ck_dat.doji) continue;

			if (stat_list[sh][ck_dat.next].time == ck_dat.time) {
				var ck_depth = stat_check_doji_depth(1, sh, ck_dat.next);
				if (ck_depth >= 1) {
					ck_dat.doji = 0.5;
					ck_dat.dsub = ck_depth;
				}
			}
		}
	}
}
function stat_check_doji_depth(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	if (stat_list[ck_sh][ck_dat.next].time == ck_dat.time) {
		ck_depth = stat_check_doji_depth(ck_depth+1, ck_sh, ck_dat.next);
	}
	if (ck_depth >= 1) {
		ck_dat.doji = 0.5*ck_depth;
		ck_dat.dsub = ck_depth;
	}
	return ck_depth;
}

// 皿
function stat_check_sara()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key != 0) continue;
			if (ck_dat.sara) continue;

			var ck_search = stat_search_ahead(sh, 0, slpos, stat_calc_diff(ck_dat.bpm));
			if (ck_search) {
				var ck_depth = stat_check_sara_depth(1, sh, ck_search);
				if (ck_depth >= 1) {
					ck_dat.sara = 2 + (ck_depth+1)/2;
					ck_dat.sdep = ck_depth;
				}
			} else {
				ck_dat.sara = 0.75;
			}
		}
	}
}
function stat_check_sara_depth(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	var ck_search = stat_search_ahead(ck_sh, 0, ck_base, stat_calc_diff(ck_dat.bpm));
	if (ck_search) {
		ck_depth = stat_check_sara_depth(ck_depth+1, ck_sh, ck_search);
	}
	if (ck_depth >= 1) {
		ck_dat.sara = (ck_depth+1)/4;
		ck_dat.sdep = ck_depth;
	}
	return ck_depth;
}

// 皿サブ
function stat_check_ssub()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.key != 0) continue;
			if (ck_dat.sdep) continue;

			var ck_search = stat_search_ahead(sh, 0, slpos, 1.6*stat_calc_diff_t(ck_dat.bpm));
			if (ck_search) {
				var ck_depth = stat_check_ssub_depth(1, sh, ck_search);
				if (ck_depth >= 1) {
					ck_dat.ssub = 0.5;
				}
			}
		}
	}
}
function stat_check_ssub_depth(ck_depth, ck_sh, ck_base)
{
	var ck_dat = stat_list[ck_sh][ck_base];
	var ck_search = stat_search_ahead(ck_sh, 0, ck_base, 1.6*stat_calc_diff_t(ck_dat.bpm));
	if (ck_search) {
		ck_depth = stat_check_ssub_depth(ck_depth+1, ck_sh, ck_search);
	}
	if (ck_depth >= 1) ck_dat.ssub = 0.5;
	return ck_depth;
}

// ＣＮ
function stat_check_cnbs()
{
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var ck_dat = stat_list[sh][slpos];
			if (ck_dat.wide) ck_dat.cnbs = (ck_dat.wide+0.3)/stat_playt;
		}
	}
}

function stat_search_ahead(s_side, s_key, s_base, s_width)
{
	s_basetime = stat_list[s_side][s_base].time;
	s_base = stat_list[s_side][s_base].next;
	while (stat_list[s_side][s_base].time <= s_basetime + s_width) {
		if (   stat_list[s_side][s_base].key == s_key
			&& stat_list[s_side][s_base].time > s_basetime) return s_base;
		s_base = stat_list[s_side][s_base].next;
	}
	return 0;
}

function stat_calc_diff(bpm)
{
	STAT_DIF=0.2;
	if (bpm>180) return STAT_DIF-0.08;
	if (bpm>100) return STAT_DIF-(bpm-100)*0.001;
	return STAT_DIF;
}
function stat_calc_diff_t(bpm)
{
	STAT_DIF=0.28;
	if (bpm>180) return STAT_DIF-0.08;
	if (bpm>100) return STAT_DIF-(bpm-100)*0.001;
	return STAT_DIF;
}
function stat_result()
{
	stat_check_doji();
	stat_check_tate();
	stat_check_tril();
	stat_check_kdan();
	stat_check_rand();
	stat_check_sara();
	stat_check_ssub();
	stat_check_cnbs();
	stat_check_tsub();

	sco=["red","gray","blue","gray","blue","gray","blue","gray"];
	o="";
	oa="";
	snow=stat_arr[2][0];
	for (var sn=0; sn<snow.length-1; sn++) {
		o+="<span style='position:absolute; left:"+(snow[sn][2]*50)+
			"px; top:0px;width:2px;height:180px;background-color:green;'>"+
			snow[sn][1]+"<\/span>";
	}
	for (var sh=0; sh<2; sh++) {
		for (var slpos=stat_list[sh][0].next; slpos!=1; slpos=stat_list[sh][slpos].next) {
			var dbkey = stat_list[sh][slpos];
			var color = sco[dbkey.key];
			if (0) {}
			else if (dbkey.tate){stat_tate[sh]+=dbkey.tate; color="limegreen";}
			else if (dbkey.kdan && dbkey.rand) {
				stat_kdan[sh]+=dbkey.kdan*3/4;stat_rand[sh]+=dbkey.rand*1/4;color="black";
			}
			else if (dbkey.kdan){stat_kdan[sh]+=dbkey.kdan; color="purple";}
			else if (dbkey.rand){stat_rand[sh]+=dbkey.rand; color="lightblue";}
			else if (dbkey.tsub&&dbkey.dsub<2){stat_tate[sh]+=dbkey.tsub; color="darkgreen";}
			else if (dbkey.doji){stat_doji[sh]+=dbkey.doji; color="magenta";}

			if (dbkey.tril){stat_tril[sh]+=dbkey.tril; color="orange";}
			if (dbkey.sara){stat_sara[sh]+=dbkey.sara;}
			if (dbkey.ssub&&!dbkey.sdep){stat_sara[sh]+=dbkey.ssub; color="darkred";}
			if (dbkey.cnbs){stat_cnbs[sh]+=dbkey.cnbs;}

			o+="<span style='position:absolute; left:"+(dbkey.time*50)+"px; top:"+
				(dbkey.key*10+sh*90)+"px;width:"+(dbkey.wide ? dbkey.wide*50 : 3)+
				"px;height:8px;font-size:0px;background-color:"+color+";'><\/span>";
		}

		oattl=0;
		oaitab=[stat_rand[sh], stat_doji[sh], stat_kdan[sh], stat_tril[sh],
				stat_tate[sh], stat_sara[sh], stat_cnbs[sh]];
		oaistr=["乱打","同時","階段","トリ","縦連","　皿","ＣＮ"];
		oanotes = (sh==0) ? p1o : notes-p1o;
		is_2p = (notes-p1o > 0);
		if (oanotes > 0) {
			oa+= (sh==0) ? "1P\n" : "2P\n";
			for (oai=0; oai<oaistr.length; oai++) {
				oabmb = (oanotes>800) ? (oanotes-800)/2+800 : oanotes;
				if(is_2p) oabmb = (oanotes>500) ? (oanotes-500)/2+500 : oanotes;
				oatmp0 = Math.ceil(1000 * oaitab[oai]/oabmb)/10;
				if (oai==6) oatmp0 = Math.ceil(1000 * oaitab[oai])/10;
				oatmp = Math.ceil(oatmp0/5);
				oachr = oaistr[oai] +" ";
				oabar = 0;
				oattl += oatmp0;
				for (oabar; oabar<oatmp; oabar++) {
					if (oabar>=20) {
						oachr += "...";
						break;
					}
					oachr += "■";
				}
				for (oabar; oabar<10; oabar++) {
					oachr += "□";
				}
				oa+= oachr + " "+oatmp0+" pt\n";
			}
//			oa+= "合計 "+(Math.round(1000 * oattl/100)/10)+" pt\n";
		}
	}
	oa+="\nPLAYTIME : "+Math.floor(stat_playt*100)/100+" sec";
	stat_restr = oa;

	o+="<p>　<p>　<p>　<p>　<p>　<p>　<p>　<p>";
	o+="[kdan:"+stat_kdan[0]+","+stat_kdan[1]+"]";
	o+="[tril:"+stat_tril[0]+","+stat_tril[1]+"]";
	o+="[tate:"+stat_tate[0]+","+stat_tate[1]+"]";
	o+="[doji:"+stat_doji[0]+","+stat_doji[1]+"]";
	o+="[rand:"+stat_rand[0]+","+stat_rand[1]+"]";
	o+="[sara:"+stat_sara[0]+","+stat_sara[1]+"]";
	o+="[cnbs:"+stat_cnbs[0]+","+stat_cnbs[1]+"]";

//	document.write(o);
}

