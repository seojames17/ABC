# 윤 반장 개편 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 리소그래프 그림체의 진행자 「윤 반장」이 나오는 재난 대비 정보 릴스를 만드는 새 파이프라인을 세우고, 첫 편을 노션 `업로드 대기`까지 올린다.

**Architecture:** 새 폴더 `banjang/`에 정보 그래픽을 Pillow로 프레임 단위로 그리는 모듈(`graphics.py`)과, 장면 JSON을 영상으로 만드는 렌더러(`render.py`)를 둔다. 그림·목소리 생성, 받아쓰기 검증(`stickman_survival/pipeline/verify.py` 재사용), 업로드, 노션 흐름은 기존 RUNBOOK 방식을 따른다. 렌더는 Higgsfield `sandbox_exec`에서 돈다.

**Tech Stack:** Python 3 + Pillow + numpy(sandbox 기본), ffmpeg, faster-whisper, Higgsfield(`gpt_image_2_5`, `text2speech_v2`/elevenlabs), Notion MCP.

**Spec:** `docs/superpowers/specs/2026-11-22-yoon-banjang-redesign-design.md`

## Global Constraints
- 화면 1080×1920, 30fps, 25~45초. 글자·그래픽은 안전 영역 x 90~990, y 240~1500 안(쇼츠와 겹침).
- 잉크 두 색만: 주황 `#FF6A13`, 청록 `#0E7C7B`, 종이 `#F3EEE2`, 먹(글자) `#1E2A2A`. 그래픽은 망점·어긋남(2~4px) 질감.
- 글꼴: Black Han Sans(큰 숫자·제목), Noto Sans KR(자막). `·` `≈` `→` 금지(글리프 없음).
- 그림: `gpt_image_2_5`, 9:16, quality medium, folder_id `8b843777-b07f-43f6-8e0f-87d3adbb477e`. 윤 반장 참고 이미지는 Task 1의 시트 job id만.
- 그림 공통 문구: `Two-color risograph print illustration, fluorescent orange and teal ink on off-white paper, visible misregistration and halftone dots, hand-printed zine feel, no text, no letters, no numbers`.
- 사실·숫자는 공식 출처 또는 제조사 스펙만, 설명서에 링크. 합산 숫자는 "대표 제품 스펙 기준"이라고 대사·캡션에 밝힌다. "직접 재 봤다" 금지.
- "전쟁" 금지, 실제 소방청·119 로고·제복 금지, 공포 팔이 금지.
- 예산: 준비(Task 1~4 시험) 20크레딧 이내, 화당 약 7크레딧.
- 커밋: `git -c user.name="James Seo" -c user.email="seojames17@users.noreply.github.com" commit`, 메시지 한국어, 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. 브랜치 `claude/stickman-survival`. push 전 `git fetch` + rebase(다른 세션도 같은 브랜치에 push함).

## Review Focus
- 긴 한국어 제목이 화면 폭(900px)을 넘는 경우 → 줄바꿈 후 크기 축소, 절대 잘리지 않는다 (Task 3 `test_fit_text_long_korean`).
- 막대 값이 0이거나 한 값이 나머지보다 100배 큰 경우 → 가장 작은 막대도 최소 8px, 숫자 라벨은 항상 표시 (Task 3 `test_bars_min_visible`).
- 장면 음성 파일이 빠진 경우 → 렌더 전에 빠진 파일 이름을 대고 멈춘다 (Task 4 `test_check_missing_audio`).
- 전체가 45초를 넘는 경우 → 렌더는 하되 경고 출력 (Task 4 `test_long_warning`).
- 소수 카운트업(11.4kg) → 중간 프레임도 소수 한 자리, 마지막은 정확히 목표값 (Task 3 `test_count_text`).

---

### Task 1: 윤 반장 캐릭터 시트와 바이블

**Files:** Create `banjang/BIBLE.md`

**Interfaces:** Produces 시트 job id(이후 모든 윤 반장 컷의 `image_references`), 인물 묘사 문구 `YOON`(프롬프트에 그대로 붙임).

