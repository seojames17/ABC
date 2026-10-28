"""에피소드 설계도(JSON)와 장면별 내레이션으로 세로 영상을 렌더링한다.

    python3 render.py episode.json --lang ko|en --assets DIR --out out.mp4

DIR 구조:
    cut/<컷 이름>.png      장면 그림
    aud/<lang>/<장면 번호>.mp3  장면별 내레이션 (verify.py로 확인한 것)
    sfx/<이름>.wav          효과음 (../tools/make_sfx.sh)
    fonts/BlackHanSans.ttf, fonts/NotoSansKR.ttf

컷 전환 시점은 손으로 정하지 않는다. 각 장면 내레이션을 faster-whisper로 받아 적은 뒤,
비트(컷)마다 할당된 대사 글자 수 비율로 가장 가까운 단어 경계를 찾아 그 단어가 시작되는 순간에 컷을 바꾼다.
"""
import argparse
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
_CHAR_RE = re.compile(r"[\w가-힣]")


def nchars(text):
    return len(_CHAR_RE.findall(text or ""))


def font(assets, name, size, bold=False):
    path = os.path.join(assets, "fonts", "BlackHanSans.ttf" if name == "bhs" else "NotoSansKR.ttf")
    f = ImageFont.truetype(path, size)
    if bold:
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
    return f


def resolve(spec, vote=None):
    """투표 갈래(vote)가 있는 장면 중 선택된 것만 남기고, battery "vote"는 선택된 갈래의 배터리 값으로 채운다."""
    chosen = [sc for sc in spec["scenes"] if "vote" not in sc or sc["vote"] == vote]
    batt = next((sc["battery"] for sc in chosen if "vote" in sc and isinstance(sc.get("battery"), int)), None)
    return dict(spec, scenes=[dict(sc, battery=batt) if sc.get("battery") == "vote" else sc for sc in chosen])


def spoken(b, lang):
    """녹음에 쓴 텍스트. 자막과 읽는 법이 다르면 비트의 tts에 적어 둔다."""
    return (b.get("tts") or {}).get(lang) or b.get(lang, "")


def duration(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def words_of(path, lang, model):
    segs, _ = model.transcribe(path, language=lang, word_timestamps=True)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words if w.word.strip()]


def beat_starts(beats, lang, words):
    """비트별 대사 글자 수 누적 비율에 가장 가까운 단어 경계의 시작 시각(장면 내 상대 시간)."""
    lens = [nchars(spoken(b, lang)) for b in beats]
    total_b = sum(lens) or 1
    wl = [nchars(w[0]) for w in words]
    total_w = sum(wl) or 1
    cum_w, acc = [], 0
    for n in wl:
        cum_w.append(acc)
        acc += n
    starts, acc_b, last_j = [0.0], 0, 0
    for i in range(1, len(beats)):
        acc_b += lens[i - 1]
        target = acc_b / total_b * total_w
        cands = range(last_j + 1, len(words)) if last_j + 1 < len(words) else [len(words) - 1]
        j = min(cands, key=lambda k: abs(cum_w[k] - target))
        last_j = j
        starts.append(words[j][1])
    return starts


