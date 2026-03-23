"""
크립토 퀀트 시뮬레이터 - Streamlit 대시보드
- 시세 조회: 일일 종가 (전일 오후 9시 기점)
- 분석 결과: 전일 종가 기준 분석
- 전략 비교: 일/주/월 수익률 비교
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict

# 프로젝트 모듈 임포트
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import SUPPORTED_COINS, INITIAL_BALANCE
from exchanges import get_exchange, EXCHANGES
from strategies import get_strategy, STRATEGIES
from simulator import SimulationEngine

# 페이지 설정
st.set_page_config(
    page_title="크립토 퀀트 시뮬레이터",
    page_icon="🪙",
    layout="wide",
)

# 세션 상태 초기화
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = {}
if "last_analysis_settings" not in st.session_state:
    st.session_state.last_analysis_settings = {}


def main():
    st.title("🪙 크립토 퀀트 시뮬레이터")
    st.markdown("*퀀트 전략 백테스팅 및 수익률 비교*")
    
    # 실시간 시세 링크
    st.info("📡 **실시간 시세**는 [여기서 확인](http://localhost:8000) (FastAPI 서버)")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 거래소 선택
        exchange_name = st.selectbox(
            "거래소",
            options=list(EXCHANGES.keys()),
            format_func=lambda x: x.upper(),
        )
        
        # 코인 선택
        symbol = st.selectbox(
            "코인",
            options=SUPPORTED_COINS,
            index=0,
        )
        
        # 초기 자금
        initial_balance = st.number_input(
            "초기 자금 (KRW)",
            min_value=100000,
            max_value=1000000000,
            value=INITIAL_BALANCE,
            step=1000000,
            format="%d",
        )
        
        st.divider()
        
        # 분석 기간
        st.subheader("📅 분석 기간")
        period_days = st.select_slider(
            "데이터 기간",
            options=[30, 60, 90, 180, 365],
            value=90,
            format_func=lambda x: f"{x}일",
        )
        
    # 현재 설정을 session_state에 저장
    current_settings = {
        "exchange": exchange_name,
        "symbol": symbol,
        "initial_balance": initial_balance,
        "period_days": period_days,
    }
    
    # 메인 컨텐츠
    tab1, tab2, tab3 = st.tabs([
        "📈 시세 조회",
        "🎯 분석 결과", 
        "📊 전략 비교"
    ])
    
    with tab1:
        show_daily_prices(exchange_name, symbol, period_days)
    
    with tab2:
        show_analysis_results(current_settings)
    
    with tab3:
        show_strategy_comparison(current_settings)


def show_daily_prices(exchange_name: str, symbol: str, period_days: int):
    """일일 종가 시세 표시 (전일 오후 9시 기점)"""
    st.subheader(f"📈 일일 종가 시세 - {exchange_name.upper()} / {symbol}")
    st.caption("기준: 전일 오후 9시 (21:00 KST)")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    try:
        exchange = get_exchange(exchange_name)
        
        # 캔들 데이터 조회
        candles = exchange.get_candles(symbol, interval="1d", limit=period_days)
        
        if not candles:
            st.warning("시세 데이터를 가져올 수 없습니다.")
            return
        
        df = pd.DataFrame(candles)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp", ascending=False)
        
        # 현재가 및 변동
        latest = df.iloc[0]
        prev = df.iloc[1] if len(df) > 1 else latest
        
        change = latest["close"] - prev["close"]
        change_pct = (change / prev["close"]) * 100 if prev["close"] else 0
        
        # 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                f"{symbol} ({exchange_name.upper()})",
                f"₩{latest['close']:,.0f}",
                f"{change_pct:+.2f}%",
            )
        
        with col2:
            st.metric("고가", f"₩{latest['high']:,.0f}")
        
        with col3:
            st.metric("저가", f"₩{latest['low']:,.0f}")
        
        with col4:
            st.metric("거래량", f"{latest['volume']:,.2f}")
        
        st.divider()
        
        # 차트
        fig = go.Figure()
        
        # 캔들스틱
        fig.add_trace(go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="가격",
            increasing_line_color='#00c853',
            decreasing_line_color='#ff4444',
        ))
        
        # 이동평균선
        df_sorted = df.sort_values("timestamp")
        df_sorted["MA5"] = df_sorted["close"].rolling(5).mean()
        df_sorted["MA20"] = df_sorted["close"].rolling(20).mean()
        
        fig.add_trace(go.Scatter(
            x=df_sorted["timestamp"],
            y=df_sorted["MA5"],
            name="MA5",
            line=dict(color="orange", width=1),
        ))
        
        fig.add_trace(go.Scatter(
            x=df_sorted["timestamp"],
            y=df_sorted["MA20"],
            name="MA20",
            line=dict(color="purple", width=1),
        ))
        
        fig.update_layout(
            title=f"{symbol} 일봉 차트 ({period_days}일)",
            xaxis_rangeslider_visible=False,
            height=500,
            template="plotly_dark",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 일일 종가 테이블
        st.subheader("📋 일일 종가 데이터")
        
        display_df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        display_df.columns = ["날짜", "시가", "고가", "저가", "종가", "거래량"]
        display_df["날짜"] = display_df["날짜"].dt.strftime("%Y-%m-%d")
        display_df["시가"] = display_df["시가"].apply(lambda x: f"₩{x:,.0f}")
        display_df["고가"] = display_df["고가"].apply(lambda x: f"₩{x:,.0f}")
        display_df["저가"] = display_df["저가"].apply(lambda x: f"₩{x:,.0f}")
        display_df["종가"] = display_df["종가"].apply(lambda x: f"₩{x:,.0f}")
        display_df["거래량"] = display_df["거래량"].apply(lambda x: f"{x:,.2f}")
        
        st.dataframe(display_df.head(30), use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"시세 조회 실패: {e}")


def run_full_analysis(exchange_name: str, symbol: str, initial_balance: float, period_days: int, silent: bool = False):
    """전체 분석 실행"""
    progress = None if silent else st.progress(0, "분석 준비 중...")
    
    try:
        exchange = get_exchange(exchange_name)
        candles = exchange.get_candles(symbol, interval="1d", limit=period_days)
        
        if not candles:
            if not silent:
                st.error("캔들 데이터를 가져올 수 없습니다.")
            return
        
        results = []
        strategy_names = list(STRATEGIES.keys())
        
        for i, strategy_name in enumerate(strategy_names):
            if progress:
                progress.progress(
                    (i + 1) / len(strategy_names),
                    f"분석 중: {STRATEGIES[strategy_name].display_name}..."
                )
            
            strategy = get_strategy(strategy_name)
            engine = SimulationEngine(
                strategy=strategy,
                exchange=exchange,
                initial_balance=initial_balance,
            )
            
            result = engine.backtest(symbol, candles)
            result["candles"] = candles
            results.append(result)
        
        # 결과 저장
        st.session_state.analysis_results = {
            "results": results,
            "symbol": symbol,
            "exchange": exchange_name,
            "initial_balance": initial_balance,
            "period_days": period_days,
            "timestamp": datetime.now(),
        }
        
        # 마지막 분석 설정 저장
        st.session_state.last_analysis_settings = {
            "exchange": exchange_name,
            "symbol": symbol,
            "initial_balance": initial_balance,
            "period_days": period_days,
        }
        
        # 기간별 수익률 계산
        calculate_period_returns(results, candles, initial_balance)
        
        if progress:
            progress.empty()
        if not silent:
            st.success("✅ 분석 완료!")
            st.rerun()
        
    except Exception as e:
        if progress:
            progress.empty()
        if not silent:
            st.error(f"분석 실패: {e}")


def calculate_period_returns(results: List[dict], candles: List[dict], initial_balance: float):
    """기간별 수익률 계산 (일/주/월) - 실제 가격 변동 기반"""
    if not candles:
        return
    
    df = pd.DataFrame(candles)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    # 데이터 기간 산출
    data_start = df["timestamp"].min()
    data_end = df["timestamp"].max()
    total_days = len(df)
    
    # 최신 종가
    latest_close = df.iloc[-1]["close"]
    
    # 기간별 시작 가격 및 날짜 찾기
    def get_period_data(days_back: int):
        """N일 전 데이터 찾기"""
        if days_back >= len(df):
            idx = 0
        else:
            idx = max(0, len(df) - days_back - 1)
        return df.iloc[idx]
    
    # 각 기간별 가격 변동률 계산
    daily_data = get_period_data(1)
    weekly_data = get_period_data(7)
    monthly_data = get_period_data(30)
    
    # 가격 기준 수익률 (Hold 전략)
    daily_price_return = ((latest_close - daily_data["close"]) / daily_data["close"] * 100) if daily_data["close"] else 0
    weekly_price_return = ((latest_close - weekly_data["close"]) / weekly_data["close"] * 100) if weekly_data["close"] else 0
    monthly_price_return = ((latest_close - monthly_data["close"]) / monthly_data["close"] * 100) if monthly_data["close"] else 0
    total_price_return = ((latest_close - df.iloc[0]["close"]) / df.iloc[0]["close"] * 100) if df.iloc[0]["close"] else 0
    
    # 기간별 날짜 범위
    period_dates = {
        "daily": {
            "start": daily_data["timestamp"],
            "end": data_end,
        },
        "weekly": {
            "start": weekly_data["timestamp"],
            "end": data_end,
        },
        "monthly": {
            "start": monthly_data["timestamp"],
            "end": data_end,
        },
        "total": {
            "start": data_start,
            "end": data_end,
        },
    }
    
    period_results = []
    
    for result in results:
        if "error" in result:
            continue
        
        strategy_name = result["strategy"]
        portfolio = result.get("portfolio", {})
        total_return_pct = portfolio.get("profit_loss_pct", 0)
        
        # 전략 효율 (전략 수익률 / 시장 수익률)
        # 시장 대비 초과 수익률(알파)을 각 기간에 적용
        if total_price_return != 0:
            strategy_alpha = total_return_pct / total_price_return
        else:
            strategy_alpha = 1.0
        
        # 각 기간별 전략 수익률 = 해당 기간 가격 변동률 × 전략 효율
        daily_return = daily_price_return * strategy_alpha
        weekly_return = weekly_price_return * strategy_alpha
        monthly_return = monthly_price_return * strategy_alpha
        
        period_results.append({
            "strategy": strategy_name,
            "display_name": STRATEGIES[strategy_name].display_name,
            "total_return_pct": total_return_pct,
            "daily_return_pct": daily_return,
            "weekly_return_pct": weekly_return,
            "monthly_return_pct": monthly_return,
            "total_value": portfolio.get("total_value", initial_balance),
            "total_trades": portfolio.get("total_trades", 0),
        })
    
    st.session_state.comparison_results = {
        "period_results": period_results,
        "period_dates": period_dates,
        "price_returns": {
            "daily": daily_price_return,
            "weekly": weekly_price_return,
            "monthly": monthly_price_return,
            "total": total_price_return,
        },
        "timestamp": datetime.now(),
    }


def needs_reanalysis(current_settings: dict) -> bool:
    """설정 변경 여부 확인"""
    last = st.session_state.last_analysis_settings
    if not last:
        return True
    return (
        last.get("exchange") != current_settings["exchange"] or
        last.get("symbol") != current_settings["symbol"] or
        last.get("initial_balance") != current_settings["initial_balance"] or
        last.get("period_days") != current_settings["period_days"]
    )


def show_analysis_results(current_settings: dict = None):
    """분석 결과 표시 (전일 종가 기준)"""
    if current_settings:
        st.subheader(f"🎯 분석 결과 - {current_settings['exchange'].upper()} / {current_settings['symbol']}")
    else:
        st.subheader("🎯 분석 결과")
    st.caption("전일 종가 기준 백테스트 결과")
    
    # 자동 분석: 데이터 없거나 설정 변경시
    if current_settings and (not st.session_state.analysis_results or needs_reanalysis(current_settings)):
        with st.spinner("분석 실행 중..."):
            run_full_analysis(
                current_settings["exchange"],
                current_settings["symbol"],
                current_settings["initial_balance"],
                current_settings["period_days"],
                silent=True
            )
    
    if not st.session_state.analysis_results:
        st.info("👈 사이드바에서 설정 후 분석이 자동 실행됩니다.")
        return
    
    data = st.session_state.analysis_results
    results = data["results"]
    symbol = data["symbol"]
    initial_balance = data["initial_balance"]
    
    # 전략 선택
    strategy_options = [r["strategy"] for r in results if "error" not in r]
    
    if not strategy_options:
        st.warning("분석 결과가 없습니다.")
        return
    
    selected_strategy = st.selectbox(
        "전략 선택",
        options=strategy_options,
        format_func=lambda x: STRATEGIES[x].display_name,
    )
    
    # 선택된 전략 결과
    result = next(r for r in results if r["strategy"] == selected_strategy)
    portfolio = result.get("portfolio", {})
    signals = result.get("signals", {})
    candles = result.get("candles", [])
    
    st.divider()
    
    # 요약 메트릭
    col1, col2, col3, col4, col5 = st.columns(5)
    
    profit = portfolio.get("profit_loss", 0)
    profit_pct = portfolio.get("profit_loss_pct", 0)
    
    with col1:
        st.metric("초기 자금", f"₩{initial_balance:,.0f}")
    
    with col2:
        st.metric(
            "최종 자산",
            f"₩{portfolio.get('total_value', 0):,.0f}",
        )
    
    with col3:
        delta_color = "normal" if profit >= 0 else "inverse"
        st.metric(
            "수익/손실",
            f"₩{profit:,.0f}",
            f"{profit_pct:+.2f}%",
            delta_color=delta_color,
        )
    
    with col4:
        st.metric("총 거래", portfolio.get("total_trades", 0))
    
    with col5:
        st.metric(
            "매수/매도",
            f"{signals.get('buy', 0)} / {signals.get('sell', 0)}",
        )
    
    st.divider()
    
    # 전략 설명
    strategy_obj = get_strategy(selected_strategy)
    st.markdown(f"**📌 전략 설명:** {strategy_obj.description}")
    
    # 차트
    if candles:
        df = pd.DataFrame(candles)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        
        # 지표 계산
        df = strategy_obj.calculate_indicators(df)
        
        fig = go.Figure()
        
        # 캔들
        fig.add_trace(go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="가격",
        ))
        
        # 전략별 지표 표시
        if selected_strategy == "sma_cross":
            if "sma_short" in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["timestamp"], y=df["sma_short"],
                    name="SMA 단기", line=dict(color="orange"),
                ))
            if "sma_long" in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["timestamp"], y=df["sma_long"],
                    name="SMA 장기", line=dict(color="purple"),
                ))
        
        elif selected_strategy == "bollinger":
            if "bb_upper" in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["timestamp"], y=df["bb_upper"],
                    name="상단 밴드", line=dict(color="gray", dash="dash"),
                ))
                fig.add_trace(go.Scatter(
                    x=df["timestamp"], y=df["bb_lower"],
                    name="하단 밴드", line=dict(color="gray", dash="dash"),
                    fill="tonexty", fillcolor="rgba(128,128,128,0.1)",
                ))
        
        fig.update_layout(
            title=f"{symbol} - {STRATEGIES[selected_strategy].display_name}",
            xaxis_rangeslider_visible=False,
            height=500,
            template="plotly_dark",
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 보유 포지션
    positions = portfolio.get("positions", [])
    if positions:
        st.subheader("💼 현재 보유 포지션")
        pos_df = pd.DataFrame(positions)
        st.dataframe(pos_df, use_container_width=True, hide_index=True)


def show_strategy_comparison(current_settings: dict = None):
    """전략별 수익률 비교 (일/주/월)"""
    if current_settings:
        st.subheader(f"📊 전략별 수익률 비교 - {current_settings['exchange'].upper()} / {current_settings['symbol']}")
    else:
        st.subheader("📊 전략별 수익률 비교")
    st.caption("일간 / 주간 / 월간 수익률 비교")
    
    # 자동 분석: 데이터 없거나 설정 변경시
    if current_settings and (not st.session_state.comparison_results or needs_reanalysis(current_settings)):
        with st.spinner("분석 실행 중..."):
            run_full_analysis(
                current_settings["exchange"],
                current_settings["symbol"],
                current_settings["initial_balance"],
                current_settings["period_days"],
                silent=True
            )
    
    if not st.session_state.comparison_results:
        st.info("👈 사이드바에서 설정 후 분석이 자동 실행됩니다.")
        return
    
    period_results = st.session_state.comparison_results.get("period_results", [])
    period_dates = st.session_state.comparison_results.get("period_dates", {})
    
    if not period_results:
        st.warning("비교 결과가 없습니다.")
        return
    
    # 기간별 날짜 문자열 생성
    def format_date_range(key: str) -> str:
        if key not in period_dates:
            return ""
        dates = period_dates[key]
        start = dates["start"]
        end = dates["end"]
        if start == end:
            return start.strftime("%m/%d")
        return f"{start.strftime('%m/%d')}~{end.strftime('%m/%d')}"
    
    # 기간 선택 옵션 (날짜 포함)
    total_range = format_date_range("total")
    daily_range = format_date_range("daily")
    weekly_range = format_date_range("weekly")
    monthly_range = format_date_range("monthly")
    
    period_options = {
        f"전체 ({total_range})": "전체",
        f"일간 ({daily_range})": "일간",
        f"주간 ({weekly_range})": "주간",
        f"월간 ({monthly_range})": "월간",
    }
    
    selected_option = st.radio(
        "비교 기간",
        options=list(period_options.keys()),
        horizontal=True,
    )
    period_type = period_options[selected_option]
    
    # 데이터 준비
    if period_type == "전체":
        return_key = "total_return_pct"
        title = f"전체 기간 수익률 ({total_range})"
    elif period_type == "일간":
        return_key = "daily_return_pct"
        title = f"일간 수익률 - 평균 ({daily_range})"
    elif period_type == "주간":
        return_key = "weekly_return_pct"
        title = f"주간 수익률 - 추정 ({weekly_range})"
    else:
        return_key = "monthly_return_pct"
        title = f"월간 수익률 - 추정 ({monthly_range})"
    
    # 정렬
    sorted_results = sorted(period_results, key=lambda x: x[return_key], reverse=True)
    
    # 테이블 (컬럼명에 기간 표시)
    table_data = []
    for i, r in enumerate(sorted_results):
        rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}"
        table_data.append({
            "순위": rank_emoji,
            "전략": r["display_name"],
            f"전체 ({total_range})": f"{r['total_return_pct']:+.2f}%",
            f"일간 ({daily_range})": f"{r['daily_return_pct']:+.3f}%",
            f"주간 ({weekly_range})": f"{r['weekly_return_pct']:+.2f}%",
            f"월간 ({monthly_range})": f"{r['monthly_return_pct']:+.2f}%",
            "최종 자산": f"₩{r['total_value']:,.0f}",
            "거래 횟수": r["total_trades"],
        })
    
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    
    st.divider()
    
    # 차트
    col1, col2 = st.columns(2)
    
    with col1:
        # 막대 차트
        strategies = [r["display_name"] for r in sorted_results]
        returns = [r[return_key] for r in sorted_results]
        colors = ["#00c853" if r >= 0 else "#ff4444" for r in returns]
        
        fig = go.Figure(data=[
            go.Bar(
                x=strategies,
                y=returns,
                marker_color=colors,
                text=[f"{r:+.2f}%" for r in returns],
                textposition="outside",
            )
        ])
        
        fig.update_layout(
            title=title,
            yaxis_title="수익률 (%)",
            height=400,
            template="plotly_dark",
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 파이 차트 (자산 분포)
        fig = go.Figure(data=[
            go.Pie(
                labels=[r["display_name"] for r in sorted_results],
                values=[r["total_value"] for r in sorted_results],
                hole=0.4,
            )
        ])
        
        fig.update_layout(
            title="최종 자산 분포",
            height=400,
            template="plotly_dark",
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 최고 성과 전략
    best = sorted_results[0]
    st.success(f"🏆 **최고 성과 전략:** {best['display_name']} ({best['total_return_pct']:+.2f}%)")
    
    # 기간별 비교 차트
    st.divider()
    st.subheader("📈 기간별 수익률 비교")
    
    # 그룹 바 차트
    fig = go.Figure()
    
    # X축 레이블에 날짜 범위 포함
    periods_with_dates = [
        f"일간\n({daily_range})",
        f"주간\n({weekly_range})",
        f"월간\n({monthly_range})",
    ]
    keys = ["daily_return_pct", "weekly_return_pct", "monthly_return_pct"]
    
    for r in sorted_results:
        fig.add_trace(go.Bar(
            name=r["display_name"],
            x=periods_with_dates,
            y=[r[k] for k in keys],
            text=[f"{r[k]:+.2f}%" for k in keys],
            textposition="outside",
        ))
    
    fig.update_layout(
        barmode="group",
        title="전략별 기간 수익률",
        yaxis_title="수익률 (%)",
        height=400,
        template="plotly_dark",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 투자 의견 섹션
    show_investment_opinion(sorted_results, st.session_state.comparison_results, current_settings)


def show_investment_opinion(sorted_results: List[dict], comparison_data: dict, settings: dict):
    """종합 투자 의견 표시"""
    st.divider()
    st.subheader("💡 종합 투자 의견")
    
    if not sorted_results or not comparison_data:
        st.info("분석 데이터가 필요합니다.")
        return
    
    price_returns = comparison_data.get("price_returns", {})
    daily_return = price_returns.get("daily", 0)
    weekly_return = price_returns.get("weekly", 0)
    monthly_return = price_returns.get("monthly", 0)
    
    # 최고 성과 전략
    best_strategy = sorted_results[0]
    worst_strategy = sorted_results[-1]
    
    # 시장 트렌드 분석
    def get_trend(ret: float) -> tuple:
        if ret > 3:
            return "강세 📈", "success"
        elif ret > 0:
            return "약세 상승 📊", "info"
        elif ret > -3:
            return "약세 하락 📉", "warning"
        else:
            return "강한 하락 🔻", "error"
    
    daily_trend, daily_color = get_trend(daily_return)
    weekly_trend, weekly_color = get_trend(weekly_return)
    monthly_trend, monthly_color = get_trend(monthly_return)
    
    # 시장 상황 카드
    st.markdown("### 📊 시장 상황")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("일간 트렌드", daily_trend, f"{daily_return:+.2f}%")
    with col2:
        st.metric("주간 트렌드", weekly_trend, f"{weekly_return:+.2f}%")
    with col3:
        st.metric("월간 트렌드", monthly_trend, f"{monthly_return:+.2f}%")
    
    st.markdown("---")
    
    # 종합 의견
    st.markdown("### 🎯 전략 추천")
    
    # 시장 상황에 따른 추천 로직
    avg_return = (daily_return + weekly_return + monthly_return) / 3
    
    # 추천 의견 생성
    opinions = []
    
    # 1. 최고 성과 전략
    opinions.append(f"**🏆 최고 성과 전략:** {best_strategy['display_name']} (전체 수익률 {best_strategy['total_return_pct']:+.2f}%)")
    
    # 2. 시장 상황별 추천
    if avg_return > 2:
        market_condition = "상승장"
        opinions.append(f"**📈 현재 시장:** {market_condition} - 추세 추종 전략(SMA 크로스, MACD)이 유리합니다.")
        recommended = "SMA 크로스오버" if any(r["strategy"] == "sma_cross" for r in sorted_results) else best_strategy["display_name"]
    elif avg_return < -2:
        market_condition = "하락장"
        opinions.append(f"**📉 현재 시장:** {market_condition} - 역추세 전략(RSI 과매도, 볼린저 밴드)이 유리합니다.")
        recommended = "RSI" if any(r["strategy"] == "rsi" for r in sorted_results) else best_strategy["display_name"]
    else:
        market_condition = "횡보장"
        opinions.append(f"**📊 현재 시장:** {market_condition} - 레인지 전략(볼린저 밴드)이 유리합니다.")
        recommended = "볼린저 밴드" if any(r["strategy"] == "bollinger" for r in sorted_results) else best_strategy["display_name"]
    
    # 3. 기간별 추천
    if weekly_return > 0 and monthly_return < 0:
        opinions.append("**⚠️ 주의:** 단기 반등 중이나 중기 하락 추세입니다. 단기 매매 권장.")
    elif weekly_return < 0 and monthly_return > 0:
        opinions.append("**💡 기회:** 단기 조정 중이나 중기 상승 추세입니다. 매수 기회 검토.")
    elif weekly_return > 0 and monthly_return > 0:
        opinions.append("**✅ 긍정적:** 단기/중기 모두 상승 추세입니다. 추세 추종 전략 권장.")
    else:
        opinions.append("**🛡️ 방어적:** 단기/중기 모두 하락 추세입니다. 현금 비중 확대 권장.")
    
    # 의견 출력
    for opinion in opinions:
        st.markdown(opinion)
    
    st.markdown("---")
    
    # 전략별 요약 테이블
    st.markdown("### 📋 전략별 요약")
    
    summary_data = []
    for i, r in enumerate(sorted_results):
        # 전략별 특징
        strategy_traits = {
            "sma_cross": "추세 추종형 - 상승장에 강함",
            "rsi": "역추세형 - 과매수/과매도 포착",
            "bollinger": "변동성 활용 - 횡보장에 강함",
            "macd": "모멘텀 기반 - 추세 전환 포착",
        }
        
        trait = strategy_traits.get(r["strategy"], "일반 전략")
        
        # 추천 여부
        if i == 0:
            recommendation = "⭐ 최우선 추천"
        elif r["total_return_pct"] > 0:
            recommendation = "✅ 양호"
        else:
            recommendation = "⚠️ 주의"
        
        summary_data.append({
            "순위": f"{i+1}위",
            "전략": r["display_name"],
            "전체 수익률": f"{r['total_return_pct']:+.2f}%",
            "특징": trait,
            "추천": recommendation,
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
    
    # 면책 조항
    st.caption("⚠️ 본 분석은 과거 데이터 기반 시뮬레이션 결과이며, 실제 투자 수익을 보장하지 않습니다. 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.")


if __name__ == "__main__":
    main()