- [ ] **Step 1:** 시안 job `429e0370-b3f8-4a50-a89c-792d3b761056`을 참고로 시트 2장 생성: ① 전신 정면·옆·뒤 ② 표정·동작 6종(무표정, 한쪽 입꼬리, 눈썹 들기, 팔짱, 가리키기, 손바닥 펴서 멈춤). 인물: 30대 후반 여성, 짧은 검은 머리, 청록 작업 조끼, 걷은 소매, 로고·명찰 없음.
- [ ] **Step 2:** `sandbox_exec` `image_paths`로 직접 보고 두 장의 얼굴·옷이 같은지 확인. 다르면 한 장만 다시(최대 2회).
- [ ] **Step 3:** `BIBLE.md`: 시트 job id, `YOON` 문구, 말투 규칙(존댓말, 짧고 건조, 문장당 15자 안팎, 툭 던지는 농담 한 줄, 겁주지 않음, "사지 마세요"도 말함), 금지 표현, 그림 공통 문구, 잉크 색값.
- [ ] **Step 4:** 커밋 `윤 반장 캐릭터 시트와 바이블`.

### Task 2: 목소리 고르기

**Files:** Modify `banjang/BIBLE.md`(목소리 절)

- [ ] **Step 1:** `text2speech_v2` elevenlabs 프리셋에서 한국어가 되는 차분한 30~40대 여성 목소리 4개를 고른다.
- [ ] **Step 2:** 같은 문장 "그 가방, 메고 계단 12층 내려가 보셨어요? 11.4킬로입니다."로 4개 녹음(약 1.2크레딧).
- [ ] **Step 3:** faster-whisper 받아쓰기 일치율 표 + 네 파일 링크를 **사용자에게 보여 주고 고르게 한다**. 답을 받기 전엔 Task 5로 넘어가지 않는다(Task 3·4는 병행).
- [ ] **Step 4:** voice_id, silenceremove 설정, 배속을 `BIBLE.md`에 적고 커밋.

### Task 3: 리소그래프 그래픽 모듈

**Files:** Create `banjang/graphics.py`; Test `banjang/test_graphics.py`(assert 기반, `python3 banjang/test_graphics.py`)

**Interfaces — Produces:**
- `INK = {"orange": (255,106,19), "teal": (14,124,123), "paper": (243,238,226), "ink": (30,42,42)}`
- `riso(img: Image.Image, seed: int) -> Image.Image` — 망점·종이결·청록 레이어 어긋남.
- `fit_text(text: str, font_path: str, max_w: int, start: int, min_size: int) -> tuple[list[str], int]`
- `count_text(value: float, t: float) -> str` — 소수 자릿수는 value를 따른다.
- `bars_frame(items: list[tuple[str, float]], t: float, unit: str, seed: int) -> Image.Image` — 위에서부터 차례로 자라는 가로 막대 + 라벨 + 값.
- `scale_frame(value: float, t: float, unit: str, seed: int) -> Image.Image` — 저울 바늘 0→value, 가운데 큰 숫자 카운트업.
- `checklist_frame(items: list[str], t: float, marks: list[str], seed: int) -> Image.Image` — marks "o"/"x", 하나씩 나타남.
- 모든 frame 함수: 1080×1920 RGB, 종이 배경, 그래픽은 안전 영역 안. t∈[0,1].

