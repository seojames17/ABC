"""
주가 데이터 대시보드 (Streamlit, yfinance 기반)

- 데이터: `yfinance`
- 실행: `streamlit run app.py`

참고:
- yfinance는 제3자 데이터 소스이므로, 장 마감/거래일/일시 중단 등에 따라 값이 비어 있을 수 있습니다.
- 본 코드는 투자 권유가 아닙니다.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots


DEFAULT_TICKER = "005490.KS"  # 예시 티커(사용자가 변경 가능): KR 거래소 형식 또는 US 티커 등


def default_ma_windows(interval: str) -> list[int]:
    """
    interval에 맞춰 이동평균 윈도우(“봉 개수”)를 합리적인 크기로 조정합니다.
    - 1d: 5/20/60일
    - 1wk: 2/6/12주
    - 1mo: 2/6/12개월
    """

    if interval == "1wk":
        return [2, 6, 12]
    if interval == "1mo":
        return [2, 6, 12]
    return [5, 20, 60]


def _to_date(d: date | str) -> date:
    if isinstance(d, date):
        return d
    return date.fromisoformat(str(d))


def _normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # yfinance 결과는 종종 tz-aware index를 줄 수 있어, 시각화 호환성을 위해 tz 제거.
    try:
        if getattr(df.index, "tz", None) is not None:
            df = df.copy()
            df.index = df.index.tz_localize(None)
    except Exception:
        pass
    return df


@st.cache_data(ttl=60 * 10, show_spinner=False)
def fetch_history(
    ticker: str, start: date, end: date, interval: str
) -> pd.DataFrame:
    # yfinance는 end date를 "포함하지 않는" 방식으로 동작하는 경우가 많아,
    # UI에서 자연스러운 결과를 위해 end에 하루를 더합니다.
    df = yf.download(
        ticker,
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        interval=interval,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    if df is None:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance(single ticker)에서는 대개 컬럼이 (Price, Ticker) 형태 MultiIndex입니다.
        # 이때 Ticker 레벨은 동일하므로 Price 레벨을 그대로 사용해야 `Close/High/...`가 유지됩니다.
        tickers_in_level = pd.unique(df.columns.get_level_values(-1))
        if len(tickers_in_level) == 1:
            df.columns = df.columns.get_level_values(0)
        else:
            # (이론상 단일 티커 사용이라 잘 안 오지만) 여러 티커가 섞이면 컬럼을 문자열로 평탄화.
            df.columns = ["{}_{}".format(a, b) for a, b in df.columns.to_list()]
    df = _normalize_index(df)
    return df


@st.cache_data(ttl=60 * 60, show_spinner=False)
def fetch_company_name(ticker: str) -> Optional[str]:
    try:
        info = yf.Ticker(ticker).info
        # "shortName"이 가장 흔하지만, 환경에 따라 달라질 수 있습니다.
        return info.get("shortName") or info.get("longName")
    except Exception:
        return None


def compute_metrics(hist: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None, None, None, None
    close = hist["Close"].dropna()
    if len(close) < 2:
        return None, None, None, None

    current = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    daily_change_pct = ((current - prev) / prev * 100.0) if prev != 0 else None

    # 거래량은 interval이 일/주/월에 따라 달라질 수 있어, "최근봉" 기준으로 표시.
    volume_latest = None
    if "Volume" in hist.columns:
        v = hist["Volume"].dropna()
        if not v.empty:
            volume_latest = float(v.iloc[-1])

    return current, daily_change_pct, volume_latest, prev


def build_line_chart(hist: pd.DataFrame, ma_windows: list[int]) -> go.Figure:
    df = hist.copy()
    df = df.dropna(subset=["Close"])
    # yfinance index 컬럼명이 환경마다 다를 수 있어, 항상 Date로 강제합니다.
    df.index.name = "Date"
    df = df.reset_index()
    x = df["Date"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df["Close"], mode="lines", name="Close"))

    for w in ma_windows:
        ma = df["Close"].rolling(w).mean()
        fig.add_trace(go.Scatter(x=x, y=ma, mode="lines", name=f"MA{w}"))

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Price",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def build_candlestick_with_volume(hist: pd.DataFrame, ma_windows: list[int]) -> go.Figure:
    df = hist.copy()
    needed = ["Open", "High", "Low", "Close"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        # OHLC가 없으면 선 그래프로 대체.
        return build_line_chart(hist, ma_windows)

    df = df.dropna(subset=needed)
    # yfinance index 컬럼명이 환경마다 다를 수 있어, 항상 Date로 강제합니다.
    df.index.name = "Date"
    df = df.reset_index()

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.72, 0.28],
        specs=[[{"type": "candlestick"}], [{"type": "bar"}]],
    )

    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    if "Volume" in df.columns:
        # 상승/하락에 따라 색 분기
        up = df["Close"] >= df["Open"]
        colors = ["#26a69a" if b else "#ef5350" for b in up.tolist()]
        fig.add_trace(
            go.Bar(x=df["Date"], y=df["Volume"], marker_color=colors, name="Volume"),
            row=2,
            col=1,
        )

    for w in ma_windows:
        ma = df["Close"].rolling(w).mean()
        fig.add_trace(go.Scatter(x=df["Date"], y=ma, mode="lines", name=f"MA{w}"), row=1, col=1)

    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Price",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def main() -> None:
    st.set_page_config(
        page_title="주가 데이터 대시보드",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📈 주가 데이터 대시보드")
    st.caption(
        "`yfinance`로 티커의 가격/거래량을 시각화하고, 최근 변동/52주 범위 같은 요약 지표를 표시합니다. "
        "투자 권유가 아닙니다."
    )

    with st.sidebar:
        st.header("설정")
        ticker = st.text_input(
            "티커 (예: 005490.KS, AAPL, MSFT)",
            value=DEFAULT_TICKER,
            help="yfinance 티커를 그대로 입력하세요.",
        ).strip()

        end_default = date.today()
        start_default = end_default - timedelta(days=365 * 2)

        start_date = st.date_input("시작일", value=start_default)
        end_date = st.date_input("종료일", value=end_default)

        interval = st.selectbox(
            "차트 간격",
            options=["1d", "1wk", "1mo"],
            index=0,
            help="1d=일봉, 1wk=주봉, 1mo=월봉",
        )

        show_52w = st.checkbox("52주 최저/최고 표시", value=True)
        company_name_on = st.checkbox("회사명 표시(추가 조회)", value=False)

        ma_on = st.checkbox("이동평균 표시", value=True)
        ma_windows = default_ma_windows(interval) if ma_on else []

        chart_type = st.selectbox(
            "차트 유형",
            options=["캔들 + 이동평균", "종가선 + 이동평균"],
            index=0,
        )

    if not ticker:
        st.error("티커를 입력해주세요.")
        st.stop()

    start_date = _to_date(start_date)
    end_date = _to_date(end_date)
    if start_date >= end_date:
        st.error("시작일은 종료일보다 이전이어야 합니다.")
        st.stop()

    with st.spinner("주가 데이터를 불러오는 중..."):
        hist = fetch_history(ticker, start_date, end_date, interval)

    if hist is None or hist.empty:
        st.warning(
            "데이터를 가져오지 못했습니다. 티커/기간/간격을 확인해 주세요. "
            "특히 interval=1wk/1mo에서 거래일이 적으면 공백이 될 수 있습니다."
        )
        st.stop()

    company_name = fetch_company_name(ticker) if company_name_on else None

    current, change_pct, volume_latest, _prev = compute_metrics(hist)

    # 최근 거래량(일봉 기준) 평균: 20개 구간
    avg_volume_20 = None
    if "Volume" in hist.columns:
        vol = hist["Volume"].dropna()
        if len(vol) >= 20:
            avg_volume_20 = float(vol.tail(20).mean())

    week52_low = None
    week52_high = None
    if show_52w:
        # 52주 범위 계산용: 1d 기준으로 별도 조회 (캐시 적용)
        today = date.today()
        should_reuse_1y = (
            interval == "1d"
            and start_date <= (today - timedelta(days=370))
            and end_date >= (today - timedelta(days=1))
        )
        hist_1y = hist if should_reuse_1y else fetch_history(ticker, today - timedelta(days=370), today, "1d")
        hist_1y = hist_1y.dropna(subset=["High", "Low"]) if not hist_1y.empty else hist_1y
        week52_low = float(hist_1y["Low"].min()) if (not hist_1y.empty and "Low" in hist_1y.columns) else None
        week52_high = float(hist_1y["High"].max()) if (not hist_1y.empty and "High" in hist_1y.columns) else None

    header = f"{company_name} ({ticker})" if company_name else f"{ticker}"
    st.subheader(header)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재가 (최근 Close)", "-" if current is None else f"{current:,.0f}")
    if change_pct is None:
        c2.metric("최근 변동률", "-")
    else:
        sign = "+" if change_pct >= 0 else ""
        c2.metric("최근 변동률(직전 대비)", f"{sign}{change_pct:.2f}%")
    c3.metric("최근 거래량 (Volume)", "-" if volume_latest is None else f"{volume_latest:,.0f}")
    if avg_volume_20 is None:
        c4.metric("거래량 평균 (최근 20)", "-")
    else:
        c4.metric("거래량 평균 (최근 20)", f"{avg_volume_20:,.0f}")

    if week52_low is not None and week52_high is not None:
        c5, c6 = st.columns(2)
        c5.metric("52주 최저가", f"{week52_low:,.0f}")
        c6.metric("52주 최고가", f"{week52_high:,.0f}")

    # 차트
    chart_hist = hist.copy()
    chart_hist = chart_hist.dropna(subset=["Close"])

    if chart_type == "캔들 + 이동평균":
        fig = build_candlestick_with_volume(chart_hist, ma_windows=ma_windows)
    else:
        fig = build_line_chart(chart_hist, ma_windows=ma_windows)

    st.plotly_chart(fig, width="stretch")

    # 데이터 테이블
    st.subheader("최근 데이터")
    show_cols = []
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in hist.columns:
            show_cols.append(c)
    latest = hist.tail(30).copy()
    latest.index.name = "Date"
    st.dataframe(latest[show_cols], width="stretch", height=280)

    csv = latest.reset_index().to_csv(index=False).encode("utf-8")
    st.download_button(
        "최근 데이터 CSV 다운로드",
        data=csv,
        file_name=f"stock_{ticker}_latest.csv",
        mime="text/csv",
    )

    st.caption("데이터 소스: yfinance. 본 대시보드는 참고/시각화 목적이며 투자 판단의 책임은 사용자에게 있습니다.")


if __name__ == "__main__":
    main()
