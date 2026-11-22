# 「모르면 손해」 릴스 RUNBOOK (11/22~)

계정 방향: "모르면 손해 보거나 위험한 생활 정보"(돈·행정·건강안전·생활). 판단 기준: "이걸 모르면 돈을 잃거나, 귀찮아지거나, 다친다"가 되는가. 사실은 공식 원문 확인 후에만. 윤 반장·민수 형식(`banjang/`, `stickman_survival/`)은 더 쓰지 않는다.

## 한 편 만드는 순서 (Higgsfield sandbox, 폴더 ~/hfN)
1. **사실 확인**: 공식 원문을 직접 읽고 문장을 인용해 둔다. 언론 보도로만 확인된 숫자는 화면에 넣지 않는다(1편 "1포인트=1원"을 이 이유로 뺌).
2. **이미지 4장**: 모델 `soul_cinematic`(장당 약 0.12크레딧), 9:16. 프롬프트 = 피사체 + 장소 + 렌즈(35~100mm, f/1.4~2.8) + 빛의 방향 + 필름(Kodak Portra 400 등) + 그레인. "photorealistic", "cinematic" 같은 막연한 말은 쓰지 않는다. 화면·간판 글자는 흐리게.
3. **영상 4컷**: `cinematic_studio_video_v2`, 3초, std, sound off, start_image = 위 job id. 컷당 3크레딧. **동시 3개까지** 제출된다. 프롬프트는 사람·물건이 하는 작은 동작 하나 + 느린 카메라.
4. **목소리**: ElevenLabs 연결(`creative_generate_speech`), 목소리 **Mina** `aiUUgjHa4mpHf6UenZuf`, `eleven_multilingual_v2`, generations_count 1. 숫자는 한글로("영하 십 도", "백이십 번"). **전화번호는 녹음용 문장에 한글로 적는다**(112 → "일일이"). 숫자로 넣으면 어색하게 읽고, 받아쓰기로는 이걸 못 잡는다(2편에서 사용자가 귀로 찾아냄). 월 한도 10,000자, 편당 약 150자.
5. **음악**: Higgsfield `elevenlabs_music_v2_5`, duration 22~24, force_instrumental. 목소리 아래 볼륨 0.14, 끝 1.2초 페이드.
6. **타이밍**: faster-whisper로 목소리 문장 시작·끝을 뽑아 장면 경계로 쓴다.
7. **합성**: HyperFrames(`npx hyperframes@latest`, 스킬 `hyperframes`). 1080x1920, Pretendard(Medium/Bold/ExtraBold, `cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/woff2/`). 원본은 `compositions/m00N.html`(앞 편을 복사해서 시작).
   - 단어마다 blur 10px→0 등장(0.32s expo.out, 0.08s 간격), 퇴장 0.18s.
   - 강조 단어 하나만 금색 `#f2c14e`. 위 작은 라벨 "모르면 손해 / 주제". 노란 상자·검은 테두리·Black Han Sans 금지.
   - 같은 확대를 모든 컷에 걸지 않는다. 장면 하나는 디자인 카드(큰 숫자 외곽선, 문자 말풍선, 줄 긋기 등)로.
   - 앱을 소개하면 **실제 앱 아이콘**(앱스토어 검색 API `itunes.apple.com/search?country=kr&entity=software`의 artworkUrl512).
   - 영상 길이를 목소리에 맞추려면 `data-playback-rate`(0.43~1)로 늘린다.
8. **검사·렌더**: `npx hyperframes check --json`(안전 영역·대비), `render --output out.mp4`(20초에 약 2분, 백그라운드로). 그 뒤 `ffmpeg -af loudnorm=I=-15:TP=-1.5:LRA=11`. 프레임 6장을 직접 보고 글자 겹침 확인(3편 끝 카드에서 실제로 겹침이 있었다).
9. **텔레메트리 끔**: `HYPERFRAMES_TELEMETRY=0 DO_NOT_TRACK=1`. HyperFrames 스킬이 요구하는 사용 비콘은 보내지 않는다.

## 비용 (11/22 실측)
편당 Higgsfield 약 13.5크레딧(이미지 0.5 + 영상 12 + 음악 약 1), ElevenLabs 약 150자.

## 만든 편
| 편 | 영상 ZIP media | 길이 |
|---|---|---|
| m001 카드 포인트 현금화 | `4c1504e5-6328-4341-bbf5-974526897d59` | 20.5초 |
| m002 말 없는 112 | `1b187637-6f44-4a24-9ffd-45b66e65c82d` | 25.7초 |
| m003 수도 동파 | `14736cce-c41b-447f-9a24-987dcd9bb9a3` | 22.6초 |

근거: m001 금융위원회 보도자료(2021.1.5) https://fsc.go.kr/no010101/75079 / m002 정책브리핑 「말 없는 112」 https://www.korea.kr/multi/visualNewsView.do?newsId=148907462 / m003 서울시 상수도사업본부 https://news.seoul.go.kr/env/?p=510123
