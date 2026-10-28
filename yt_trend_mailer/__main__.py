"""매일 아침 유튜브 트렌드 브리핑 메일을 만든다.

    python -m yt_trend_mailer                 # 수집 → 요약 → 메일 발송
    python -m yt_trend_mailer --dry-run       # 메일 대신 HTML 파일로 저장
    python -m yt_trend_mailer --sample --dry-run   # API 키 없이 샘플 데이터로 미리보기
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .analyze import analyze
from .mailer import send_mail
from .render import render
from .summarize import summarize
from .youtube import Video, _to_video, fetch_trending

SAMPLE_PATH = Path(__file__).with_name("sample_data.json")


def load_sample() -> tuple[list[Video], datetime]:
    data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    cats = data["categories"]
    videos = [_to_video(item, item["region"], item["rank"], cats) for item in data["items"]]
    return videos, datetime.fromisoformat(data["fetched_at"])


def plain_text(summary: dict, stats: dict) -> str:
    lines = [summary["headline"], "", summary["summary"], ""]
    for t in summary.get("themes", []):
        lines += [f"▶ {t['title']}", t["description"], ""]
    lines.append("가장 빠르게 뜨는 영상:")
    lines += [f"- {v.title} ({v.channel}) {v.url}" for v in stats["rising"]]
    if summary.get("outlook"):
        lines += ["", summary["outlook"]]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="메일을 보내지 않고 HTML 파일로 저장")
    parser.add_argument("--sample", action="store_true", help="YouTube API 대신 동봉된 샘플 데이터 사용")
    parser.add_argument("--out", default="trend_briefing.html", help="--dry-run 결과 파일 경로")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    tz = ZoneInfo(os.environ.get("TIMEZONE", "Asia/Seoul"))
    if args.sample:
        videos, now_utc = load_sample()
    else:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            logging.error("YOUTUBE_API_KEY 환경 변수가 필요합니다.")
            return 1
        regions = [r.strip().upper() for r in os.environ.get("REGIONS", "KR").split(",") if r.strip()]
        max_results = int(os.environ.get("MAX_RESULTS", "50"))
        videos = [v for region in regions for v in fetch_trending(api_key, region, max_results)]
        now_utc = datetime.now(timezone.utc)

    if not videos:
        logging.error("가져온 영상이 없습니다.")
        return 1
    logging.info("영상 %d개 수집", len(videos))

    stats = analyze(videos, now_utc)
    summary = summarize(videos, stats, now_utc)
    now_local = now_utc.astimezone(tz)
    html = render(summary, stats, videos, now_local, now_utc)
    subject = f"[유튜브 트렌드 {now_local:%m/%d}] {summary['headline']}"

    if args.dry_run:
        Path(args.out).write_text(html, encoding="utf-8")
        logging.info("미리보기 저장: %s (제목: %s)", args.out, subject)
    else:
        send_mail(subject, html, plain_text(summary, stats))
        logging.info("메일 발송 완료: %s", subject)
    return 0


if __name__ == "__main__":
    sys.exit(main())
