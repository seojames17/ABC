from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.schemas import InquiryRequest, InquiryResponse
from backend.services import FaqStore, InquiryProcessor


app = FastAPI(title="Inquiry AI - Prototype", version="0.1.0")


_processor: InquiryProcessor | None = None


def _get_processor() -> InquiryProcessor:
    global _processor
    if _processor is None:
        faq_path = Path(__file__).resolve().parent.parent / "data" / "faq_store.json"
        faq_store = FaqStore(faq_path=faq_path)
        _processor = InquiryProcessor(faq_store=faq_store)
    return _processor


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=InquiryResponse)
def analyze(req: InquiryRequest) -> InquiryResponse:
    processor = _get_processor()
    return processor.process(req)


@app.post("/api/analyze_batch", response_model=list[InquiryResponse])
def analyze_batch(reqs: list[InquiryRequest]) -> list[InquiryResponse]:
    processor = _get_processor()
    return [processor.process(r) for r in reqs]

