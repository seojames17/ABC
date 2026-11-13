"""1203호 1화 전체 렌더링 (멀티컷 + 효과음 + 자막).

작업 폴더: cut/<컷>.png, sfx/*.wav (../tools/make_sfx.sh), fonts/ (Black Han Sans, Noto Sans KR),
내레이션 mp3는 A 경로. 컷 전환 시점은 내레이션 단어 타이밍(faster-whisper) 기준으로 잡았다.
"""
import subprocess
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920; BHS="fonts/BlackHanSans.ttf"
def noto(s):
    f=ImageFont.truetype("fonts/NotoSansKR.ttf",s)
    try: f.set_variation_by_name("Bold")
    except Exception: pass
    return f
def bhs(s): return ImageFont.truetype(BHS,s)
A="/home/user/ep1_ko/aud"
NARR=[(1,0.3),(2,5.2),(3,8.5),(4,13.0),(5,21.8),(6,29.4),(7,41.1),(8,48.3),(9,51.8),(10,61.9)]
TOTAL=68.2
# (컷, 시작, 끝, 줌) — 4a는 10번 컷 재사용(정지)
CUTS=[("01",0,1.24,"in"),("02",1.24,1.78,"in"),("03",1.78,2.78,"shake"),("04",2.78,5.2,"out"),
 ("05",5.2,7.08,"in"),("06",7.08,8.5,"in"),("07",8.5,9.5,"out"),("08",9.5,10.64,"in"),("09",10.64,11.56,"in"),("10",11.56,13.0,"push"),
 ("10",13.0,13.86,"none"),("41",13.86,17.26,"in"),("42",17.26,19.28,"out"),("43",19.28,21.8,"in"),
 ("51",21.8,22.84,"in"),("52",22.84,25.6,"in"),("53",25.6,27.06,"out"),("54",27.06,29.4,"in"),
 ("61",29.4,31.76,"in"),("62",31.76,33.8,"in"),("63",33.8,35.22,"shake"),("64",35.22,38.38,"out"),("65",38.38,41.1,"in"),
 ("71",41.1,43.02,"in"),("72",43.02,45.26,"in"),("73",45.26,46.46,"in"),("74",46.46,48.3,"push"),
 ("81",48.3,50.2,"out"),("82",50.2,51.8,"in"),
 ("91",51.8,54.4,"in"),("92",54.4,56.86,"in"),("93",56.86,61.9,"none"),
 ("100",61.9,64.26,"out"),("101",64.26,TOTAL,"in")]
# (시작, 끝, 자막, 배터리, 강조 문구, 특수 그리기)
SUBS=[(0,2.78,"밤 9시. 전기가 나갔습니다.",None,None,None),(2.78,5.2,"그리고… 다시는 들어오지 않았습니다.",None,None,None),
 (5.2,7.08,"민수는 생각했죠.",62,None,None),(7.08,8.5,"\"곧 들어오겠지.\"",62,None,None),
 (8.5,10.64,"심심해서 맥주나 마시려고",62,None,None),(10.64,13.0,"냉장고를 열었는데—",62,None,None),
 (13.0,13.86,"잠깐!",62,None,"stop"),
 (13.86,17.26,"냉장고는 문을 닫아 두면 네 시간 정도 차갑게 버팁니다.",62,["냉장실 약 4시간"],None),
 (17.26,19.28,"꽉 찬 냉동실은 이틀 가까이요.",62,["냉동실(가득) 약 48시간"],None),
 (19.28,21.8,"문을 열 때마다 그 시간이 줄어들어요.",62,["열수록 줄어요!"],None),
 (21.8,25.6,"그때 옆집 할머니는 욕조에 물을 받고 계셨어요.",62,None,None),(25.6,27.06,"민수는 웃었죠.",62,None,None),
 (27.06,29.4,"\"에이, 수돗물이 왜 끊겨요.\"",62,None,None),
 (29.4,31.76,"다음 날 아침.",41,None,None),(31.76,35.22,"수도꼭지에서 물이 졸졸… 멈췄습니다.",41,None,None),
 (35.22,38.38,"많은 고층 아파트는 전기 펌프로 물을 끌어올려요.",41,["전기 = 물"],None),
 (38.38,41.1,"펌프가 멈추면 물도 멈춥니다.",41,["전기 = 물"],None),
 (41.1,45.26,"편의점에 갔더니 카드 단말기가 꺼져 있었어요.",41,None,None),
 (45.26,46.46,"\"현금만 돼요.\"",41,None,"cash"),(46.46,48.3,"민수 지갑엔… 0원.",41,None,None),
 (48.3,50.2,"민수의 1일차 생존 점수는…",21,None,None),(50.2,51.8,"30점.",21,None,"score"),
 (51.8,54.4,"남은 배터리 21%.",21,None,None),(54.4,56.86,"당신이라면 어디에 쓰겠어요?",21,None,None),
 (56.86,59.06,"A, 가족에게 연락.",21,None,"ab"),(59.06,61.9,"B, 밤에 쓸 손전등.",21,None,"ab"),
 (61.9,64.26,"다음 화, DAY 3.",None,None,None),(64.26,TOTAL,"마트 앞에 줄이 생기기 시작합니다.",None,["NEXT: DAY 3"],None)]
