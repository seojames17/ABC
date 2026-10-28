"""YouTube Data API v3에서 지역별 인기 급상승(mostPopular) 영상을 가져온다."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

API_BASE = "https://www.googleapis.com/youtube/v3"
_DURATION_RE = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


@dataclass
class Video:
    video_id: str
    region: str
    rank: int
    title: str
    channel: str
    category: str
    published_at: datetime
    duration_sec: int
    views: int
    likes: int
    comments: int
    tags: list[str] = field(default_factory=list)
    description: str = ""
    thumbnail: str = ""

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"

    @property
    def is_short(self) -> bool:
        # 쇼츠는 최대 3분까지 허용된다.
        return self.duration_sec <= 180

    def hours_since_publish(self, now: datetime) -> float:
        return max((now - self.published_at).total_seconds() / 3600, 1.0)

    def views_per_hour(self, now: datetime) -> float:
        return self.views / self.hours_since_publish(now)


def parse_duration(value: str) -> int:
    m = _DURATION_RE.fullmatch(value or "")
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def fetch_categories(api_key: str, region: str, hl: str = "ko") -> dict[str, str]:
    resp = requests.get(
        f"{API_BASE}/videoCategories",
        params={"part": "snippet", "regionCode": region, "hl": hl, "key": api_key},
        timeout=20,
    )
    resp.raise_for_status()
    return {item["id"]: item["snippet"]["title"] for item in resp.json().get("items", [])}


def fetch_trending(api_key: str, region: str, max_results: int = 50, hl: str = "ko") -> list[Video]:
    categories = fetch_categories(api_key, region, hl)
    resp = requests.get(
        f"{API_BASE}/videos",
        params={
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": min(max_results, 50),
            "hl": hl,
            "key": api_key,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return [_to_video(item, region, rank, categories) for rank, item in enumerate(resp.json().get("items", []), 1)]


def _to_video(item: dict, region: str, rank: int, categories: dict[str, str]) -> Video:
    sn = item.get("snippet", {})
    st = item.get("statistics", {})
    thumbs = sn.get("thumbnails", {})
    thumb = (thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
    return Video(
        video_id=item["id"],
        region=region,
        rank=rank,
        title=sn.get("localized", {}).get("title") or sn.get("title", ""),
        channel=sn.get("channelTitle", ""),
        category=categories.get(sn.get("categoryId", ""), "기타"),
        published_at=datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")).astimezone(timezone.utc),
        duration_sec=parse_duration(item.get("contentDetails", {}).get("duration", "")),
        views=int(st.get("viewCount", 0)),
        likes=int(st.get("likeCount", 0)),
        comments=int(st.get("commentCount", 0)),
        tags=sn.get("tags", [])[:15],
        description=(sn.get("description") or "")[:300],
        thumbnail=thumb,
    )
