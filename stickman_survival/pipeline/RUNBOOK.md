# 「1203호」 에피소드 제작 파이프라인

에피소드 하나 = 설계도 파일 하나 (`episodes/sNNeNN.json`). 이 문서는 사람이든 자동 실행되는 Claude든 같은 순서로 따라 하는 작업 지침이다.

## 전체 흐름

```
① 대본·설계도 작성  →  ② 그림 생성  →  ③ 내레이션 생성(ko, en)  →  ④ 음성 검증  →  ⑤ 렌더링(ko, en)
   (Claude)            (Higgsfield)      (Higgsfield)                (verify.py)       (render.py)
→  ⑥ 프레임 검수  →  ⑦ Higgsfield 프로젝트 「1203호 생존툰」에 저장  →  ⑧ 사람에게 검토 요청 (업로드는 사람이)
```

①~⑦은 자동, ⑧부터는 사람. 인스타 업로드는 API 계정 설정 전까지 사람이 한다.

## 자동 실행 방식 (주 2회, 대본 승인제)

1. 예약 작업이 새 세션을 띄운다. 세션은 `claude/stickman-survival` 브랜치를 받고 이 문서와 `SERIES.md`를 읽는다.
2. **①만 한다**: 다음 화 설계도(`episodes/sNNeNN.json`)와 설명서(`episodes/sNNeNN.md`: 줄거리, 컷 목록, 사실 확인 표, 게시 캡션 ko/en)를 쓰고 브랜치에 커밋·푸시한다.
3. 사용자에게 한국어로 대본 요약(두 갈래 모두)을 보여주고 **승인**과 **지난 화 A/B 투표 결과**를 묻는다. 승인 전에는 그림·음성을 만들지 않는다(크레딧 보호).
4. 승인(필요하면 수정 반영) 후 ②~⑦을 진행하고 ⑧로 보고한다. `SERIES.md`의 화별 기록을 갱신해 커밋·푸시한다.
5. Higgsfield 크레딧이 30 미만이면 제작을 시작하지 말고 사용자에게 알린다.

## 작업 서버 준비 (Higgsfield sandbox_exec)

작업 서버 파일은 24시간 지나면 사라질 수 있으니 매번 확인하고 없으면 다시 만든다.

```
mkdir -p ~/pipe/assets/{cut,sfx,fonts,aud/ko,aud/en} ~/pipe/episodes
cd ~/pipe/assets/fonts
curl -sfL -o NotoSansKR.ttf "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
curl -sfL -o BlackHanSans.ttf "https://github.com/google/fonts/raw/main/ofl/blackhansans/BlackHanSans-Regular.ttf"
```

`render.py`, `verify.py`, 설계도 JSON, `../tools/make_sfx.sh`는 저장소에서 읽어 heredoc으로 작업 서버에 쓴다(작업 서버는 비공개 저장소에 접근할 수 없음). 효과음은 `assets/` 안에서 `make_sfx.sh`를 실행하면 `assets/sfx/`에 생긴다. 이전 화 컷을 재사용할 때는 해당 job id의 결과 URL을 `curl`로 받는다.

## ① 설계도 작성 규칙

- 형식은 `episodes/s01e01.json` 참고. 장면(scenes) → 비트(beats). 비트 하나 = 컷 하나.
- 비트의 `ko`/`en`은 **그 컷이 나오는 동안 말하는 대사 조각**. 장면 내레이션은 비트 대사를 이어 붙인 것.
- `cont: true`면 앞 비트 자막에 이어 붙여 글자가 늘어난다(말하는 대로 자막이 차오름).
- 한 장면 3~5컷, 컷당 0.5~2.5초가 되도록 대사를 쪼갠다. 전신 / 손·물건 클로즈업 / 표정 클로즈업을 섞는다.
- 매화 구조: 위기 → 민수의 실수 → **진짜 생존 지식**(할머니가 알고 있음) → 생존 점수 → A/B 질문 → 다음 화 예고
- 금지: 피·잔혹 묘사, 실존 작품 설정 모방, 비니·모자 캐릭터(Beanie Survives와 구분)
- 생존 지식마다 사실 확인 표를 `episodes/sNNeNN.md`에 남긴다. 확신도 "중간" 이하가 있으면 ⑧에서 사람에게 꼭 알린다.
- **A/B 투표는 진짜 갈림길이어야 한다.** 다음 화에서 고른 쪽에 따라 최소 세 가지가 달라진다:
  1. 시작 상황 (첫 30% 안에 "여러분의 선택: A" 화면과 그 결과가 보일 것)
  2. 그 갈래에서만 배우는 생존 지식 한 가지
  3. 자원(`SERIES.md`의 상태 표: 배터리, 현금, 물, 빚, 관계)과 생존 점수
