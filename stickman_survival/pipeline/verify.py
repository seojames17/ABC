"""장면별 AI 내레이션을 받아 적어 대본과 비교한다. 문제가 있는 장면만 다시 녹음하면 된다.

    python3 verify.py episode.json --lang ko|en --assets DIR

다음 경우를 FAIL로 표시한다 (AI 음성에서 실제로 겪은 문제들):
- 받아쓴 내용이 대본과 많이 다름 (유사도 < 0.75)
- 문장 앞에 대본에 없는 소리가 붙음 (첫 단어 전에 0.8초 넘게 다른 말이 있음)
- 1.5초 넘는 정적 (말줄임표 "…"에서 자주 생김)
"""
import argparse
import difflib
import json
import os
import re
import sys

_KEEP = re.compile(r"[^\w가-힣]")


def norm(s):
    return _KEEP.sub("", s or "").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--lang", required=True)
    ap.add_argument("--assets", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))

    from faster_whisper import WhisperModel
    model = WhisperModel("small", compute_type="int8")
    bad = []
    for si, scene in enumerate(spec["scenes"], 1):
        path = os.path.join(a.assets, "aud", a.lang, f"{si}.mp3")
        expected = " ".join(b.get(a.lang, "") for b in scene["beats"])
        segs, _ = model.transcribe(path, language=a.lang, word_timestamps=True)
        words = [w for s in segs for w in s.words if w.word.strip()]
        heard = " ".join(w.word.strip() for w in words)
        ratio = difflib.SequenceMatcher(None, norm(expected), norm(heard)).ratio()
        gaps = [round(words[i + 1].start - words[i].end, 2) for i in range(len(words) - 1)
                if words[i + 1].start - words[i].end > 1.5]
        first = norm(expected.split()[0]) if expected.split() else ""
        prefix = bool(words) and first and not norm(words[0].word).startswith(first[:2]) and words[0].end > 0.8
        problems = []
        if ratio < 0.75:
            problems.append(f"내용 불일치({ratio:.2f})")
        if prefix:
            problems.append("앞에 이상한 소리")
        if gaps:
            problems.append(f"긴 정적 {gaps}")
        status = "FAIL" if problems else "ok"
        print(f"[{status}] {si:>2} {ratio:.2f} | {heard}" + (f"  <- {', '.join(problems)}" if problems else ""))
        if problems:
            bad.append(si)
    print("다시 녹음할 장면:", bad or "없음")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
