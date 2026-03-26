from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.schemas import InquiryRequest, InquiryResponse


def _strip_html(text: str) -> str:
    # 매우 단순한 HTML 제거(프로토타입). 실제 서비스에서는 정규화 규칙을 강화하세요.
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_language(content: str, language_hint: Optional[str] = None) -> str:
    if language_hint:
        return language_hint

    if re.search(r"[가-힣]", content):
        return "ko"
    if re.search(r"[\u3040-\u30ff]", content):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", content):
        return "zh"
    # 라틴/기타 언어
    if re.search(r"[A-Za-z]", content):
        return "en"
    return "other"


def translate_if_needed(content: str, language: str) -> str:
    # 프로토타입에서는 번역을 mock으로 처리합니다.
    # 실제 연동 시: LLM/번역 API 결과를 이 함수에서 반환하도록 교체하세요.
    if language == "ko":
        return content
    return content


@dataclass
class FaqItem:
    question: str
    answer: str
    tags: list[str]


class FaqStore:
    def __init__(self, faq_path: Path) -> None:
        self.faq_path = faq_path
        self._items: list[FaqItem] = []
        self._idf: dict[str, float] = {}
        self._doc_tfidf: list[dict[str, float]] = []
        self._doc_norms: list[float] = []

        self._load()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        # 한국어/일본어/중국어/영문/숫자 토큰화(프로토타입)
        tokens = re.findall(r"[A-Za-z0-9]+|[\u3131-\u318E\uAC00-\uD7A3]+|[\u3040-\u30FF]+|[\u4E00-\u9FFF]+", text)
        # 소문자 통일
        return [t.lower() for t in tokens if t.strip()]

    def _load(self) -> None:
        if not self.faq_path.exists():
            # FAQ가 없으면 faq_used/answer_match이 항상 None이 되도록 합니다.
            self._items = []
            self._idf = {}
            self._doc_tfidf = []
            self._doc_norms = []
            return

        raw = json.loads(self.faq_path.read_text(encoding="utf-8"))
        items: list[FaqItem] = []
        for it in raw:
            items.append(
                FaqItem(
                    question=str(it["question"]),
                    answer=str(it["answer"]),
                    tags=list(it.get("tags", [])),
                )
            )
        self._items = items

        # 간단 TF-IDF(소규모 FAQ 기준) 계산
        # - N: 문서 수(=FAQ 수)
        # - df: 해당 토큰이 등장한 FAQ 개수
        doc_tokens: list[list[str]] = [self._tokenize(i.question) for i in self._items]
        n_docs = len(doc_tokens)

        df: dict[str, int] = {}
        for tokens in doc_tokens:
            for tok in set(tokens):
                df[tok] = df.get(tok, 0) + 1

        # idf = log((N+1)/(df+1)) + 1
        self._idf = {tok: float(np_log((n_docs + 1) / (count + 1)) + 1.0) for tok, count in df.items()}

        self._doc_tfidf = []
        self._doc_norms = []
        for tokens in doc_tokens:
            tf: dict[str, int] = {}
            for tok in tokens:
                tf[tok] = tf.get(tok, 0) + 1
            # tf-idf
            tfidf: dict[str, float] = {}
            for tok, c in tf.items():
                tfidf[tok] = (float(c) / float(len(tokens))) * self._idf.get(tok, 0.0)
            norm = float(sum(v * v for v in tfidf.values())) ** 0.5
            self._doc_tfidf.append(tfidf)
            self._doc_norms.append(norm)

    def find_best_answer(self, text: str, *, min_similarity: float = 0.25) -> tuple[Optional[str], Optional[str]]:
        if not self._items:
            return None, None

        q_tokens = self._tokenize(text)
        if not q_tokens:
            return None, None

        tf: dict[str, int] = {}
        for tok in q_tokens:
            tf[tok] = tf.get(tok, 0) + 1

        q_tfidf: dict[str, float] = {}
        for tok, c in tf.items():
            q_tfidf[tok] = (float(c) / float(len(q_tokens))) * self._idf.get(tok, 0.0)

        q_norm = float(sum(v * v for v in q_tfidf.values())) ** 0.5
        if q_norm == 0.0:
            return None, None

        best_idx: Optional[int] = None
        best_sim = 0.0

        for i, d_tfidf in enumerate(self._doc_tfidf):
            # dot product (only overlap terms)
            dot = 0.0
            for tok, qv in q_tfidf.items():
                dv = d_tfidf.get(tok)
                if dv is not None:
                    dot += qv * dv
            denom = q_norm * self._doc_norms[i] if self._doc_norms[i] != 0 else 0.0
            sim = (dot / denom) if denom else 0.0
            if sim > best_sim:
                best_sim = sim
                best_idx = i

        if best_idx is None or best_sim < min_similarity:
            return None, None

        item = self._items[int(best_idx)]
        return item.answer, item.question


def np_log(x: float) -> float:
    # numpy 없이 log를 쓰기 위한 얕은 래퍼
    import math

    return math.log(x)


