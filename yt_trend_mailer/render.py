"""메일 클라이언트 호환을 위해 인라인 스타일만 쓰는 HTML 브리핑을 만든다."""

from __future__ import annotations

from datetime import datetime
from html import escape

from .youtube import Video

_ACCENT = "#e62117"
_MUTED = "#6b7280"


def _num(n: float) -> str:
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}".removesuffix(".0") + "억"
    if n >= 10_000:
        return f"{n / 10_000:.1f}".removesuffix(".0") + "만"
    return f"{n:,.0f}"


def _video_row(v: Video, now: datetime, note: str = "") -> str:
    meta = f"{escape(v.channel)} · 조회수 {_num(v.views)} · 시간당 {_num(v.views_per_hour(now))}"
    if v.is_short:
        meta += " · 쇼츠"
    note_html = f'<div style="font-size:13px;color:#374151;margin-top:4px">{escape(note)}</div>' if note else ""
    thumb = (
        f'<td width="120" style="padding:8px 12px 8px 0;vertical-align:top">'
        f'<a href="{v.url}"><img src="{escape(v.thumbnail)}" width="120" style="border-radius:6px;display:block" alt=""></a></td>'
        if v.thumbnail
        else ""
    )
    return (
        f'<tr>{thumb}<td style="padding:8px 0;vertical-align:top">'
        f'<a href="{v.url}" style="color:#111827;font-weight:600;text-decoration:none;font-size:14px">{escape(v.title)}</a>'
        f'<div style="font-size:12px;color:{_MUTED};margin-top:2px">[{v.region} #{v.rank}] {meta}</div>{note_html}</td></tr>'
    )


def _section(title: str, body: str) -> str:
    return (
        f'<h2 style="font-size:16px;margin:28px 0 8px;padding-bottom:6px;border-bottom:2px solid {_ACCENT}">{title}</h2>{body}'
    )


def render(summary: dict, stats: dict, videos: list[Video], now_local: datetime, now_utc: datetime) -> str:
    by_id = {v.video_id: v for v in videos}
    parts: list[str] = [
        f'<p style="font-size:15px;line-height:1.7;margin:0">{escape(summary["summary"])}</p>',
    ]

    if summary.get("themes"):
        themes = []
        for t in summary["themes"]:
            rows = "".join(_video_row(by_id[vid], now_utc) for vid in t["video_ids"][:3] if vid in by_id)
            themes.append(
                f'<h3 style="font-size:15px;margin:18px 0 4px">▶ {escape(t["title"])}</h3>'
                f'<p style="font-size:14px;line-height:1.6;margin:0 0 4px;color:#374151">{escape(t["description"])}</p>'
                f'<table cellpadding="0" cellspacing="0" width="100%">{rows}</table>'
            )
        parts.append(_section("오늘의 트렌드 테마", "".join(themes)))

    picks = "".join(_video_row(by_id[p["video_id"]], now_utc, p["reason"]) for p in summary.get("watch_picks", []) if p["video_id"] in by_id)
    if picks:
        parts.append(_section("오늘 볼 만한 영상", f'<table cellpadding="0" cellspacing="0" width="100%">{picks}</table>'))

    chips = " ".join(
        f'<span style="display:inline-block;background:#f3f4f6;border-radius:12px;padding:3px 10px;margin:2px;font-size:13px">#{escape(k)} <span style="color:{_MUTED}">{n}</span></span>'
        for k, n in stats["keywords"]
    )
    max_cat = stats["categories"][0][1] if stats["categories"] else 1
    cat_rows = "".join(
        f'<tr><td style="font-size:13px;padding:2px 8px 2px 0;white-space:nowrap">{escape(c)}</td>'
        f'<td width="100%"><div style="background:{_ACCENT};height:10px;border-radius:5px;width:{n / max_cat * 100:.0f}%"></div></td>'
        f'<td style="font-size:12px;color:{_MUTED};padding-left:8px">{n}</td></tr>'
        for c, n in stats["categories"]
    )
    numbers = (
        f'<p style="font-size:13px;color:#374151;margin:0 0 10px">분석 영상 {stats["total"]}개 · 쇼츠 비중 {stats["shorts_ratio"]:.0%} · '
        f'24시간 내 업로드 {stats["fresh_count"]}개 · 평균 업로드 경과 {stats["avg_age_hours"]:.0f}시간</p>'
    )
    parts.append(
        _section(
            "숫자로 보는 오늘",
            numbers + f'<table cellpadding="0" cellspacing="0" width="100%">{cat_rows}</table>'
            + (f'<div style="margin-top:12px">{chips}</div>' if chips else ""),
        )
    )

    if stats.get("global_hits"):
        hits = "".join(_video_row(v, now_utc, f"{', '.join(regs)} 동시 인기") for v, regs in stats["global_hits"])
        parts.append(_section("여러 나라에서 동시에 뜬 영상", f'<table cellpadding="0" cellspacing="0" width="100%">{hits}</table>'))

    rising = "".join(_video_row(v, now_utc) for v in stats["rising"])
    parts.append(_section("가장 빠르게 뜨는 영상 (시간당 조회수)", f'<table cellpadding="0" cellspacing="0" width="100%">{rising}</table>'))

    top = "".join(_video_row(v, now_utc) for v in stats["top"])
    parts.append(_section("인기 급상승 상위", f'<table cellpadding="0" cellspacing="0" width="100%">{top}</table>'))

    if summary.get("outlook"):
        parts.append(_section("앞으로 주목할 포인트", f'<p style="font-size:14px;line-height:1.6;margin:0">{escape(summary["outlook"])}</p>'))

    body = "".join(parts)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f5">
<table cellpadding="0" cellspacing="0" width="100%" style="background:#f5f5f5"><tr><td align="center" style="padding:16px">
<table cellpadding="0" cellspacing="0" width="100%" style="max-width:640px;background:#ffffff;border-radius:10px;font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;color:#111827">
<tr><td style="padding:24px 24px 8px">
<div style="font-size:12px;color:{_ACCENT};font-weight:700;letter-spacing:.5px">YOUTUBE TREND BRIEFING · {now_local:%Y.%m.%d}</div>
<h1 style="font-size:22px;line-height:1.35;margin:8px 0 16px">{escape(summary["headline"])}</h1>
{body}
</td></tr>
<tr><td style="padding:16px 24px 24px;font-size:11px;color:{_MUTED}">
데이터: YouTube Data API 인기 급상승 ({", ".join(stats["regions"])}) · 요약: {escape(summary.get("generated_by", ""))}
</td></tr>
</table></td></tr></table>
</body></html>"""
