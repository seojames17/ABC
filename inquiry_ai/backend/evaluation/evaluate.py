from __future__ import annotations

import json
from pathlib import Path

from backend.schemas import InquiryRequest
from backend.services import FaqStore, InquiryProcessor


def main() -> None:
    base_dir = Path(__file__).resolve().parents[2]
    data_path = base_dir / "data" / "sample_inquiries.jsonl"
    faq_path = base_dir / "data" / "faq_store.json"

    processor = InquiryProcessor(faq_store=FaqStore(faq_path=faq_path))

    rows: list[dict] = []
    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    total = 0
    correct_category = 0
    correct_priority = 0

    for r in rows:
        req = InquiryRequest(
            message_id=r.get("message_id"),
            content=r["content"],
            source=r.get("source", "website_email"),
            language_hint=r.get("language_hint"),
        )
        expected_category = r.get("expected_category")
        expected_priority = r.get("expected_priority")

        pred = processor.process(req)

        total += 1
        if expected_category and pred.category == expected_category:
            correct_category += 1
        if expected_priority and pred.priority == expected_priority:
            correct_priority += 1

        print(
            f"- {req.message_id}: pred_category={pred.category}, expected_category={expected_category}, "
            f"pred_priority={pred.priority}, expected_priority={expected_priority}"
        )

    print("\n=== Summary ===")
    print(f"총 {total}건")
    print(f"카테고리 정확도: {correct_category}/{total} = {correct_category/total:.2%}")
    print(f"우선순위 정확도: {correct_priority}/{total} = {correct_priority/total:.2%}")


if __name__ == "__main__":
    main()