def classify_and_route(text: str) -> tuple[str, float, str, str]:
    """
    Returns:
      (category, confidence, priority, route_department)
    """
    # 매우 단순한 룰 기반 분류(프로토타입)
    t = text.lower()

    # 고가치/긴급 신호(민원/불만/요청/분쟁 등)
    high_markers = [
        "불만",
        "항의",
        "민원",
        "사과",
        "소송",
        "분쟁",
        "환불",
        "지급",
        "해고",
        "차별",
        "위법",
        "요청",
        "긴급",
        "클레임",
        "dispute",
        "complaint",
        "refund",
        "urgent",
    ]
    is_high = any(m in text for m in high_markers)

    # 카테고리 마커
    rules: list[tuple[str, list[str], str]] = [
        ("채용/인사", ["채용", "지원", "면접", "이력서", "인턴", "recruit", "hiring"], "인사/채용 담당 부서"),
        ("투자/IR", ["투자", "ir", "주주", "공시", "배당", "shareholder", "investor"], "IR/투자정보 담당 부서"),
        ("법무/계약", ["계약", "법무", "변호", "소송", "계약서", "legal", "contract", "attorney"], "법무/컴플라이언스"),
        ("민원/불만", ["민원", "불만", "클레임", "항의", "refund", "complaint"], "포스코 커뮤니케이션실"),
        ("기타/일반정보", ["문의", "안내", "방법", "절차", "how", "policy"], "포스코 커뮤니케이션실"),
    ]

    scores: dict[str, int] = {r[0]: 0 for r in rules}
    for category, markers, _dept in rules:
        scores[category] = sum(1 for m in markers if m in text or m in t)

    category = max(scores.items(), key=lambda kv: kv[1])[0]
    score = scores[category]

    # confidence: 간단히 "매칭 마커 개수"로 치환
    confidence = min(0.95, 0.3 + 0.12 * score)

    priority = "high" if (is_high or category in {"법무/계약", "민원/불만"}) else "low"
    _, _, route_department = next(r for r in rules if r[0] == category)
    return category, confidence, priority, route_department


def generate_draft_answer(
    *,
    inquiry_text: str,
    language: str,
    category: str,
    priority: str,
    faq_answer: Optional[str],
    faq_used_question: Optional[str],
) -> tuple[str, Optional[str]]:
    if faq_answer:
        # FAQ가 매칭된 경우: 그대로 초안으로 사용
        return faq_answer, faq_used_question

    # FAQ가 없으면 템플릿 기반 초안을 생성
    if priority == "high":
        prefix = "우선, 불편을 드린 점에 대해 사과드리며 신속히 확인하겠습니다."
    else:
        prefix = "문의 주신 내용에 대해 아래와 같이 안내드립니다."

    if category == "채용/인사":
        body = "지원서 제출 절차/마감일/자격요건 등은 채용 공고 기준으로 안내드릴 수 있습니다. 공고 링크(또는 공고명)와 함께 문의해 주세요."
    elif category == "투자/IR":
        body = "투자/IR 관련 정보는 공시/보도자료/IR 자료를 기준으로 안내드릴 수 있습니다. 원하시는 자료 유형(예: 공시, 배당, 주주총회)을 알려주세요."
    elif category == "법무/계약":
        body = "법무/계약 관련 문의는 문서/사실관계를 확인한 후 담당 부서가 검토합니다. 계약명(또는 관련 문서/기간)을 구체적으로 요청드립니다."
    elif category == "민원/불만":
        body = "민원/불만 처리 시에는 발생 일시/채널/관련 주문/증빙이 필요할 수 있습니다. 가능한 정보를 함께 보내주시면 확인 절차를 진행하겠습니다."
    else:
        body = "추가로 확인이 필요한 항목이 있을 수 있어, 원하시는 목적(무엇을 신청/문의하시는지)을 조금 더 구체적으로 알려주시면 정확히 안내하겠습니다."

    if language == "ko":
        answer = f"{prefix}\n\n{body}"
    else:
        # 번역을 mock 처리하므로, 여기서는 '원문 언어' 그대로 제공(추후 실제 번역/다국어 답변으로 교체)
        answer = f"{prefix}\n\n{body}"

    return answer, None


class InquiryProcessor:
    def __init__(self, faq_store: FaqStore) -> None:
        self.faq_store = faq_store

    def process(self, req: InquiryRequest) -> InquiryResponse:
        cleaned = _strip_html(req.content)
        language = detect_language(cleaned, req.language_hint)
        translated = translate_if_needed(cleaned, language)

        category, confidence, priority, route_department = classify_and_route(translated)
        faq_answer, faq_used_q = self.faq_store.find_best_answer(translated)

        draft, faq_used = generate_draft_answer(
            inquiry_text=translated,
            language=language,
            category=category,
            priority=priority,
            faq_answer=faq_answer,
            faq_used_question=faq_used_q,
        )

        rationale = (
            f"언어={language}, 카테고리={category}(confidence={confidence:.2f}), "
            f"우선순위={priority}, FAQ 매칭={'있음' if faq_used else '없음'}"
        )

        return InquiryResponse(
            message_id=req.message_id,
            language=language,
            translated_text=translated,
            category=category,
            confidence=confidence,
            priority=priority,
            route_department=route_department,
            draft_answer=draft,
            faq_used=faq_used,
            rationale=rationale,
        )

