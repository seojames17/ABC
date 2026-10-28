"""s01e01 자막·DAY 카운터·배터리 오버레이(투명 PNG)와 장면별 길이(durs.json)를 만든다.

작업 폴더 구조: img/{1..10}.png, aud/{1..10}.mp3, fonts/BlackHanSans.ttf, fonts/NotoSansKR.ttf
다음 화에서는 NARR / BATT / KEY와 8·9번 장면 전용 그리기 부분만 바꾸면 된다.
"""
import json, subprocess
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
BHS = "fonts/BlackHanSans.ttf"
def noto(size):
    f = ImageFont.truetype("fonts/NotoSansKR.ttf", size)
    try: f.set_variation_by_name("Bold")
    except Exception: pass
    return f

NARR = {
 1: ["밤 9시. 전기가 나갔습니다.", "그리고… 다시는 들어오지 않았습니다."],
 2: ["민수는 생각했죠.", "\"곧 들어오겠지.\""],
 3: ["심심해서 맥주나 마시려고", "냉장고를 열었는데—"],
 4: ["잠깐!", "냉장고는 문을 닫아 두면 네 시간 정도 차갑게 버팁니다.", "꽉 찬 냉동실은 이틀 가까이요.", "문을 열 때마다 그 시간이 줄어들어요."],
 5: ["그때 옆집 할머니는 욕조에 물을 받고 계셨어요.", "민수는 웃었죠.", "\"에이, 수돗물이 왜 끊겨요.\""],
 6: ["다음 날 아침.", "수도꼭지에서 물이 졸졸… 멈췄습니다.", "많은 고층 아파트는 전기 펌프로 물을 끌어올려요.", "펌프가 멈추면 물도 멈춥니다."],
 7: ["편의점에 갔더니 카드 단말기가 꺼져 있었어요.", "\"현금만 돼요.\"", "민수 지갑엔… 0원."],
 8: ["민수의 1일차 생존 점수는…", "30점."],
 9: ["남은 배터리 21%.", "당신이라면 어디에 쓰겠어요?", "A, 가족에게 연락.", "B, 밤에 쓸 손전등."],
 10: ["다음 화, DAY 3.", "마트 앞에 줄이 생기기 시작합니다."],
}
BATT = {2:62,3:62,4:62,5:62,6:41,7:41,8:21,9:21}
KEY = {
 4: ["냉장실 약 4시간", "냉동실(가득) 약 48시간"],
 6: ["전기 = 물"],
 7: ["현금만 가능"],
 10: ["NEXT: DAY 3"],
}
PAD = 0.4

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def base(k):
    im = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(BHS, 64)
    d.rounded_rectangle((40, 60, 300, 160), 20, fill=(0,0,0,220))
    d.text((170, 110), "DAY 1", font=f, fill="white", anchor="mm")
    if k in BATT:
        p = BATT[k]; col = (220,40,40) if p <= 25 else (255,190,0) if p <= 45 else (60,200,90)
        x0, y0 = 760, 75
        d.rounded_rectangle((x0-20, 60, 1040, 160), 20, fill=(0,0,0,220))
        d.rectangle((x0, y0+10, x0+110, y0+60), outline="white", width=5)
        d.rectangle((x0+110, y0+25, x0+120, y0+45), fill="white")
        d.rectangle((x0+8, y0+18, x0+8+int(94*p/100), y0+52), fill=col)
        d.text((x0+140, 110), f"{p}%", font=ImageFont.truetype(BHS, 56), fill="white", anchor="lm")
    if k in KEY:
        f2 = ImageFont.truetype(BHS, 84 if len(KEY[k]) < 3 else 70)
        y = 300
        for line in KEY[k]:
            d.text((W//2, y), line, font=f2, fill=(255,230,0), anchor="mm", stroke_width=8, stroke_fill="black")
            y += 105
    # 좌표는 s01e01 이미지(점수판, 휴대폰 버튼 위치)에 맞춘 값
    if k == 8:
        d.text((765, 690), "30", font=ImageFont.truetype(BHS, 230), fill=(220,40,40), anchor="mm")
        d.text((765, 820), "/ 100", font=ImageFont.truetype(BHS, 70), fill="black", anchor="mm")
    if k == 9:
        fb = ImageFont.truetype(BHS, 120)
        d.text((705, 792), "A", font=fb, fill=(30,90,220), anchor="mm")
        d.text((837, 792), "B", font=fb, fill=(230,120,0), anchor="mm")
        f3 = ImageFont.truetype(BHS, 76)
        d.rounded_rectangle((190, 1290, 890, 1400), 24, fill=(0,0,0,200))
        d.text((W//2, 1345), "댓글로 A or B!", font=f3, fill=(255,230,0), anchor="mm")
    return im

def scene(k):
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"aud/{k}.mp3"]))
    total = dur + PAD
    # 자막 덩어리는 글자 수 비율로 시간을 나눈다
    chunks = NARR[k]; weights = [max(len(c),4) for c in chunks]; s = sum(weights)
    lst = []
    f = noto(62)
    for i, c in enumerate(chunks):
        im = base(k); d = ImageDraw.Draw(im)
        lines = wrap(d, c, f, 940)
        y = 1560 - (len(lines)-1)*45
        for ln in lines:
            d.text((W//2, y), ln, font=f, fill="white", anchor="mm", stroke_width=7, stroke_fill="black")
            y += 90
        path = f"ov/{k}_{i}.png"; im.save(path)
        t = dur * weights[i] / s + (PAD if i == len(chunks)-1 else 0)
        lst.append((path, t))
    with open(f"ov/{k}.txt","w") as fh:
        for p, t in lst: fh.write(f"file '{p.split('/')[-1]}'\nduration {t:.3f}\n")
        fh.write(f"file '{lst[-1][0].split('/')[-1]}'\n")
    return total

import os; os.makedirs("ov", exist_ok=True)
durs = {k: scene(k) for k in range(1, 11)}
json.dump(durs, open("durs.json","w"))
print(durs, sum(durs.values()))
