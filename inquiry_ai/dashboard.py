from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from backend.services import FaqStore, InquiryProcessor
from backend.schemas import InquiryRequest


@st.cache_data(ttl=60)
def load_processor() -> InquiryProcessor:
    base_dir = Path(__file__).resolve().parent
    faq_path = base_dir / "data" / "faq_store.json"
    return InquiryProcessor(faq_store=FaqStore(faq_path=faq_path))


st.set_page_config(page_title="Inquiry AI Dashboard", layout="wide")
st.title("Inquiry AI - 문의 자동 처리 프로토타입")
st.caption("규칙 기반(mock) 분류/라우팅/답변 초안 생성. LLM 연동 시 `backend/services.py`의 번역/분류 부분을 교체하세요.")

processor = load_processor()

with st.sidebar:
    st.header("입력")
    language_hint = st.selectbox(
        "언어 힌트(선택)",
        options=["auto", "ko", "en", "ja", "zh", "other"],
        index=0,
    )
    hint_val = None if language_hint == "auto" else language_hint

    st.markdown("---")
    st.subheader("샘플 데이터 배치 테스트")
    if st.button("샘플 6건 처리"):
        base_dir = Path(__file__).resolve().parent
        sample_path = base_dir / "data" / "sample_inquiries.jsonl"
        rows: list[dict[str, Any]] = []
        with sample_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))

        results = []
        for r in rows:
            req = InquiryRequest(
                message_id=r.get("message_id"),
                content=r["content"],
                source=r.get("source", "website_email"),
                language_hint=r.get("language_hint") or hint_val,
            )
            results.append(processor.process(req).model_dump())

        st.session_state["batch_results"] = results

if "batch_results" in st.session_state:
    st.subheader("배치 결과")
    st.json(st.session_state["batch_results"])
    st.markdown("---")

st.subheader("개별 문의 테스트")
content = st.text_area(
    "문의 내용을 입력하세요",
    placeholder="예: 안녕하세요. 환불 절차에 대해 문의드립니다. 긴급합니다.",
    height=160,
)

if st.button("분석/초안 생성"):
    if not content.strip():
        st.warning("문의 내용을 입력해 주세요.")
    else:
        req = InquiryRequest(content=content, language_hint=hint_val)
        resp = processor.process(req)
        st.subheader("결과")
        st.json(resp.model_dump())

