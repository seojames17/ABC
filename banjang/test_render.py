import io, os, sys, tempfile, contextlib
sys.path.insert(0, os.path.dirname(__file__))
from render import check, plan, warn_length, ff_ok

SAMPLE = {"title": "t", "voice": {"voice_id": "x", "speed": 1.25}, "scenes": [
    {"type": "art", "image": "b000_01", "title": "몇 kg?", "say": "a"},
    {"type": "scale", "value": 11.4, "unit": "kg", "title": "x", "say": "b"},
    {"type": "list", "items": ["a"], "marks": ["x"], "title": "y", "say": "c"}]}


def assets_with_aud(*ns):
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "aud")); os.makedirs(os.path.join(d, "cut"))
    open(os.path.join(d, "cut", "b000_01.png"), "wb").close()
    for n in ns:
        open(os.path.join(d, "aud", f"{n}.mp3"), "wb").close()
    return d


def test_check_missing_audio():
    assert check(SAMPLE, assets_with_aud(1, 2)) == ["aud/3.mp3"]


def test_check_missing_image():
    d = assets_with_aud(1, 2, 3); os.remove(os.path.join(d, "cut", "b000_01.png"))
    assert check(SAMPLE, d) == ["cut/b000_01.png"]


def test_plan_starts():
    assert plan(SAMPLE, [2.5, 5.0, 2.5]) == [0.0, 2.25, 6.5]


def test_long_warning():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        warn_length(46.0); warn_length(30.0)
    assert buf.getvalue().count("45초 초과") == 1


def test_ffmpeg_failure_exits():
    try:
        ff_ok(1)
    except SystemExit:
        ff_ok(0)
        return
    raise AssertionError("ffmpeg 실패가 그냥 지나감")


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("ok  ", k)
            except Exception as e:
                fails += 1; print("FAIL", k, repr(e)[:200])
    sys.exit(1 if fails else 0)
