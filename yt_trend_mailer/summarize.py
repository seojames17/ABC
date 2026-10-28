"""Claude로 인기 영상 목록을 읽고 한국어 트렌드 브리핑을 만든다.

ANTHROPIC_API_KEY가 없거나 호출이 실패하면 통계만으로 만든 기본 요약을 쓴다.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime

from .youtube import Video

log = logging.getLogger(__name__)

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

SYSTEM_PROMPT = """당신은 유튜브 트렌드 애널리스트입니다. 매일 아침 바쁜 독자에게 보내는 \
이메일 브리핑을 씁니다. 주어진 '인기 급상승 영상' 목록과 통계만 근거로, 지금 사람들이 \
무엇에 관심을 쏟고 있는지 묶어서 설명하세요.

- 개별 영상 나열이 아니라, 여러 영상을 관통하는 흐름(테마)을 찾으세요.
- 근거가 되는 영상은 video_id로 연결하세요. 목록에 없는 id는 쓰지 마세요.
- 조회수 속도(views_per_hour), 업로드 후 경과 시간, 쇼츠 여부를 함께 고려하세요.
- 여러 지역 데이터가 있으면 지역별로 다른 관심사와, 여러 지역에서 동시에 뜬 흐름을 함께 짚으세요.
- 데이터로 확인되지 않는 사실(사건의 배경 등)은 단정하지 말고 '~로 보입니다'처럼 쓰세요.
- 모든 문장은 자연스러운 한국어로, 간결하게 씁니다."""

SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "오늘 트렌드를 한 줄로 요약한 메일 제목용 문구 (40자 이내)"},
        "summary": {"type": "string", "description": "전체 흐름 요약 3~4문장"},
        "themes": {
            "type": "array",
            "description": "오늘의 주요 테마 3~5개",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string", "description": "2~3문장 설명"},
                    "video_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "description", "video_ids"],
                "additionalProperties": False,
            },
        },
        "watch_picks": {
            "type": "array",
            "description": "오늘 꼭 볼 만한 영상 3개",
            "items": {
                "type": "object",
                "properties": {
                    "video_id": {"type": "string"},
                    "reason": {"type": "string", "description": "추천 이유 1문장"},
                },
                "required": ["video_id", "reason"],
                "additionalProperties": False,
            },
        },
        "outlook": {"type": "string", "description": "앞으로 며칠간 주목할 포인트 1~2문장"},
    },
    "required": ["headline", "summary", "themes", "watch_picks", "outlook"],
    "additionalProperties": False,
}


def _video_payload(videos: list[Video], now: datetime) -> list[dict]:
    return [
        {
            "video_id": v.video_id,
            "region": v.region,
            "rank": v.rank,
            "title": v.title,
            "channel": v.channel,
            "category": v.category,
            "views": v.views,
            "views_per_hour": round(v.views_per_hour(now)),
            "hours_since_publish": round(v.hours_since_publish(now), 1),
            "is_short": v.is_short,
            "likes": v.likes,
            "comments": v.comments,
            "tags": v.tags[:8],
            "description": v.description[:200],
        }
        for v in videos
    ]


def summarize(videos: list[Video], stats: dict, now: datetime) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.info("ANTHROPIC_API_KEY가 없어 통계 기반 요약을 사용합니다.")
        return fallback_summary(stats)
    try:
        return _summarize_with_claude(videos, stats, now)
    except Exception:  # 메일은 어떤 경우에도 나가야 하므로 요약 실패는 기본 요약으로 대체
        log.exception("Claude 요약 실패 - 통계 기반 요약으로 대체합니다.")
        return fallback_summary(stats)


def _summarize_with_claude(videos: list[Video], stats: dict, now: datetime) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    stats_payload = {
        "regions": stats["regions"],
        "categories": stats["categories"],
        "top_keywords": stats["keywords"],
        "shorts_ratio": round(stats["shorts_ratio"], 2),
        "uploaded_within_24h": stats["fresh_count"],
        "multi_region_hits": [{"video_id": v.video_id, "regions": regs} for v, regs in stats["global_hits"]],
    }
    user_content = (
        f"기준 시각(UTC): {now:%Y-%m-%d %H:%M}\n\n"
        f"## 통계\n{json.dumps(stats_payload, ensure_ascii=False)}\n\n"
        f"## 인기 급상승 영상\n{json.dumps(_video_payload(videos, now), ensure_ascii=False)}"
    )

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        # 안전 분류기가 요청을 거절하면 서버에서 다른 모델로 자동 재시도한다.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"요약 요청이 거절되었습니다: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("응답이 max_tokens에서 잘렸습니다.")

    text = next(b.text for b in response.content if b.type == "text")
    result = json.loads(text)
    known = {v.video_id for v in videos}
    for theme in result["themes"]:
        theme["video_ids"] = [vid for vid in theme["video_ids"] if vid in known]
    result["watch_picks"] = [p for p in result["watch_picks"] if p["video_id"] in known]
    result["generated_by"] = response.model
    return result


def fallback_summary(stats: dict) -> dict:
    cats = stats.get("categories", [])
    kws = [k for k, _ in stats.get("keywords", [])[:5]]
    top_cat = cats[0][0] if cats else "-"
    summary = (
        f"오늘 인기 영상 {stats.get('total', 0)}개 중 '{top_cat}' 카테고리가 가장 많았습니다. "
        f"쇼츠 비중은 {stats.get('shorts_ratio', 0):.0%}, 최근 24시간 내 업로드된 영상은 "
        f"{stats.get('fresh_count', 0)}개입니다."
    )
    if kws:
        summary += f" 자주 등장한 키워드는 {', '.join(kws)}입니다."
    return {
        "headline": f"오늘의 유튜브: {top_cat} 강세" + (f" · #{kws[0]}" if kws else ""),
        "summary": summary,
        "themes": [],
        "watch_picks": [{"video_id": v.video_id, "reason": "조회수 증가 속도 상위"} for v in stats.get("rising", [])[:3]],
        "outlook": "",
        "generated_by": "통계 기반 기본 요약",
    }
