import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from graphics import (INK, BAR_TOP, BAR_ROW, BAR_X0, riso, fit_text, count_text,
                      bars_frame, scale_frame, checklist_frame, FONT_BHS)

ORANGE = np.array(INK["orange"])
PAPER = np.array(INK["paper"])


def orange_mask(im):
    a = np.asarray(im).astype(int)
    return (np.abs(a - ORANGE).sum(axis=2) < 90)


def orange_width_in_row(im, i):
    y = BAR_TOP + i * BAR_ROW + BAR_ROW // 2
    return int(orange_mask(im)[y - 4:y + 4, BAR_X0:990].any(axis=0).sum())


def non_paper_bbox(im):
    a = np.asarray(im).astype(int)
    m = np.abs(a - PAPER).sum(axis=2) > 60
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max(), ys.max()


def text_w(line, size):
    f = ImageFont.truetype(FONT_BHS, size)
    return ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(line, font=f)


def near_ink_mix(c, tol):
    cands = [np.array(v) for v in INK.values()]
    o, t = np.array(INK["orange"]) / 255, np.array(INK["teal"]) / 255
    cands.append(o * t * 255)
    return min(np.abs(np.array(c) - k).sum() for k in cands) <= tol * 3


def test_count_text():
    assert count_text(11.4, 1.0) == "11.4"
    assert count_text(11.4, 0.0) == "0.0"
    assert count_text(500, 0.5) == "250"


def test_bars_min_visible():
    im = bars_frame([("생수", 6.0), ("랜턴", 0.0), ("라디오", 0.06)], 1.0, "kg", 1)
    assert im.size == (1080, 1920)
    assert orange_width_in_row(im, 1) >= 8, orange_width_in_row(im, 1)
    assert orange_width_in_row(im, 2) >= 8


def test_bars_t0_empty():
    im = bars_frame([("생수", 6.0)], 0.0, "kg", 1)
    y = BAR_TOP + BAR_ROW // 2
    assert orange_mask(im)[y - 4:y + 4, BAR_X0:990].sum() == 0


def test_fit_text_long_korean():
    lines, size = fit_text("재난가방 공식 목록대로 전부 넣으면 몇 킬로그램일까요", FONT_BHS, 900, 120, 60)
    assert size >= 60 and all(text_w(l, size) <= 900 for l in lines), (lines, size)


def test_riso_palette():
    art = Image.new("RGB", (1080, 1920), INK["paper"])
    d = ImageDraw.Draw(art)
    d.rectangle([200, 400, 800, 900], fill=INK["orange"])
    d.ellipse([300, 1000, 900, 1500], fill=INK["teal"])
    out = riso(art, 1).convert("RGB").quantize(8).convert("RGB")
    cols = sorted(out.getcolors(64), reverse=True)[:6]
    assert all(near_ink_mix(c, 40) for _, c in cols), cols


def test_safe_area():
    for im in (scale_frame(11.4, 1.0, "kg", 1), checklist_frame(["생수 3병", "라면"], 1.0, ["o", "x"], 1),
               bars_frame([("아주 긴 물건 이름입니다", 100.0), ("b", 1.0)], 1.0, "kg", 1)):
        x0, y0, x1, y1 = non_paper_bbox(im)
        assert x0 >= 90 and x1 <= 990 and y0 >= 240 and y1 <= 1500, (x0, y0, x1, y1)


def _raises(f):
    try:
        f()
    except ValueError:
        return True
    return False


def test_bars_overflow_raises():
    assert _raises(lambda: bars_frame([(f"항목{i}", i + 1.0) for i in range(12)], 1.0, "kg", 1, title="두 줄이 되는 아주 긴 제목입니다 정말로"))


def test_checklist_marks_mismatch_raises():
    assert _raises(lambda: checklist_frame(["a", "b"], 1.0, ["o"], 1))


def test_checklist_text_too_long_raises():
    assert _raises(lambda: checklist_frame(["가" * 80], 1.0, ["o"], 1))


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("ok  ", k)
            except Exception as e:
                fails += 1; print("FAIL", k, repr(e)[:200])
    sys.exit(1 if fails else 0)
