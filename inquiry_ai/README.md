# Inquiry AI 자동 처리 시스템 (프로토타입)

이 프로젝트는 포스코 홈페이지 문의를 **다국어 번역 → 문의 유형 분류 → 중요도/우선순위 판단 → 담당 부서 라우팅 → 초안 답변 생성**까지 자동화하는 흐름의 **프로토타입 스켈레톤**입니다.

## 목표(명세 기반)
- 자동 처리율 `85%+`
- 유형 분류 정확도 `90%+`
- 평균 대응 시간 `5시간 이내` 단축

> 현재 코드는 LLM을 실제로 호출하지 않고, 규칙 기반(mock) 로직으로 동작합니다. `LLMClient` 인터페이스를 교체하면 실제 LLM 연동이 가능합니다.

## 폴더 구조(핵심)
- `backend/` : FastAPI API 서버
- `dashboard/` : Streamlit 대시보드(테스트/시각화)
- `data/` : FAQ 및 샘플 입력 데이터

## 실행 방법

### 1) 가상환경 생성/설치
```bash
cd inquiry_ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 백엔드 실행
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) 대시보드 실행
```bash
streamlit run dashboard.py --server.port 8501
```

## API 예시
### 문의 분석 요청
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"content":"안녕하세요. 채용 관련 문의드립니다. 지원서 제출 방법은 어떻게 되나요?"}'
```

## 환경 변수(선택)
- 추후 실제 LLM 연동 시 `OPENAI_API_KEY` 등의 변수를 사용하도록 `LLMClient` 확장 지점을 마련해두었습니다.

