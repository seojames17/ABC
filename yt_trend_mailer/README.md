# 유튜브 트렌드 아침 브리핑 메일러

매일 아침 유튜브 **인기 급상승** 영상을 모아 트렌드를 분석하고, 한국어 브리핑 메일로 보내 줍니다.

```
YouTube Data API (mostPopular)  →  통계 분석  →  Claude 트렌드 요약  →  HTML 메일 (SMTP)
       youtube.py                 analyze.py      summarize.py          render.py / mailer.py
```

## 메일에 담기는 내용

- **헤드라인 + 전체 요약**: 오늘의 흐름을 3~4문장으로
- **트렌드 테마 3~5개**: 여러 영상을 관통하는 흐름과 근거 영상
- **오늘 볼 만한 영상 3개**와 추천 이유
- **숫자로 보는 오늘**: 카테고리 분포, 쇼츠 비중, 24시간 내 업로드 수, 자주 나온 키워드
- **가장 빠르게 뜨는 영상**: 업로드 후 시간당 조회수 기준 상위 5개
- **인기 급상승 상위** 목록, **앞으로 주목할 포인트**

`ANTHROPIC_API_KEY`가 없거나 요약 호출이 실패해도 통계 기반 요약으로 메일은 항상 발송됩니다.

## 준비물

| 항목 | 발급 방법 |
|---|---|
| `YOUTUBE_API_KEY` | Google Cloud Console → 프로젝트 생성 → *YouTube Data API v3* 사용 설정 → 사용자 인증 정보에서 API 키 생성 (무료 할당량으로 충분: 하루 약 2~4 유닛 사용) |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com 에서 발급 (선택) |
| `SMTP_USER` / `SMTP_PASSWORD` | Gmail 주소 + [앱 비밀번호](https://myaccount.google.com/apppasswords) (2단계 인증 필요, 일반 비밀번호 아님) |
| `MAIL_TO` | 받는 주소. 쉼표로 여러 명 가능 (생략 시 `SMTP_USER`) |

선택 설정: `REGIONS` (기본 `KR`, 예: `KR,US,JP`), `MAX_RESULTS` (지역당 최대 50), `CLAUDE_MODEL` (기본 `claude-opus-5-5`), `TIMEZONE` (기본 `Asia/Seoul`), `SMTP_HOST`/`SMTP_PORT` (기본 Gmail 465).

## 로컬에서 실행

```bash
pip install -r yt_trend_mailer/requirements.txt

# API 키 없이 샘플(가상) 데이터로 메일 모양 미리보기
python -m yt_trend_mailer --sample --dry-run --out preview.html

# 실제 데이터로 미리보기
export YOUTUBE_API_KEY=... ANTHROPIC_API_KEY=...
python -m yt_trend_mailer --dry-run

# 실제 발송
export SMTP_USER=you@gmail.com SMTP_PASSWORD=앱비밀번호 MAIL_TO=you@gmail.com
python -m yt_trend_mailer
```

## 매일 아침 자동 발송 (GitHub Actions)

`.github/workflows/yt-trend-mailer.yml`이 매일 **06:50 KST**에 실행됩니다.

1. 저장소 → Settings → Secrets and variables → Actions → **Secrets**에
   `YOUTUBE_API_KEY`, `ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_TO` 등록
2. (선택) **Variables**에 `REGIONS` 등록 (예: `KR,US`)
3. Actions 탭 → *YouTube 트렌드 아침 브리핑* → **Run workflow**로 바로 한 번 테스트

참고: 스케줄 워크플로는 기본 브랜치에 있어야 동작하고, 저장소에 60일간 활동이 없으면 GitHub가 자동으로 일시 중지합니다.

## Claude 호출 관련

- 모델: `claude-opus-5-5`, effort `medium`, 구조화 출력(JSON 스키마)으로 테마/추천을 받아 템플릿에 채웁니다.
- 안전 분류기가 요청을 거절하는 드문 경우를 위해 서버 측 대체 모델(`fallbacks: "default"`)을 켜 두었습니다.
- 하루 1회 호출(입력 약 1~2만 토큰)로 비용은 대략 하루 $0.1~0.2 수준입니다. 더 아끼려면 `CLAUDE_MODEL=claude-sonnet-5-5`.