def build_timeline(spec, lang, assets, work):
    from faster_whisper import WhisperModel
    model = WhisperModel("small", compute_type="int8")
    t = spec.get("lead_in", 0.3)
    gap = spec.get("scene_gap", 0.35)
    # 내레이션 배속 (음높이 유지). 대사가 길어 영상이 늘어질 때 쓴다. 예: "speed": {"ko": 1.12}
    speed = (spec.get("speed") or {}).get(lang, 1.0)
    narr, beats_out = [], []
    for si, scene in enumerate(spec["scenes"], 1):
        aud = os.path.join(assets, "aud", lang, f"{si}.mp3")
        if speed != 1.0:
            fast = os.path.join(work, f"narr{si:02d}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", aud, "-filter:a", f"atempo={speed}", fast], check=True)
            aud = fast
        d = duration(aud)
        words = words_of(aud, lang, model)
        starts = beat_starts(scene["beats"], lang, words)
        start = 0.0 if si == 1 else t
        narr.append((aud, t))
        for bi, b in enumerate(scene["beats"]):
            beats_out.append(dict(b, scene=si, batt=scene.get("battery"),
                                  t0=(start if bi == 0 else t + starts[bi])))
        t = t + d + gap
    total = t - gap + spec.get("tail", 1.8)
    for i, b in enumerate(beats_out):
        b["t1"] = beats_out[i + 1]["t0"] if i + 1 < len(beats_out) else total
    return narr, beats_out, total


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        s = (cur + " " + w).strip()
        if d.textlength(s, font=f) <= maxw:
            cur = s
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def overlay(spec, lang, assets, b, subtitle):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    badge = spec["badge"][lang]
    bf = font(assets, "bhs", 54)
    bw = d.textlength(badge, font=bf) + 70
    d.rounded_rectangle((40, 60, 40 + bw, 160), 20, fill=(0, 0, 0, 220))
    d.text((40 + bw / 2, 110), badge, font=bf, fill="white", anchor="mm")
    p = b.get("batt")
    if p:
        x0, y0 = 760, 75
        col = (220, 40, 40) if p <= 25 else (255, 190, 0) if p <= 45 else (60, 200, 90)
        d.rounded_rectangle((x0 - 20, 60, 1040, 160), 20, fill=(0, 0, 0, 220))
        d.rectangle((x0, y0 + 10, x0 + 110, y0 + 60), outline="white", width=5)
        d.rectangle((x0 + 110, y0 + 25, x0 + 120, y0 + 45), fill="white")
        d.rectangle((x0 + 8, y0 + 18, x0 + 8 + int(94 * p / 100), y0 + 52), fill=col)
        d.text((x0 + 140, 110), f"{p}%", font=font(assets, "bhs", 56), fill="white", anchor="lm")
    key = (b.get("key") or {}).get(lang)
    if key:
        kf = font(assets, "bhs", 84 if len(key) <= 16 else 70)
        d.text((W // 2, 300), key, font=kf, fill=(255, 230, 0), anchor="mm", stroke_width=9, stroke_fill="black")
    for o in b.get("draw", []):
        text = o["text"][lang] if isinstance(o["text"], dict) else o["text"]
        of = font(assets, "bhs", o.get("size", 80))
        x, y = o["xy"]
        if o.get("box"):
            tw = d.textlength(text, font=of)
            d.rounded_rectangle((x - tw / 2 - 40, y - 55, x + tw / 2 + 40, y + 55), 24, fill=(0, 0, 0, 210))
        fill = o.get("fill", "white")
        d.text((x, y), text, font=of, fill=tuple(fill) if isinstance(fill, list) else fill, anchor="mm",
               stroke_width=o.get("stroke", 0), stroke_fill=o.get("stroke_fill", "black"))
    if subtitle:
        sf = font(assets, "noto", 62, bold=True)
        lines = wrap(d, subtitle, sf, 960)
        y = 1600 - (len(lines) - 1) * 45
        for ln in lines:
            d.text((W // 2, y), ln, font=sf, fill="white", anchor="mm", stroke_width=8, stroke_fill="black")
            y += 90
    return im


def render(spec, lang, assets, out, work):
    os.makedirs(work, exist_ok=True)
    narr, beats, total = build_timeline(spec, lang, assets, work)

    # 자막: cont=true인 비트는 같은 줄에 이어 붙여 말하는 대로 글자가 늘어나게 한다
    line = ""
    with open(os.path.join(work, "ov.txt"), "w") as fh:
        for i, b in enumerate(beats):
            text = b.get(lang, "")
            line = (line + " " + text).strip() if b.get("cont") else text
            path = os.path.join(work, f"ov{i:03d}.png")
            overlay(spec, lang, assets, b, line).save(path)
            fh.write(f"file '{os.path.basename(path)}'\nduration {b['t1'] - b['t0']:.3f}\n")
        fh.write(f"file 'ov{len(beats) - 1:03d}.png'\n")

    segs, frames_acc = [], 0
    for i, b in enumerate(beats):
        end_frames = round(b["t1"] * FPS)
        n = max(1, end_frames - frames_acc)
        frames_acc = end_frames
        mode = b.get("zoom", "in")
        z = {"in": "'min(1+0.0012*on,1.08)'", "out": "'max(1.08-0.0012*on,1.0)'",
             "push": "'min(1+0.004*on,1.25)'"}.get(mode, "1.0")
        shake = (",crop=1080:1920:'(in_w-1080)/2+8*sin(n*2.1)':'(in_h-1920)/2+8*cos(n*1.7)',scale=1080:1920"
                 if mode == "shake" else "")
        vf = (f"scale=1620:2895,crop=1620:2880,zoompan=z={z}:d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":s=1100x1956:fps={FPS},crop=1080:1920{shake},setsar=1,format=yuv420p")
        seg = os.path.join(work, f"seg{i:03d}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(assets, "cut", f"{b['cut']}.png"),
                        "-vf", vf, "-frames:v", str(n), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "19", seg], check=True)
        segs.append(os.path.basename(seg))
    with open(os.path.join(work, "segs.txt"), "w") as fh:
        fh.write("".join(f"file '{s}'\n" for s in segs))
    base = os.path.join(work, "base.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(work, "segs.txt"), "-c", "copy", base], check=True)

    inputs, filt, idx = [], [], 0
    for path, t in narr:
        ms = int(t * 1000)
        inputs += ["-i", path]
        filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{idx}]")
        idx += 1
    for b in beats:
        for s in ([b["sfx"]] if isinstance(b.get("sfx"), str) else b.get("sfx", [])):
            ms = int(b["t0"] * 1000)
            inputs += ["-i", os.path.join(assets, "sfx", f"{s}.wav")]
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.75,"
                        f"adelay={ms}|{ms}[a{idx}]")
            idx += 1
    filt.append("".join(f"[a{i}]" for i in range(idx)) +
                f"amix=inputs={idx}:normalize=0,atrim=0:{total:.3f},alimiter=limit=0.95[aout]")
    mix = os.path.join(work, "mix.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[aout]", "-c:a", "aac", "-b:a", "160k", mix], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-f", "concat", "-safe", "0", "-i",
                    os.path.join(work, "ov.txt"), "-i", mix, "-filter_complex",
                    "[1:v]fps=30,format=rgba[o];[0:v][o]overlay=0:0:eof_action=repeat,format=yuv420p[v]",
                    "-map", "[v]", "-map", "2:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "19", "-c:a", "copy", out], check=True)
    with open(os.path.join(work, "timeline.json"), "w") as fh:
        json.dump([{k: b[k] for k in ("scene", "cut", "t0", "t1")} for b in beats], fh, indent=1)
    print(f"{out}: {total:.1f}s, {len(beats)} beats")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--lang", required=True)
    ap.add_argument("--assets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=None)
    ap.add_argument("--vote", default=None, help="지난 화 투표 결과 (vote 갈래가 있는 화)")
    a = ap.parse_args()
    spec = resolve(json.load(open(a.spec, encoding="utf-8")), a.vote)
    render(spec, a.lang, a.assets, a.out, a.work or f"work_{a.lang}")


if __name__ == "__main__":
    sys.exit(main())
