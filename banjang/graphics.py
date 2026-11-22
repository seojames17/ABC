"""리소그래프(두 잉크) 질감의 정보 그래픽. 모든 frame 함수는 1080x1920 RGB."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SAFE = (90, 240, 990, 1500)
INK = {"orange": (255, 106, 19), "teal": (14, 124, 123), "paper": (243, 238, 226), "ink": (30, 42, 42)}
FONTS = os.environ.get("BANJANG_FONTS", os.path.expanduser("~/bj/fonts"))
FONT_BHS = os.path.join(FONTS, "BlackHanSans.ttf")
FONT_NOTO = os.path.join(FONTS, "NotoSansKR.ttf")
BAR_TOP, BAR_ROW, BAR_X0, BAR_X1 = 420, 130, 120, 960

_HT = {}


def _font(path, size):
    return ImageFont.truetype(path, size)


def count_text(value: float, t: float) -> str:
    v0 = float(value)
    dec = 0 if v0.is_integer() else len(repr(v0).split(".")[1])
    v = v0 if t >= 1 else v0 * max(0.0, t)
    return f"{v:.{dec}f}"


def fit_text(text, font_path, max_w, start, min_size):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(start, min_size - 1, -4):
        f = _font(font_path, size)
        lines, cur = [], ""
        for word in text.split(" "):
            cand = (cur + " " + word).strip()
            if d.textlength(cand, font=f) <= max_w:
                cur = cand
            else:
                if cur:
                    lines.append(cur)
                cur = word
        lines.append(cur)
        if len(lines) <= 2 and all(d.textlength(l, font=f) <= max_w for l in lines):
            return lines, size
    f = _font(font_path, min_size)
    lines, cur = [], ""
    for ch in text:  # 최후 수단: 글자 단위로 끊어 절대 넘지 않게
        if d.textlength(cur + ch, font=f) > max_w:
            lines.append(cur); cur = ch
        else:
            cur += ch
    lines.append(cur)
    return [l.strip() for l in lines], min_size


def _paper(seed):
    rng = np.random.default_rng(seed)
    grain = np.kron(rng.normal(0, 5, (H // 4, W // 4)), np.ones((4, 4)))[:H, :W]
    return np.clip(np.array(INK["paper"], float) + grain[..., None], 0, 255)


def _halftone(density, cell=6):
    """농도(0~1 배열)를 망점 마스크로. 칸마다 원 하나, 반지름은 농도의 제곱근에 비례."""
    key = cell
    if key not in _HT:
        yy, xx = np.mgrid[0:H, 0:W]
        _HT[key] = np.sqrt((yy % cell - cell / 2) ** 2 + (xx % cell - cell / 2) ** 2)
    return (_HT[key] <= cell * 0.75 * np.sqrt(np.clip(density, 0, 1))).astype(float)


def _compose(orange_m, teal_m, ink_layer, seed):
    """두 잉크 마스크를 종이에 곱하기 합성. 청록 판은 (+3,-2)px 어긋남. ink_layer(L)는 먹색 글자."""
    out = _paper(seed) / 255
    teal_m = np.roll(np.roll(teal_m, -2, axis=0), 3, axis=1)
    for m, c in ((orange_m, INK["orange"]), (teal_m, INK["teal"])):
        col = np.array(c, float) / 255
        out = out * (1 - m[..., None] + m[..., None] * col)
    img = Image.fromarray((out * 255).astype(np.uint8))
    if ink_layer is not None:
        img.paste(Image.new("RGB", (W, H), INK["ink"]), (0, 0), ink_layer)
    return img


def riso(img: Image.Image, seed: int) -> Image.Image:
    """임의 그림을 주황/청록 두 잉크 인쇄로. 진한 곳은 단색, 옅은 곳은 망점."""
    a = np.asarray(img.convert("RGB").resize((W, H))).astype(float) / 255
    o, t = np.array(INK["orange"]) / 255, np.array(INK["teal"]) / 255
    A = np.stack([1 - o, 1 - t], axis=1)
    coef = np.linalg.lstsq(A, (1 - a).reshape(-1, 3).T, rcond=None)[0]
    co = np.clip(coef[0].reshape(H, W), 0, 1)
    ct = np.clip(coef[1].reshape(H, W), 0, 1)
    so, st = (co > 0.85).astype(float), (ct > 0.85).astype(float)
    return _compose(np.maximum(so, _halftone(co * (1 - so))), np.maximum(st, _halftone(ct * (1 - st))), None, seed)


def _ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _stagger(t, i, n, lag):
    return 1.0 if t >= 1 else _ease(t * (n * lag + 1) - i * lag)


def _title(d, text, y=260):
    if not text:
        return
    lines, size = fit_text(text, FONT_BHS, 860, 96, 56)
    f = _font(FONT_BHS, size)
    for i, l in enumerate(lines):
        d.text((W // 2, y + i * (size + 10)), l, font=f, fill=255, anchor="mt")


def _clip_label(d, text, f, max_w):
    while d.textlength(text, font=f) > max_w and len(text) > 1:
        text = text[:-1]
    return text


def bars_frame(items, t, unit, seed, title=None):
    om = np.zeros((H, W)); tm = np.zeros((H, W))
    ink = Image.new("L", (W, H), 0); d = ImageDraw.Draw(ink)
    _title(d, title)
    vmax = max([v for _, v in items] + [1e-9])
    lf, vf = _font(FONT_NOTO, 40), _font(FONT_BHS, 52)
    rows = [(l, v) for i, (l, v) in enumerate(items) if BAR_TOP + (i + 1) * BAR_ROW <= SAFE[3]]
    n = len(rows)
    dots = _halftone(np.full((H, W), 0.35))
    for i, (label, v) in enumerate(rows):
        y0 = BAR_TOP + i * BAR_ROW
        ti = _stagger(t, i, n, 0.6)
        if ti > 0:
            bw = max(8, int((BAR_X1 - BAR_X0) * 0.68 * (v / vmax) * ti))
            by = y0 + BAR_ROW // 2 - 22
            om[by:by + 44, BAR_X0:BAR_X0 + bw] = 1
            tm[by + 10:by + 44, BAR_X0:BAR_X0 + bw] = dots[by + 10:by + 44, BAR_X0:BAR_X0 + bw]
            val = count_text(v, ti) + unit
            vx = min(BAR_X0 + bw + 16, SAFE[2] - d.textlength(val, font=vf))
            d.text((vx, y0 + BAR_ROW // 2), val, font=vf, fill=255, anchor="lm")
        d.text((BAR_X0, y0 + 2), _clip_label(d, label, lf, BAR_X1 - BAR_X0), font=lf, fill=255, anchor="lt")
    return _compose(om, tm, ink, seed)


def scale_frame(value, t, unit, seed, title=None, vmax=None):
    om = np.zeros((H, W)); tm = np.zeros((H, W))
    ink = Image.new("L", (W, H), 0); d = ImageDraw.Draw(ink)
    _title(d, title)
    cx, cy, r = W // 2, 860, 330
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    dome = (dist <= r) & (yy <= cy)
    tm[dome] = _halftone(np.full((H, W), 0.45))[dome]
    om[dome & (dist >= r - 14)] = 1
    vmax = vmax or max(1.0, math.ceil(value * 1.25))
    e = _ease(t)
    for k in range(11):
        a = math.pi * (1 - k / 10)
        d.line([(cx + (r - 44) * math.cos(a), cy - (r - 44) * math.sin(a)),
                (cx + (r - 18) * math.cos(a), cy - (r - 18) * math.sin(a))], fill=255, width=6)
    ang = math.pi * (1 - min(value * e, vmax) / vmax)
    d.line([(cx, cy), (cx + (r - 54) * math.cos(ang), cy - (r - 54) * math.sin(ang))], fill=255, width=12)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=255)
    d.text((cx, cy + 50), count_text(value, e), font=_font(FONT_BHS, 200), fill=255, anchor="mt")
    om[cy + 290:cy + 308, cx - 120:cx + 120] = 1
    d.text((cx, cy + 330), unit, font=_font(FONT_BHS, 72), fill=255, anchor="mt")
    return _compose(om, tm, ink, seed)


def checklist_frame(items, t, marks, seed, title=None):
    om = np.zeros((H, W)); tm = np.zeros((H, W))
    ink = Image.new("L", (W, H), 0); d = ImageDraw.Draw(ink)
    _title(d, title)
    n = len(items)
    row = min(150, (SAFE[3] - 460) // max(n, 1))
    f, sf = _font(FONT_BHS, 64), _font(FONT_BHS, 70)
    shown = []
    for i, (txt, mk) in enumerate(zip(items, marks)):
        if _stagger(t, i, n, 0.7) <= 0:
            continue
        y = 460 + i * row
        (om if mk == "x" else tm)[y:y + 90, 130:220] = 1
        d.text((260, y + 45), _clip_label(d, txt, f, SAFE[2] - 260), font=f, fill=255, anchor="lm")
        shown.append((y, mk))
    img = _compose(om, tm, ink, seed)
    dd = ImageDraw.Draw(img)
    for y, mk in shown:
        dd.text((175, y + 45), "X" if mk == "x" else "O", font=sf, fill=INK["paper"], anchor="mm")
    return img