- [ ] **Step 1: 실패하는 테스트**
```python
def test_count_text():
    assert count_text(11.4, 1.0) == "11.4"
    assert count_text(11.4, 0.0) == "0.0"
    assert count_text(500, 0.5) == "250"
def test_bars_min_visible():
    im = bars_frame([("생수", 6.0), ("랜턴", 0.0), ("라디오", 0.06)], 1.0, "kg", 1)
    assert im.size == (1080, 1920)
    assert orange_width_in_row(im, row_of("랜턴")) >= 8 and orange_width_in_row(im, row_of("라디오")) >= 8
def test_bars_t0_empty():
    assert orange_pixels(bars_frame([("생수", 6.0)], 0.0, "kg", 1), BAR_AREA) == 0
def test_fit_text_long_korean():
    lines, size = fit_text("재난가방 공식 목록대로 전부 넣으면 몇 킬로그램일까요", BHS, 900, 120, 60)
    assert size >= 60 and all(text_w(l, size) <= 900 for l in lines)
def test_riso_palette():
    assert all(near_ink_mix(c, 40) for c in top_colors(riso(sample_art(), 1), 6))
def test_safe_area():
    for im in (scale_frame(11.4, 1.0, "kg", 1), checklist_frame(["a","b"], 1.0, ["o","x"], 1)):
        x0, y0, x1, y1 = non_paper_bbox(im)
        assert x0 >= 90 and x1 <= 990 and y0 >= 240 and y1 <= 1500
```
(헬퍼 `orange_width_in_row`, `row_of`, `orange_pixels`, `BAR_AREA`, `text_w`, `near_ink_mix`, `top_colors`, `sample_art`, `non_paper_bbox`는 테스트 파일 안에 둔다. `bars_frame`은 행 위치를 알 수 있게 `BAR_TOP=420`, `BAR_ROW=130` 상수를 graphics.py에 노출.)
- [ ] **Step 2:** sandbox에서 실행 → 실패(모듈 없음) 확인.
- [ ] **Step 3:** 구현. numpy로 종이결 노이즈(seed 고정), 채움 영역에만 6px 망점, 청록 레이어를 (+3,−2)px 어긋나게 곱하기 합성. 글자는 먹색 단색(망점 없음).
- [ ] **Step 4:** 통과 확인. 세 frame의 t=1 이미지를 시트로 만들어 직접 보고 시안 2번과 같은 인쇄물 느낌인지 판단, 아니면 질감 값 조정.
- [ ] **Step 5:** 커밋 `리소그래프 정보 그래픽 모듈`.

### Task 4: 장면 JSON → 영상 렌더러

**Files:** Create `banjang/render.py`, `banjang/test_render.py`, `banjang/episodes/_sample.json`(3장면)

**Interfaces:**
- Consumes: Task 3 함수 전부.
- Produces: 설계도 형식
```json
{"title": "...", "voice": {"voice_id": "...", "speed": 1.25},
 "scenes": [
  {"type": "art", "image": "b001_01", "title": "몇 kg일까?", "say": "자막", "tts": "녹음용(선택)"},
  {"type": "scale", "value": 11.4, "unit": "kg", "title": "...", "say": "..."},
  {"type": "bars", "items": [["생수 2L 3병", 6.0]], "unit": "kg", "title": "...", "say": "..."},
  {"type": "list", "items": ["..."], "marks": ["x"], "title": "...", "say": "..."}
 ]}
```
  - 장면당 음성 하나 `assets/aud/<n>.mp3`(1부터), 그림 `assets/cut/<image>.png`.
  - `check(spec: dict, assets: str) -> list[str]` 빠진 상대 경로 목록.
  - `plan(spec: dict, durations: list[float]) -> list[float]` 장면 시작 시각. 장면 길이 = 원음 길이 / speed, 장면 사이 0.25초.
  - 그래픽 장면 t: 장면 앞 70% 동안 ease-out 0→1, 이후 정지. art 장면: 1.00→1.06 느린 확대, 제목 위.
  - 자막: y 1500~1700, Noto Sans KR 52, 먹색 상자에 종이색 글자.
  - CLI: `python3 banjang/render.py banjang/episodes/b001.json --assets assets --out b001.mp4`
