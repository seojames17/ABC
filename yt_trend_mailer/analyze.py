"""수집한 인기 영상 목록에서 정량 트렌드 지표를 뽑는다."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from .youtube import Video

# 키워드 집계에서 제외할 흔한 단어
_STOPWORDS = {
    "the", "a", "an", "and", "of", "to", "in", "on", "for", "with", "is", "my", "i", "you",
    "official", "video", "mv", "ep", "shorts", "short", "full", "ver", "feat", "vs",
    "https", "http", "com", "www",
    "영상", "공식", "모음", "오늘", "그리고", "진짜", "이번", "우리", "있는", "하는",
}
_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]{2,}")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS and not t.isdigit()]


def analyze(videos: list[Video], now: datetime) -> dict:
    if not videos:
        return {"total": 0}

    categories = Counter(v.category for v in videos)
    channels = Counter(v.channel for v in videos)

    keywords: Counter[str] = Counter()
    for v in videos:
        # 한 영상이 같은 단어를 여러 번 써도 1회로 센다.
        keywords.update(set(_tokens(v.title)) | {t.lower() for t in v.tags})

    shorts = [v for v in videos if v.is_short]
    fresh = [v for v in videos if v.hours_since_publish(now) <= 24]

    # 같은 영상이 여러 지역 차트에 오르면 순위 목록에서는 한 번만 보여준다.
    unique: dict[str, Video] = {}
    regions_by_id: dict[str, list[str]] = {}
    for v in videos:
        unique.setdefault(v.video_id, v)
        regions_by_id.setdefault(v.video_id, []).append(v.region)
    global_hits = sorted(
        ((unique[vid], regs) for vid, regs in regions_by_id.items() if len(regs) > 1),
        key=lambda pair: (-len(pair[1]), -pair[0].views),
    )[:5]

    rising = sorted(unique.values(), key=lambda v: v.views_per_hour(now), reverse=True)[:5]
    engaging = sorted(
        (v for v in unique.values() if v.views >= 10_000),
        key=lambda v: (v.likes + v.comments) / v.views,
        reverse=True,
    )[:5]

    return {
        "total": len(videos),
        "regions": sorted({v.region for v in videos}),
        "categories": categories.most_common(8),
        "top_channels": [(c, n) for c, n in channels.most_common(5) if n > 1],
        "keywords": [(k, n) for k, n in keywords.most_common(20) if n > 1][:12],
        "shorts_ratio": len(shorts) / len(videos),
        "fresh_count": len(fresh),
        "avg_age_hours": sum(v.hours_since_publish(now) for v in videos) / len(videos),
        # 지역이 여러 개면 지역마다 상위 몇 개씩 고르게 담는다.
        "top": sorted(
            (v for v in videos if v.rank <= max(10 // len({v.region for v in videos}), 3)),
            key=lambda v: (v.region, v.rank),
        ),
        "global_hits": global_hits,
        "rising": rising,
        "engaging": engaging,
    }
