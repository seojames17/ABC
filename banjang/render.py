"""윤 반장 설계도(JSON) → 1080x1920 30fps mp4.
python3 render.py episodes/b001.json --assets assets --out b001.mp4
"""
import argparse, json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphics import (W, H, INK, FONT_BHS, FONT_NOTO, fit_text, _font, _ease,
                      bars_frame, scale_frame, checklist_frame)

FPS, GAP = 30, 0.25
SILENCE = "silenceremove=stop_periods=-1:stop_duration=0.45:stop_threshold=-38dB:stop_silence=0.3"


def check(spec, assets):
    miss = []
    for i, s in enumerate(spec["scenes"], 1):
        if s["type"] == "art" and not os.path.exists(os.path.join(assets, "cut", s["image"] + ".png")):
            miss.append(f"cut/{s['image']}.png")
        if not os.path.exists(os.path.join(assets, "aud", f"{i}.mp3")):
            miss.append(f"aud/{i}.mp3")
    return miss


def plan(spec, durations):
    speed = spec["voice"].get("speed", 1.0)
    starts, t = [], 0.0
    for d in durations:
        starts.append(round(t, 4))
        t += d / speed + GAP
    return starts


def warn_length(total):
    if total > 45:
        print(f"경고: 영상 {total:.1f}초, 45초 초과", file=sys.stderr)


def _dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True, check=True).stdout)


def _subtitle(img, text):
    if not text:
        return img
    d = ImageDraw.Draw(img)
    lines, size = fit_text(text, FONT_NOTO, 860, 52, 40)
    f = _font(FONT_NOTO, size)
    h = len(lines) * (size + 12) + 36
    y0 = 1560 - h // 2
    d.rectangle([90, y0, 990, y0 + h], fill=INK["ink"])
    for k, l in enumerate(lines):
        d.text((W // 2, y0 + 18 + k * (size + 12)), l, font=f, fill=INK["paper"], anchor="mt")
    return img


def _art_frame(src, t, title, shift=0):
    """shift: 그림을 아래로 내려 위쪽을 종이로 비운다(제목이 얼굴을 가리지 않게)."""
    z = 1.0 + 0.06 * t
    w, h = int(W * z), int(H * z)
    img = src.resize((w, h), Image.LANCZOS).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
    if shift:
        base = Image.new("RGB", (W, H), src.getpixel((8, 8)))  # 그림 자체의 종이색으로 채워 이음새가 안 보이게
        base.paste(img, (0, shift))
        img = base
    if title:
        d = ImageDraw.Draw(img)
        lines, size = fit_text(title, FONT_BHS, 860, 110, 60)
        f = _font(FONT_BHS, size)
        for k, l in enumerate(lines):
            d.text((W // 2, 260 + k * (size + 10)), l, font=f, fill=INK["ink"], anchor="mt",
                   stroke_width=10, stroke_fill=INK["paper"])
    return img


def scene_frame(s, t_scene, seed, art_cache):
    """t_scene: 장면 안 진행도 0~1. 그래픽은 앞 70% 동안 0→1."""
    tg = min(1.0, t_scene / 0.7)
    title = s.get("title")
    if s["type"] == "art":
        img = _art_frame(art_cache[s["image"]], t_scene, title, s.get("shift", 0))
    elif s["type"] == "scale":
        img = scale_frame(s["value"], tg, s.get("unit", ""), seed, title=title, vmax=s.get("max"))
    elif s["type"] == "bars":
        img = bars_frame([tuple(x) for x in s["items"]], tg, s.get("unit", ""), seed, title=title)
    elif s["type"] == "list":
        img = checklist_frame(s["items"], tg, s["marks"], seed, title=title)
    else:
        raise ValueError(f"모르는 장면 종류: {s['type']}")
    return _subtitle(img, s.get("say"))


def render(spec, assets, out):
    miss = check(spec, assets)
    if miss:
        sys.exit("빠진 파일: " + ", ".join(miss))
    speed = spec["voice"].get("speed", 1.0)
    work = tempfile.mkdtemp()
    parts, durs = [], []
    for i in range(1, len(spec["scenes"]) + 1):
        p = os.path.join(work, f"{i}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(assets, "aud", f"{i}.mp3"),
                        "-af", f"{SILENCE},atempo={speed}", "-ar", "44100", "-ac", "1", p], check=True)
        parts.append(p); durs.append(_dur(p) * speed)  # plan()이 speed로 나누므로 원래 길이 기준으로 맞춤
    starts = plan(spec, durs)
    lens = [d / speed + GAP for d in durs]
    total = starts[-1] + lens[-1]
    warn_length(total)
    # 음성: 장면 사이 GAP 무음
    sil = os.path.join(work, "gap.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(GAP), sil], check=True)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{p}'\nfile '{sil}'\n")
    audio = os.path.join(work, "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, audio], check=True)
    art = {s["image"]: Image.open(os.path.join(assets, "cut", s["image"] + ".png")).convert("RGB").resize((W, H))
           for s in spec["scenes"] if s["type"] == "art"}
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                           "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", out],
                          stdin=subprocess.PIPE)
    for idx, s in enumerate(spec["scenes"]):
        n = max(1, round(lens[idx] * FPS))
        last = None
        for k in range(n):
            t_scene = k / n
            # 그래픽은 70% 지나면 멈춤 → 마지막 프레임 재사용으로 시간 절약
            if s["type"] != "art" and t_scene >= 0.7 and last is not None:
                ff.stdin.write(last); continue
            frame = scene_frame(s, t_scene, idx + 1, art).tobytes()
            last = frame
            ff.stdin.write(frame)
    ff.stdin.close(); ff.wait()
    print(f"{out} {total:.1f}s")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--assets", default="assets"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    render(json.load(open(a.spec, encoding="utf-8")), a.assets, a.out)


if __name__ == "__main__":
    main()
