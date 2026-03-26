from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


LanguageCode = Literal["ko", "en", "ja", "zh", "other"]


class InquiryRequest(BaseModel):
    message_id: Optional[str] = Field(default=None, description="원문 문의 ID(있다면)")
    content: str = Field(..., description="문의 원문(HTML 제거 후 텍스트 권장)")
    source: Optional[str] = Field(default="website_email", description="유입 경로(홈페이지/이메일 등)")
    language_hint: Optional[LanguageCode] = Field(
        default=None, description="언어를 알고 있으면 힌트로 전달(없으면 자동 추정)"
    )


class InquiryResponse(BaseModel):
    message_id: Optional[str] = None

    language: LanguageCode
    translated_text: str

    # 분류 결과(프로토타입에서는 규칙 기반)
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    priority: Literal["low", "high"]

    # 라우팅 결과
    route_department: str

    # 답변 초안/근거
    draft_answer: str
    faq_used: Optional[str] = None
    rationale: str