- [ ] **Step 1: 실패하는 테스트**
```python
def test_check_missing_audio():
    assert check(SAMPLE, assets_with_aud(1, 2)) == ["aud/3.mp3"]
def test_plan_starts():
    assert plan(SAMPLE, [2.5, 5.0, 2.5]) == [0.0, 2.25, 6.5]   # speed 1.25: 2.0, 4.0, 2.0 + 0.25 간격
def test_long_warning():
    # 총 길이 > 45초면 stderr에 "45초 초과", 예외 없음
```
- [ ] **Step 2:** 실패 확인.
- [ ] **Step 3:** 구현. Pillow 프레임 → ffmpeg stdin(rawvideo, 30fps). 음성은 장면별 `silenceremove=stop_periods=-1:stop_duration=0.45:stop_threshold=-38dB:stop_silence=0.3` → `atempo=speed` → 0.25초 간격 이어 붙임. 배경음 없음.
- [ ] **Step 4:** 통과. `_sample.json`을 실제 렌더(Task 2 전이면 Holden으로 3줄, 약 0.9크레딧, 그림은 시안 재사용) → 프레임 6장 시트를 직접 확인.
- [ ] **Step 5:** 커밋 `윤 반장 렌더러`.

### Task 5: 첫 편 「재난가방 공식 목록대로 싸면 몇 kg?」

**Files:** Create `banjang/episodes/b001.json`, `banjang/episodes/b001.md`

- [ ] **Step 1: 사실 확인.** 국민재난안전포털·행정안전부 비상용 물품 목록 원문을 PC에서 `curl`로 받아 읽는다. 항목별 대표 제품(판매 상위 일반 제품) 무게를 스펙에서 찾아 링크와 함께 표로. 수량이 없는 항목은 가정을 명시. 합계는 계산값 그대로(11.4가 아니어도).
- [ ] **Step 2: 대본.** 6~8장면, 한국어 내레이션 180자 안쪽. 물건+숫자 질문 → 답 먼저 → 무게 순위 막대 → 줄이는 법 3가지(구체 물건) → 저장·공유 유도(제휴 링크 없음). 말투는 BIBLE.md. 훅 3개를 영어로 옮겨 `.claude/skills/ig-reel/hookscore.py`로 채점, `short-form-video` 스킬로 첫 3초·컷 속도 점검, 결과를 `b001.md`에.
- [ ] **Step 3:** 그림 3~4장(윤 반장 2, 물건 1~2) 생성, 직접 보고 판단.
- [ ] **Step 4:** 목소리 생성 → verify(`stickman_survival/pipeline/verify.py` 방식) → 렌더 → 프레임 시트 확인 → 표지(graphics.py로 그린 큰 숫자 + 윤 반장 그림).
- [ ] **Step 5:** ZIP·표지 업로드(PUT에 `If-None-Match: *`), 프로젝트 attach.
- [ ] **Step 6:** 노션 보드 새 행(`화`: `윤 반장 1 — <제목>`, 상태 `업로드 대기`)과 본문(링크, 캡션은 `social` 스킬 + `.claude/skills/ig-caption/caption.py` 점검, "대표 제품 스펙 기준", 해시태그 `#재난가방 #비상가방 #재난대비 #민방위` + 1개, 사실 확인 표). 보드에 "윤 반장" 보기(화가 "윤 반장"으로 시작하는 행) 추가.
- [ ] **Step 7:** 실제 사용 크레딧을 `b001.md`에, 커밋·push `윤 반장 1편`.

### Task 6: 계정 개편 안내와 문서 정리

**Files:** Create `banjang/RUNBOOK.md`; Modify `stickman_survival/pipeline/HANDOVER.md`(맨 위)

- [ ] **Step 1:** 프로필 사진(윤 반장 얼굴, 리소, 정사각) 1장 생성.
- [ ] **Step 2:** 이름 칸·소개글 3안, 아이디 후보 3개를 `social` 스킬로 쓰고 1편 노션 행 맨 위 콜아웃에(사용자가 직접 바꾸는 순서와 기존 22편 보관 방법 포함).
- [ ] **Step 3:** `banjang/RUNBOOK.md`(주제 기준 → 사실 확인 → 대본 → 그림 → 목소리 → verify → 렌더 → 검수 → 업로드 → 노션, 비용, 1편에서 배운 것). HANDOVER 맨 위에 "개편: `banjang/RUNBOOK.md`부터 읽는다".
- [ ] **Step 4:** 커밋·push `윤 반장 RUNBOOK, 핸드오버 갱신`.