- 두 선택지 모두 그럴듯하고 득실이 있어야 한다(한쪽이 뻔한 정답이면 투표할 이유가 없음).
- 다음 화 설계도에는 두 갈래를 모두 쓰고 장면에 `"vote": "A"|"B"`를 단다. 갈래와 무관한 장면은 공통. 배터리를 갈래에 따라 바꾸려면 공통 장면에 `"battery": "vote"`.
- 투표 결과가 나오면 그 갈래만 그림·음성을 만든다(`verify.py`/`render.py`에 `--vote A`). 그래서 갈래를 크게 벌려도 비용은 거의 늘지 않는다.
- 숫자처럼 자막과 읽는 법이 다른 대사는 비트에 `"tts": {"ko": "..."}`로 녹음용 텍스트를 따로 적는다.
- 새 컷에는 비트에 그림 정보를 함께 적는다: `"prompt": "<영문 장면 묘사>"`, `"refs": ["<참고 job id>", ...]`. 이전 화 컷을 그대로 쓰면 `"reuse": "<job id>"`. 그림 생성 후 `"job": "<생성된 job id>"`를 채운다.

## ② 그림 생성 (Higgsfield `gpt_image_2_5`, 9:16, quality medium, 장당 0.5크레딧)

- 캐릭터 참고 이미지(`image_references`)
  - 민수: `719dd12e-5a62-4b7e-8824-e36ae4648f3c` (+ 포즈 시트 `406af5ab-9d83-4bb3-b115-bbb5e2c5c112`)
  - 할머니: `f3ea0e5e-c389-403b-a446-0bd473b0f738`
- 같은 공간의 컷은 그 공간의 첫 컷을 참고 이미지로 함께 넣어 배경을 유지한다.
- 프롬프트 공통: `Same simple thick black doodle style as the reference ... flat colors, no shading, vertical composition, no text, no letters, no watermark`
- 그림에 글자를 넣지 않는다. 숫자·문구는 설계도의 `key`/`draw`로 편집 단계에서 얹는다(빈 점수판, 빈 쪽지 등을 그리게 할 것).
- 한 번에 3장까지만 제출(그 이상은 429 속도 제한). 결과는 `assets/cut/<컷 이름>.png`로 내려받는다.
- `generate_*` 호출에 프로젝트 폴더 `folder_id`를 넘겨 「1203호 생존툰」 프로젝트에 쌓이게 한다.

## ③ 내레이션 (Higgsfield `seed_audio`, 목소리 Julian `95429266-c0ac-4137-a209-63b8812b0f23`)

- 장면마다 1개 파일. 한국어 `speech_rate: 20`, 영어 `speech_rate: 10`. 줄당 0.2크레딧.
- 숫자·약어는 소리 나는 대로 풀어 쓴다 ("4시간쯤" → "네 시간 정도", "DAY 3" → "데이 쓰리", "30" → "thirty").
- "…"는 2~4초 정적을 만들 수 있으니 녹음용 텍스트에서는 쉼표로 바꾼다(자막은 그대로 둬도 됨).
- 한 번에 3줄까지만 제출. `assets/aud/<lang>/<장면 번호>.mp3`로 저장.

## ④ 음성 검증 (필수)

```
python3 verify.py episodes/sNNeNN.json --lang ko --assets assets
python3 verify.py episodes/sNNeNN.json --lang en --assets assets
```

FAIL 장면만 다시 녹음하고 다시 검증한다. AI 음성은 가끔 문장 앞에 알아들을 수 없는 소리를 붙이거나 긴 정적을 만든다.

## ⑤ 렌더링

```
bash ../tools/make_sfx.sh            # 처음 한 번 (assets/sfx 생성)
python3 render.py episodes/sNNeNN.json --lang ko --assets assets --out sNNeNN_ko.mp4
python3 render.py episodes/sNNeNN.json --lang en --assets assets --out sNNeNN_en.mp4
```

컷 전환 시점은 내레이션을 받아 적은 단어 타이밍으로 자동 계산된다. Higgsfield `sandbox_exec`(ffmpeg, faster-whisper 설치됨)에서 실행한다. 폰트는 `assets/fonts/`에 Black Han Sans, Noto Sans KR.

## ⑥ 프레임 검수

장면마다 프레임을 1장씩 뽑아 직접 본다: 캐릭터 일관성(빨간 후드·안경 / 겨자색 카디건), 그림 속 엉뚱한 글자, 자막·강조 문구가 그림의 중요한 부분을 가리는지. 문제 컷만 다시 생성한다.

## ⑦ 저장

`media_upload` → `media_confirm` → `attach_project_asset`으로 「1203호 생존툰」 프로젝트(`8b843777-b07f-43f6-8e0f-87d3adbb477e`, workspace `f1357b6e-9e22-4f9c-a4e4-034f8e6683cb`)에 두 영상을 넣는다.

## ⑧ 사람에게 넘기기

다음을 정리해 보고한다: 두 영상 링크, 사실 확인 표(확신도 중간 이하 강조), 게시 캡션(ko/en), 커버로 쓸 컷, 사용 크레딧.

## 비용 기준 (1화 실측)

그림 약 35컷 ≈ 18크레딧, 음성 20줄 ≈ 4크레딧, 재녹음 몇 줄 ≈ 1크레딧 → **화당 약 23크레딧**.
