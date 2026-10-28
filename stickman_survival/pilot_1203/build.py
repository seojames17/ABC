"""「1203호」 15초 시범판 렌더링: 컷별 줌 영상 → 이어붙이기 → 내레이션+효과음 믹스 → 자막 오버레이.

작업 폴더: cut/01~10.png, sfx/*.wav (tools/make_sfx.sh), fonts/, 내레이션 mp3 경로는 NARR 참고.
"""
import subprocess
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920; BHS="fonts/BlackHanSans.ttf"
def noto(s):
    f=ImageFont.truetype("fonts/NotoSansKR.ttf",s)
    try: f.set_variation_by_name("Bold")
    except Exception: pass
    return f
TOTAL=14.0
# (컷 파일, 시작, 끝, 확대 방향) — 전환 시점은 내레이션 단어 타이밍 기준
CUTS=[("01",0.0,1.24,"in"),("02",1.24,1.78,"in"),("03",1.78,2.78,"none"),("04",2.78,5.2,"out"),
      ("05",5.2,7.08,"in"),("06",7.08,8.5,"in"),("07",8.5,9.5,"out"),("08",9.5,10.64,"in"),
      ("09",10.64,11.56,"in"),("10",11.56,14.0,"push")]
SUBS=[(0.0,2.78,"밤 9시. 전기가 나갔습니다.",None),(2.78,5.2,"그리고… 다시는 들어오지 않았습니다.",None),
      (5.2,7.08,"민수는 생각했죠.",62),(7.08,8.5,"\"곧 들어오겠지.\"",62),
      (8.5,10.64,"심심해서 맥주나 마시려고",62),(10.64,14.0,"냉장고를 열었는데—",62)]
NARR=[("/home/user/ep1_ko/aud/1.mp3",0.3),("/home/user/ep1_ko/aud/2.mp3",5.2),("/home/user/ep1_ko/aud/3.mp3",8.5)]
SFX=[("hum",1.0),("thunk",1.78),("click",5.35),("whoosh",9.45),("creak",10.7),("sting",11.56)]

def overlay(text,batt):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((40,60,420,160),20,fill=(0,0,0,220))
    d.text((230,110),"1203호 · DAY 1",font=ImageFont.truetype(BHS,56),fill="white",anchor="mm")
    if batt:
        x0,y0=760,75; col=(60,200,90)
        d.rounded_rectangle((x0-20,60,1040,160),20,fill=(0,0,0,220))
        d.rectangle((x0,y0+10,x0+110,y0+60),outline="white",width=5)
        d.rectangle((x0+110,y0+25,x0+120,y0+45),fill="white")
        d.rectangle((x0+8,y0+18,x0+8+int(94*batt/100),y0+52),fill=col)
        d.text((x0+140,110),f"{batt}%",font=ImageFont.truetype(BHS,56),fill="white",anchor="lm")
    f=noto(64)
    d.text((W//2,1560),text,font=f,fill="white",anchor="mm",stroke_width=8,stroke_fill="black")
    return im

with open("ov.txt","w") as fh:
    for i,(a,b,t,bat) in enumerate(SUBS):
        overlay(t,bat).save(f"ov{i}.png"); fh.write(f"file 'ov{i}.png'\nduration {b-a:.3f}\n")
    fh.write(f"file 'ov{len(SUBS)-1}.png'\n")

# 컷별 영상 (03번은 정전 순간이라 화면을 흔든다)
segs=[]
for name,a,b,mode in CUTS:
    d=b-a; n=max(1,round(d*30))
    if mode=="in": z="'min(1+0.0012*on,1.08)'"
    elif mode=="out": z="'max(1.08-0.0012*on,1.0)'"
    elif mode=="push": z="'min(1+0.004*on,1.25)'"
    else: z="1.0"
    shake = ",crop=1080:1920:'(in_w-1080)/2+8*sin(n*2.1)':'(in_h-1920)/2+8*cos(n*1.7)',scale=1080:1920" if name=="03" else ""
    out=f"seg{name}.mp4"
    vf=(f"scale=1620:2895,crop=1620:2880,zoompan=z={z}:d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1100x1956:fps=30,"
        f"crop=1080:1920{shake if shake else ''},setsar=1,format=yuv420p")
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"cut/{name}.png","-vf",vf,"-frames:v",str(n),"-r","30",
                    "-c:v","libx264","-preset","veryfast","-crf","19",out],check=True)
    segs.append(out)
open("segs.txt","w").write("".join(f"file '{s}'\n" for s in segs))
subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","segs.txt","-c","copy","base.mp4"],check=True)

# 오디오: 내레이션 + 효과음
inputs=[]; filt=[]; idx=0
for f,t in NARR:
    inputs+=["-i",f]; filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={int(t*1000)}|{int(t*1000)}[a{idx}]"); idx+=1
for s,t in SFX:
    inputs+=["-i",f"sfx/{s}.wav"]; filt.append(f"[{idx}:a]aresample=44100,volume=0.8,adelay={int(t*1000)}|{int(t*1000)}[a{idx}]"); idx+=1
filt.append("".join(f"[a{i}]" for i in range(idx))+f"amix=inputs={idx}:normalize=0,atrim=0:{TOTAL},alimiter=limit=0.95[aout]")
subprocess.run(["ffmpeg","-v","error","-y",*inputs,"-filter_complex",";".join(filt),"-map","[aout]","-c:a","aac","-b:a","160k","mix.m4a"],check=True)

subprocess.run(["ffmpeg","-v","error","-y","-i","base.mp4","-f","concat","-safe","0","-i","ov.txt","-i","mix.m4a",
  "-filter_complex","[1:v]fps=30,format=rgba[o];[0:v][o]overlay=0:0:eof_action=repeat,format=yuv420p[v]",
  "-map","[v]","-map","2:a","-t",str(TOTAL),"-c:v","libx264","-preset","veryfast","-crf","19","-c:a","copy","pilot.mp4"],check=True)
print(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_name,width,height","-of","compact","pilot.mp4"]).decode())
