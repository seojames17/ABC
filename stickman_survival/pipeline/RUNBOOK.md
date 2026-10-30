# 「1203호」 에피소드 제작 파이프라인

에피소드 하나 = 설계도 파일 하나 (`episodes/sNNeNN.json`). 이 문서는 사람이든 자동 실행되는 Claude든 같은 순서로 따라 하는 작업 지침이다.

## 전체 흐름

```
① 대본·설계도 작성  →  ② 그림 생성  →  ③ 내레이션 생성(ko, en)  →  ④ 음성 검증  →  ⑤ 렌더링(ko, en)
   (Claude)            (Higgsfield)      (Higgsfield)                (verify.py)       (render.py)
→  ⑥ 프레임 검수  →  ⑦ Higgsfield 프로젝트 「1203호 생존툰」에 저장  →  ⑧ 사람에게 검토 요청 (업로드는 사람이)
```

①~⑦은 자동, ⑧은 노션 「1203호 업로드 보드」에 올리는 것까지 자동. 인스타 업로드와 투표 결과·조회수 입력은 사람이 한다.

## 자동 실행 방식 (매일 17:47 KST, 승인 없이 끝까지)

매일 한 화씩 올린다. 사람은 저녁에 올리고, 다음 날 17시 전까지 노션에 투표 결과를 고른다. 17:47에 예약 작업이 새 세션을 띄워 다음 화를 끝까지 만든다.

1. 저장소 `seojames17/ABC`의 `claude/stickman-survival` 브랜치를 받고 이 문서와 `SERIES.md`를 읽는다.
2. 노션 보드(data source `collection://c273277b-4c03-4d91-b726-1945fa4f2367`)를 조회한다.
   - 상태가 "업로드 대기" 또는 "제작 중"인 행이 하나라도 있으면 사람이 아직 올리지 않은 것이다. 새로 만들지 말고 멈춘다(크레딧 낭비, 투표 없는 화가 연달아 나오는 것 방지). 그래서 사람은 올린 뒤 꼭 "게시 완료"로 바꿔야 다음 화가 만들어진다.
   - 가장 최근 화의 **투표 결과**를 읽는다. 비어 있으면 이야기상 더 좋은 쪽을 고르되, 영상에서 "여러분의 선택"이라고 하지 말고 "민수의 선택"이라고 하고, 노션 행의 **갈래**에 "투표 없음"을 적는다.
   - 지난 화들의 조회수·스킵률이 적혀 있으면 참고한다(스킵률이 높으면 첫 2초를 더 세게).
3. Higgsfield 크레딧을 확인한다. 40 미만이면 만들지 말고 노션에 상태 "확인 필요" 행을 만들어 이유를 적는다.
4. 노션에 새 행을 상태 "제작 중"으로 먼저 만든다(제목, DAY, 갈래).
5. ① 다음 화 설계도는 **고른 갈래 하나만** 쓴다(투표 결과를 이미 알고 있으므로 두 갈래를 쓰지 않는다). 그 화의 A/B 질문은 두 선택지가 다음 화를 실제로 바꾸도록 설계하고, 갈래별 결과 계획을 `episodes/sNNeNN.md`에 적어 둔다.
6. ②~⑦을 진행한다. 사람 승인을 기다리지 않는다. 사실 확인에서 확신도 "낮음"인 지식은 쓰지 않는다.
7. ⑧ 노션 행을 채우고 상태를 "업로드 대기"로 바꾼다. 형식은 보드의 2화 페이지를 그대로 따른다.
8. `SERIES.md`(상태 표·화별 기록)와 설계도·설명서를 커밋·푸시한다.
9. 중간에 막히면(생성 실패 반복, 검증 계속 실패 등) 노션 행 상태를 "확인 필요"로 바꾸고 메모에 어디서 막혔는지 적은 뒤 끝낸다.

## 작업 서버 준비 (Higgsfield sandbox_exec)

작업 서버는 초기화될 수 있다(2화 다음 날 실제로 모든 파일이 사라졌다). 매번 `ls ~/pipe/render.py`로 확인하고 없으면 아래를 그대로 실행한다. 저장소가 공개라 작업 서버에서 GitHub에서 바로 받을 수 있다.

