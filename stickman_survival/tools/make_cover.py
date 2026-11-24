"""표지 이미지 만들기 (RUNBOOK ⑧).

    python3 make_cover.py <컷 png> <출력 jpg> --badge "1203호 13화" --big "정전 21일째" --sub "불이 들어오는 날" [--font serif] [--assets assets] [--dark]

맨 위 빨간 배지, 가장 크게 노란 큰 글자, 그 아래 흰색 한 줄. 글자는 프로필 격자(가운데 3:4, y 240~1680) 안에 둔다.
--dark 는 시즌 2용: 배지를 짙은 남색, 큰 글자를 상아색으로.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONTS = {"bhs": "BlackHanSans.ttf", "serif": "NotoSerifKR.ttf", "noto": "NotoSansKR.ttf"}


def font(assets, name, size):
    f = ImageFont.truetype(os.path.join(assets, "fonts", FONTS[name]), size)
    if name != "bhs":
        try:
            f.set_variation_by_name("Black")
        except Exception:
            try:
                f.set_variation_by_name("Bold")
            except Exception:
                pass
    return f


def fit(d, text, assets, name, size, maxw, minsize=60):
    f = font(assets, name, size)
    while d.textlength(text, font=f) > maxw and size > minsize:
        size -= 4
        f = font(assets, name, size)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--badge", required=True)
    ap.add_argument("--big", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--font", default="bhs")
    ap.add_argument("--assets", default="assets")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--y", type=int, default=330, help="배지 윗변 y (격자 안쪽 240 이상)")
    a = ap.parse_args()

    im = Image.open(a.src).convert("RGB").resize((W, H))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # 글자 뒤를 살짝 어둡게 해서 어떤 컷 위에서도 읽히게 한다
    band_top, band_bot = a.y - 60, a.y + 560 + (90 if a.sub else 0)
    for i in range(band_top, band_bot):
        t = 1 - abs((i - (band_top + band_bot) / 2) / ((band_bot - band_top) / 2))
        d.line((0, i, W, i), fill=(0, 0, 0, int(150 * min(1, t * 2))))

    badge_col = (20, 40, 90) if a.dark else (215, 30, 30)
    big_col = (245, 235, 210) if a.dark else (255, 225, 0)
    bf = font(a.assets, a.font, 64)
    bw = d.textlength(a.badge, font=bf) + 80
    y = a.y
    d.rounded_rectangle(((W - bw) / 2, y, (W + bw) / 2, y + 110), 24, fill=badge_col)
    d.text((W / 2, y + 55), a.badge, font=bf, fill="white", anchor="mm")
    y += 170
    gf = fit(d, a.big, a.assets, a.font, 190, 960)
    d.text((W / 2, y + 110), a.big, font=gf, fill=big_col, anchor="mm", stroke_width=12, stroke_fill="black")
    y += 260
    if a.sub:
        sf = fit(d, a.sub, a.assets, a.font, 96, 940)
        d.text((W / 2, y + 60), a.sub, font=sf, fill="white", anchor="mm", stroke_width=9, stroke_fill="black")
    out = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    out.save(a.out, quality=92)
    print("saved", a.out)


if __name__ == "__main__":
    main()
