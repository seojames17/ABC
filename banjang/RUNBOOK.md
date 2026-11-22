# 윤 반장 RUNBOOK — 한 편 만드는 순서

새 세션은 이 파일 → `BIBLE.md` → 최근 `episodes/bNNN.md` 순으로 읽는다. 사용자에게는 한국어로 짧게 답한다. 설계: `docs/superpowers/specs/2026-11-22-yoon-banjang-redesign-design.md`. (민수 연재용 `stickman_survival/pipeline/RUNBOOK.md`는 더 쓰지 않는다.)

## 0. 작업 서버 준비 (Higgsfield `sandbox_exec`, 폴더 `~/bj`)
하루 넘게 쉬면 초기화된다. `ls ~/bj/render.py`가 없으면:
```
mkdir -p ~/bj/fonts ~/bj/episodes ~/bj/assets/aud ~/bj/assets/cut && cd ~/bj/fonts
curl -sfL -o BlackHanSans.ttf "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/blackhansans/BlackHanSans-Regular.ttf"
curl -sfL -o NotoSansKR.ttf "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
```
파일은 **커밋 SHA로 고정한 raw 주소**로 받는다(브랜치 이름은 캐시된 옛 파일이 오고, GitHub API는 시간당 60회 제한에 걸려 조용히 실패한다):
`curl -sf -o render.py "https://raw.githubusercontent.com/seojames17/ABC/<SHA>/banjang/render.py"` (graphics.py, test_*.py, episodes/bNNN.json 도 같은 방식). 받은 뒤 `grep`으로 새 내용이 들어왔는지 확인한다.

## 1. 주제 고르기
- "지금 누구에게 보낼 영상인가"가 바로 떠오를 것(7화 교훈). 숫자 하나와 상식 뒤집기 하나가 있을 것.
- 그 숫자가 **공식 원문**에 있거나, 공식 원문 숫자로 계산할 수 있을 것. 없으면 주제를 바꾼다(1편: "공식 목록대로 몇 kg?"은 한국 목록에 수량이 없어 "물 3일치 몇 kg?"으로 바꿈).
- 나중에 제휴(쿠팡 파트너스 승인 후): 영상에 나온 물건을 살 수 있는가도 본다.

## 2. 사실 확인
- 원문을 PC에서 `curl`로 받아 직접 읽는다(go.kr·hira.or.kr은 WebFetch가 시간 초과). 문구를 그대로 인용해 `bNNN.md` 표에 링크와 함께.
- 윤 반장의 조언(공식 문구가 아닌 것)은 `bNNN.md`와 캡션에 "조언"이라고 밝힌다.

## 3. 대본·설계도 (`episodes/bNNN.json`)
- 6장면 안팎, 한국어 내레이션 150~180자, 영상 20~40초. 장면 종류: `art`(그림+제목), `scale`(저울·큰 숫자), `bars`(막대 비교), `list`(O/X 체크리스트). 형식은 `render.py` 맨 위와 `episodes/b001.json`.
- 첫 장면에 답과 뒤집기를 먼저(1편 영어 훅 점수: 질문형 58 → 답+뒤집기 84). 훅 후보를 영어로 옮겨 `python .claude/skills/ig-reel/hookscore.py <파일>`.
- 매화 같은 구조를 반복하지 않는다. 끝은 "행동 하나"(들어 보기, 저장, 단톡방).
- `art` 장면은 그림 위쪽이 비어 있지 않으면 `"shift": 260~300`으로 그림을 내려 제목이 얼굴을 가리지 않게.
- 숫자는 `tts`에서 한글로 풀어 쓴다. 제목에 `·` `≈` `→` 금지.

## 4. 그림 (`gpt_image_2_5`, 9:16, medium, folder `8b843777-b07f-43f6-8e0f-87d3adbb477e`)
- 윤 반장 컷은 시트 두 장(`BIBLE.md`)을 `image_references`로, 프롬프트에 `YOON` 문구 + 그림 공통 문구 + "The top third of the image is empty plain paper".
- 한 편에 3~4장. 동시 4장까지 제출된다(5번째는 거절).
- 내려받아 `sandbox_exec` `image_paths`로 직접 본다.

## 5. 목소리
- Helena(`BIBLE.md`). 장면당 한 줄, 한 번에 3줄씩 제출(ElevenLabs 429 방지). `assets/aud/<장면 번호>.mp3`.
- faster-whisper로 받아써 눈으로 읽는다(숫자 표기 차이는 무시).

## 6. 렌더와 검수 (백그라운드 명령 하나로)
```
python3 test_graphics.py && python3 test_render.py
python3 render.py episodes/bNNN.json --assets assets --out bNNN.mp4
```
- 23초 영상에 약 2분. 프레임 시트(`fps=12/길이, tile=6x2`)를 직접 본다: 제목이 얼굴을 가리는지, 글자 잘림, 그림 속 글자.
- 표지: `render._art_frame(그림, 0, 제목, shift)`로 첫 장면을 저장.
- 업로드: `media_upload`(ZIP은 `source_type: file_input`, 표지는 image/jpeg) → 같은 명령 안에서 PUT(`If-None-Match: *`) → `media_confirm` → `attach_project_asset`.

## 7. 노션
- 보드 `collection://c273277b-4c03-4d91-b726-1945fa4f2367`. 화 `윤 반장 N — <제목>`, 상태 `업로드 대기`, 영상 한국어(ZIP)·표지 링크, 메모(길이, 크레딧). DAY·갈래·투표 결과·생존 점수는 비운다.
- 본문: 게시 후 할 일 → 영상·표지 → 캡션(코드 블록) → 첫 댓글 → 올릴 때 체크 → 사실 확인.
- 캡션은 `social` 스킬의 "No AI Tells"를 지킨다(대시, 한 줄씩 끊는 글, 자문자답 금지). 해시태그 `#재난가방 #비상가방 #재난대비 #민방위` + 주제 하나.

## 8. 커밋
`git -c user.name="James Seo" -c user.email="seojames17@users.noreply.github.com" commit`, 한국어, 끝에 Co-Authored-By. 브랜치 `claude/stickman-survival`. push 전 `git fetch` + rebase(다른 세션도 push함).

## 비용 (1편 실측)
그림 3장(1.5) + 목소리 6줄 + 재녹음 2줄(약 2.4) ≈ 화당 4~5크레딧. 준비 비용(시트 2, 목소리 후보 4, 샘플, 프로필) 약 4.