```
R=https://raw.githubusercontent.com/seojames17/ABC/claude/stickman-survival/stickman_survival
mkdir -p ~/pipe/episodes ~/pipe/assets/cut ~/pipe/assets/aud/ko ~/pipe/assets/aud/en ~/pipe/assets/fonts
cd ~/pipe && curl -sf -O $R/pipeline/render.py && curl -sf -O $R/pipeline/verify.py && curl -sf -o make_sfx.sh $R/tools/make_sfx.sh
cd assets/fonts
curl -sfL -o NotoSansKR.ttf "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
curl -sfL -o BlackHanSans.ttf "https://github.com/google/fonts/raw/main/ofl/blackhansans/BlackHanSans-Regular.ttf"
cd .. && bash ../make_sfx.sh       # assets/sfx/*.wav 생성
```

- 설계도도 푸시한 뒤 `curl -sf -o episodes/sNNeNN.json $R/pipeline/episodes/sNNeNN.json`으로 받는다. 스크립트를 고쳤으면 먼저 푸시하고 다시 받는다.
- 이전 화 컷을 재사용할 때는 `jobs_wait`(timeout 0)에 그 job id를 넣어 `result_url`을 얻고 `curl`로 `assets/cut/<컷 이름>.png`에 받는다.
- 작업 서버로 파일을 base64로 넘기면 거부된다. 위처럼 URL에서 받는다.

## ① 설계도 작성 규칙

- 형식은 `episodes/s01e01.json` 참고. 장면(scenes) → 비트(beats). 비트 하나 = 컷 하나.
- 비트의 `ko`/`en`은 **그 컷이 나오는 동안 말하는 대사 조각**. 장면 내레이션은 비트 대사를 이어 붙인 것.
- `cont: true`면 앞 비트 자막에 이어 붙여 글자가 늘어난다(말하는 대로 자막이 차오름).
- 한 장면 3~5컷, 컷당 0.5~2.5초가 되도록 대사를 쪼갠다. 전신 / 손·물건 클로즈업 / 표정 클로즈업을 섞는다.
- 매화 구조: 위기 → 민수의 실수 → **진짜 생존 지식**(할머니가 알고 있음) → 생존 점수 → A/B 질문 → 다음 화 예고
- 금지: 피·잔혹 묘사, 실존 작품 설정 모방, 비니·모자 캐릭터(Beanie Survives와 구분)
- 생존 지식은 **"오, 몰랐네"가 나오는 것**만 쓴다. "휴대폰 손전등은 배터리를 먹는다"처럼 누구나 아는 건 금지. 기준: ① 시청자 절반 이상이 모를 것 ② 이유(왜 그런지)를 한 문장으로 붙일 것 ③ 바로 따라 할 수 있는 행동이 있을 것.
- 생존 지식마다 사실 확인 표를 `episodes/sNNeNN.md`에 남긴다. 확신도 "중간" 이하가 있으면 ⑧에서 사람에게 꼭 알린다.
- **A/B 투표는 진짜 갈림길이어야 한다.** 다음 화에서 고른 쪽에 따라 최소 세 가지가 달라진다:
  1. 시작 상황 (첫 30% 안에 "여러분의 선택: A" 화면과 그 결과가 보일 것)
  2. 그 갈래에서만 배우는 생존 지식 한 가지
  3. 자원(`SERIES.md`의 상태 표: 배터리, 현금, 물, 빚, 관계)과 생존 점수
- 두 선택지 모두 그럴듯하고 득실이 있어야 한다(한쪽이 뻔한 정답이면 투표할 이유가 없음).
- 매일 자동 실행에서는 투표 결과를 이미 알고 쓰므로 **고른 갈래만** 쓴다.
- 결과가 나오기 전에 미리 쓸 때만 두 갈래를 모두 쓰고 장면에 `"vote": "A"|"B"`를 단다. 갈래와 무관한 장면은 공통. 배터리를 갈래에 따라 바꾸려면 공통 장면에 `"battery": "vote"`. 렌더링 때 `--vote A`로 그 갈래만 만든다.
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

FAIL 장면만 다시 녹음하고 다시 검증한다. AI 음성은 가끔 문장 앞뒤에 알아들을 수 없는 소리를 붙이거나, 첫 문장을 빼먹거나, 긴 정적을 만든다.
- 녹음용 텍스트에서는 따옴표를 빼고 쉼표로 이어 쓴다. 따옴표로 나뉜 두 문장 사이에 4초 정적이 생기거나(2화 영어 3번) 따옴표 앞 문장이 통째로 빠진 적이 있다(2화 한국어 3번). 자막에는 따옴표를 그대로 둬도 된다.
- verify가 ok여도 받아쓴 문장을 눈으로 한 번 읽는다. 첫머리 누락·끝 잡음은 유사도만으로는 못 잡을 때가 있다.