SFX=[("hum",1.0),("thunk",1.78),("click",5.35),("whoosh",9.45),("creak",10.7),("sting",11.56),
 ("stop",13.0),("click",13.9),("whoosh",19.3),
 ("creak",21.85),("whoosh",27.1),
 ("chirp",29.5),("drip",32.9),("thunk",33.8),("hum",35.3),("error",38.4),
 ("chime",41.2),("error",43.1),("sad",46.5),
 ("ding",50.2),("lowbat",51.9),("whoosh",56.86),("pop",59.06),("sting",61.9),("whoosh",64.26)]

def wrap(d,t,f,mw):
    ws,ls,c=t.split(" "),[],""
    for w in ws:
        s=(c+" "+w).strip()
        if d.textlength(s,font=f)<=mw: c=s
        else:
            if c: ls.append(c)
            c=w
    if c: ls.append(c)
    return ls

def overlay(text,batt,key,sp):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((40,60,440,160),20,fill=(0,0,0,220))
    d.text((240,110),"1203호 | DAY 1",font=bhs(54),fill="white",anchor="mm")
    if batt:
        x0,y0=760,75; col=(220,40,40) if batt<=25 else (255,190,0) if batt<=45 else (60,200,90)
        d.rounded_rectangle((x0-20,60,1040,160),20,fill=(0,0,0,220))
        d.rectangle((x0,y0+10,x0+110,y0+60),outline="white",width=5)
        d.rectangle((x0+110,y0+25,x0+120,y0+45),fill="white")
        d.rectangle((x0+8,y0+18,x0+8+int(94*batt/100),y0+52),fill=col)
        d.text((x0+140,110),f"{batt}%",font=bhs(56),fill="white",anchor="lm")
    if key:
        y=300
        for k in key:
            d.text((W//2,y),k,font=bhs(84),fill=(255,230,0),anchor="mm",stroke_width=9,stroke_fill="black"); y+=105
    # 좌표는 이 화의 그림(종이 쪽지, 점수판, 2분할 패널) 위치에 맞춘 값
    if sp=="stop":
        d.text((W//2,760),"잠깐!",font=bhs(260),fill=(230,40,40),anchor="mm",stroke_width=14,stroke_fill="white")
    if sp=="cash":
        d.text((825,1110),"현금만",font=bhs(70),fill="black",anchor="mm")
    if sp=="score":
        d.text((540,580),"30",font=bhs(280),fill=(220,40,40),anchor="mm")
        d.text((540,760),"/ 100",font=bhs(80),fill="black",anchor="mm")
    if sp=="ab":
        d.text((270,250),"A",font=bhs(200),fill="white",anchor="mm",stroke_width=10,stroke_fill="black")
        d.text((810,250),"B",font=bhs(200),fill="white",anchor="mm",stroke_width=10,stroke_fill="black")
        d.rounded_rectangle((190,1300,890,1410),24,fill=(0,0,0,210))
        d.text((W//2,1355),"댓글로 A or B!",font=bhs(76),fill=(255,230,0),anchor="mm")
    f=noto(62); ls=wrap(d,text,f,960); y=1600-(len(ls)-1)*45
    for l in ls:
        d.text((W//2,y),l,font=f,fill="white",anchor="mm",stroke_width=8,stroke_fill="black"); y+=90
    return im

with open("ov.txt","w") as fh:
    for i,(a,b,t,bat,key,sp) in enumerate(SUBS):
        overlay(t,bat,key,sp).save(f"ov{i:02d}.png"); fh.write(f"file 'ov{i:02d}.png'\nduration {b-a:.3f}\n")
    fh.write(f"file 'ov{len(SUBS)-1:02d}.png'\n")

# 컷별 영상: 누적 프레임으로 길이를 잡아 반올림 오차가 쌓이지 않게 한다
segs=[]; frames_acc=0
for i,(name,a,b,mode) in enumerate(CUTS):
    end_frames=round(b*30); n=max(1,end_frames-frames_acc); frames_acc=end_frames
    z={"in":"'min(1+0.0012*on,1.08)'","out":"'max(1.08-0.0012*on,1.0)'","push":"'min(1+0.004*on,1.25)'"}.get(mode,"1.0")
    shake=",crop=1080:1920:'(in_w-1080)/2+8*sin(n*2.1)':'(in_h-1920)/2+8*cos(n*1.7)',scale=1080:1920" if mode=="shake" else ""
    vf=(f"scale=1620:2895,crop=1620:2880,zoompan=z={z}:d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1100x1956:fps=30,"
        f"crop=1080:1920{shake},setsar=1,format=yuv420p")
    out=f"seg{i:02d}.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"cut/{name}.png","-vf",vf,"-frames:v",str(n),"-r","30",
        "-c:v","libx264","-preset","veryfast","-crf","19",out],check=True)
    segs.append(out)
open("segs.txt","w").write("".join(f"file '{s}'\n" for s in segs))
subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","segs.txt","-c","copy","base.mp4"],check=True)

inputs=[]; filt=[]; idx=0
for k,t in NARR:
    inputs+=["-i",f"{A}/{k}.mp3"]; ms=int(t*1000)
    filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{idx}]"); idx+=1
for s,t in SFX:
    inputs+=["-i",f"sfx/{s}.wav"]; ms=int(t*1000)
    filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.75,adelay={ms}|{ms}[a{idx}]"); idx+=1
filt.append("".join(f"[a{i}]" for i in range(idx))+f"amix=inputs={idx}:normalize=0,atrim=0:{TOTAL},alimiter=limit=0.95[aout]")
subprocess.run(["ffmpeg","-v","error","-y",*inputs,"-filter_complex",";".join(filt),"-map","[aout]","-c:a","aac","-b:a","160k","mix.m4a"],check=True)
subprocess.run(["ffmpeg","-v","error","-y","-i","base.mp4","-f","concat","-safe","0","-i","ov.txt","-i","mix.m4a",
  "-filter_complex","[1:v]fps=30,format=rgba[o];[0:v][o]overlay=0:0:eof_action=repeat,format=yuv420p[v]",
  "-map","[v]","-map","2:a","-t",str(TOTAL),"-c:v","libx264","-preset","veryfast","-crf","19","-c:a","copy","ep1_1203_ko.mp4"],check=True)
print(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_name,width,height","-of","compact","ep1_1203_ko.mp4"]).decode())