## ⑤ 렌더링

```
bash ../tools/make_sfx.sh            # 처음 한 번 (assets/sfx 생성)
python3 render.py episodes/sNNeNN.json --lang ko --assets assets --out sNNeNN_ko.mp4
python3 render.py episodes/sNNeNN.json --lang en --assets assets --out sNNeNN_en.mp4
```

- 영상이 70초를 넘으면 설계도에 `"speed": {"ko": 1.12}`처럼 내레이션 배속을 준다(음높이 유지). 2화 한국어는 1.12배.

컷 전환 시점은 내레이션을 받아 적은 단어 타이밍으로 자동 계산된다. Higgsfield `sandbox_exec`(ffmpeg, faster-whisper 설치됨)에서 실행한다. 폰트는 `assets/fonts/`에 Black Han Sans, Noto Sans KR.

## ⑥ 프레임 검수

장면마다 프레임을 1장씩 뽑아 직접 본다: 캐릭터 일관성(빨간 후드·안경 / 겨자색 카디건), 그림 속 엉뚱한 글자, 자막·강조 문구가 그림의 중요한 부분을 가리는지. 문제 컷만 다시 생성한다.

## ⑦ 저장

`media_upload` → `media_confirm` → `attach_project_asset`으로 「1203호 생존툰」 프로젝트(`8b843777-b07f-43f6-8e0f-87d3adbb477e`, workspace `f1357b6e-9e22-4f9c-a4e4-034f8e6683cb`)에 두 영상을 넣는다.

## ⑧ 사람에게 넘기기

**커버 이미지도 만들어 준다.** 맨 위에 빨간 배지 "1203호 N화", 가장 크게 노란 "정전 N일째", 그 아래 흰색으로 그 화의 갈고리 한 줄(예: "라면 10봉지의 최후"). 시리즈의 축은 "정전 며칠째"이므로 표지에서 그게 먼저 보여야 한다. 글자는 프로필 격자(가운데 3:4, y 240~1680) 안에 둔다.

**아이폰으로 받을 수 있게 ZIP 링크를 함께 준다.** 영상(mp4) 링크는 사파리·크롬에서 재생만 되고 저장이 안 되며, 업로드한 영상은 Higgsfield 앱 화면에도 보이지 않는다. 작업 서버에서 `zip -0 sNNeNN_ko.zip sNNeNN_ko.mp4`로 감싼 뒤 `media_upload`(파일명 .zip, `source_type: file_input`) → PUT → `media_confirm`(type file)으로 올리고, 그 cloudfront 주소를 준다. 사파리에서 열면 다운로드 → 파일 앱에서 ZIP을 눌러 풀기 → 영상 공유 → "비디오 저장".


커버 이미지는 `media_upload`(image/jpeg) → PUT → `media_confirm`(type image)으로 올린다. jpg 링크는 아이폰 사파리에서 길게 눌러 사진 앱에 저장할 수 있다.

**노션 보드 행 채우기** (2화 페이지 `https://app.notion.com/p/409295818b0e811680fdc1b192a8a881`과 같은 형식)
- 속성: 화(`N화 — 정전 N일째: 부제`), 게시일(오늘), 상태(업로드 대기), DAY, 갈래, 영상 한국어(ZIP), 영상 영어(ZIP), 표지(jpg), 다음 투표(A/B 질문 한 줄), 생존 점수, 메모(길이, 사용 크레딧, 특이사항)
- 본문: 맨 위 노란 콜아웃(게시 후 할 일) → 1. 영상·표지 받기(링크 + 표지 이미지) → 2. 캡션(한국어, 복사용 코드 블록) → 3. 첫 댓글 → 4. 스토리 투표 → 5. 올릴 때 체크(음악 X, 커버, AI 레이블, 고정 댓글) → 6. 사실 확인(확신도 중간 이하만) → 7. 영어 캡션
- 해시태그는 5개(`#1203호 #정전 #재난대비 #생존꿀팁 #생존툰`, 영어는 `#unit1203 #blackout #survivaltips #emergencyprep #stickman`).

## 비용 기준 (1화 실측)

그림 약 35컷 ≈ 18크레딧, 음성 20줄 ≈ 4크레딧, 재녹음 몇 줄 ≈ 1크레딧 → **화당 약 23크레딧**. 2화 실측은 26.7(그림 25장, 음성 26줄). 새 화 예상은 25~30으로 잡는다.
