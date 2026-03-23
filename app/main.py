"""
크립토 퀀트 시뮬레이터 - Streamlit 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# 프로젝트 모듈 임포트
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import SUPPORTED_COINS, INITIAL_BALANCE
from app.realtime import realtime_manager, format_price_for_display
from exchanges import get_exchange, EXCHANGES
from exchanges.websocket import WEBSOCKETS
from strategies import get_strategy, STRATEGIES
from simulator import SimulationEngine

# 페이지 설정
st.set_page_config(
    page_title="크립토 퀀트 시뮬레이터",
    page_icon="🪙",
    layout="wide",
)

# 세션 상태 초기화
if "ws_started" not in st.session_state:
    st.session_state.ws_started = False
if "portfolios" not in st.session_state:
    st.session_state.portfolios = {}
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = {}


def start_websocket():
    """웹소켓 시작"""
    if not st.session_state.ws_started:
        realtime_manager.start(
            exchanges=["upbit", "bithumb"],
            symbols=SUPPORTED_COINS,
        )
        st.session_state.ws_started = True


def main():
    st.title("🪙 크립토 퀀트 시뮬레이터")
    st.markdown("*가상 투자 시뮬레이션으로 퀀트 전략 비교*")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 실시간 연결 상태
        ws_status = realtime_manager.get_status()
        if ws_status["is_running"]:
            connected = sum(1 for e in ws_status["exchanges"].values() if e["connected"])
            st.success(f"🟢 실시간 연결 ({connected}개 거래소)")
        else:
            st.warning("🔴 실시간 연결 안됨")
        
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
        
        # 전략 선택
        strategy_name = st.selectbox(
            "전략",
            options=list(STRATEGIES.keys()),
            format_func=lambda x: STRATEGIES[x].display_name,
        )
        
        # 초기 자금
        initial_balance = st.number_input(
            "초기 자금 (KRW)",
            min_value=100000,
            max_value=1000000000,
            value=INITIAL_BALANCE,
            step=1000000,
        )
        
        st.divider()
        
        # 실시간 연결 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔌 실시간 연결", use_container_width=True):
                start_websocket()
                st.rerun()
        
        with col2:
            if st.button("⏹️ 연결 해제", use_container_width=True):
                realtime_manager.stop()
                st.session_state.ws_started = False
                st.rerun()
        
        st.divider()
        
        # 분석 버튼
        if st.button("📊 백테스트 실행", type="primary", use_container_width=True):
            run_analysis(exchange_name, symbol, strategy_name, initial_balance)
        
        if st.button("🔄 전체 전략 비교", use_container_width=True):
            compare_all_strategies(exchange_name, symbol, initial_balance)
    
    # 메인 컨텐츠
    tab1, tab2, tab3, tab4 = st.tabs([
        "📡 실시간 시세", 
        "📈 시세 조회",
        "🎯 분석 결과", 
        "📊 전략 비교"
    ])
    
    with tab1:
        show_realtime_prices()
    
    with tab2:
        show_static_prices(exchange_name)
    
    with tab3:
        show_analysis_results()
    
    with tab4:
        show_strategy_comparison()


def show_realtime_prices():
    """실시간 시세 표시 (WebSocket)"""
    st.subheader("📡 실시간 시세")
    
    # 자동 새로고침 설정
    auto_refresh = st.checkbox("🔄 자동 새로고침 (2초)", value=True)
    
    # 연결 시작
    if not st.session_state.ws_started:
        st.info("👆 사이드바에서 '실시간 연결' 버튼을 클릭하세요")
        start_websocket()
        time.sleep(1)  # 연결 대기
    
    # 가격 표시 영역
    price_container = st.empty()
    chart_container = st.empty()
    
    # 가격 조회
    all_prices = realtime_manager.get_all_prices()
    
    if not all_prices:
        price_container.warning("시세 데이터 수신 대기 중... (몇 초 소요)")
        if auto_refresh:
            time.sleep(2)
            st.rerun()
        return
    
    # 심볼별로 그룹화 (최신 가격만)
    latest_prices = {}
    for ticker in all_prices:
        key = ticker.symbol
        if key not in latest_prices or ticker.timestamp > latest_prices[key].timestamp:
            latest_prices[key] = ticker
    
    # 테이블 데이터 생성
    data = []
    for symbol in SUPPORTED_COINS:
        if symbol in latest_prices:
            formatted = format_price_for_display(latest_prices[symbol])
            data.append(formatted)
    
    if data:
        with price_container.container():
            # 메트릭 카드
            cols = st.columns(min(5, len(data)))
            for i, item in enumerate(data[:5]):
                with cols[i]:
                    delta_color = "normal" if item["change_raw"] >= 0 else "inverse"
                    st.metric(
                        label=f"{item['symbol']} ({item['exchange']})",
                        value=f"₩{item['price']}",
                        delta=f"{item['change_raw']:+.2f}%",
                        delta_color=delta_color,
                    )
            
            st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
        
        # 가격 비교 차트
        with chart_container.container():
            # 거래소별 가격 비교
            exchange_prices = {}
            for ticker in all_prices:
                key = (ticker.symbol, ticker.exchange)
                if key not in exchange_prices:
                    exchange_prices[key] = ticker
            
            chart_data = []
            for (symbol, exchange), ticker in exchange_prices.items():
                chart_data.append({
                    "코인": symbol,
                    "거래소": exchange.upper(),
                    "가격": ticker.price,
                })
            
            if chart_data:
                df = pd.DataFrame(chart_data)
                fig = px.bar(
                    df,
                    x="코인",
                    y="가격",
                    color="거래소",
                    barmode="group",
                    title="거래소별 가격 비교",
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # 자동 새로고침
    if auto_refresh:
        time.sleep(2)
        st.rerun()


def show_static_prices(exchange_name: str):
    """정적 시세 표시 (REST API)"""
    st.subheader("📈 시세 조회")
    
    if st.button("🔄 새로고침"):
        st.rerun()
    
    try:
        exchange = get_exchange(exchange_name)
        tickers = exchange.get_tickers(SUPPORTED_COINS)
        
        if not tickers:
            st.warning("시세 정보를 가져올 수 없습니다.")
            return
        
        # 시세 테이블
        data = []
        for ticker in tickers:
            change_color = "🟢" if ticker.change_24h >= 0 else "🔴"
            data.append({
                "코인": ticker.symbol,
                "현재가": f"₩{ticker.price:,.0f}",
                "변동률": f"{change_color} {ticker.change_24h:+.2f}%",
                "24h 고가": f"₩{ticker.high_24h:,.0f}",
                "24h 저가": f"₩{ticker.low_24h:,.0f}",
                "거래소": ticker.exchange.upper(),
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 차트
        col1, col2 = st.columns(2)
        
        with col1:
            prices = [t.price for t in tickers]
            symbols = [t.symbol for t in tickers]
            
            fig = px.bar(x=symbols, y=prices, title="코인별 현재가")
            fig.update_layout(yaxis_title="KRW")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            changes = [t.change_24h for t in tickers]
            colors = ["green" if c >= 0 else "red" for c in changes]
            
            fig = go.Figure(data=[
                go.Bar(x=symbols, y=changes, marker_color=colors)
            ])
            fig.update_layout(title="24시간 변동률", yaxis_title="%")
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"시세 조회 실패: {e}")


def run_analysis(exchange_name: str, symbol: str, strategy_name: str, initial_balance: float):
    """분석 실행"""
    with st.spinner("백테스트 실행 중..."):
        try:
            exchange = get_exchange(exchange_name)
            strategy = get_strategy(strategy_name)
            
            candles = exchange.get_candles(symbol, interval="1d", limit=100)
            
            if not candles:
                st.error("캔들 데이터를 가져올 수 없습니다.")
                return
            
            engine = SimulationEngine(
                strategy=strategy,
                exchange=exchange,
                initial_balance=initial_balance,
            )
            
            result = engine.backtest(symbol, candles)
            
            key = f"{exchange_name}_{symbol}_{strategy_name}"
            st.session_state.simulation_results[key] = {
                "result": result,
                "candles": candles,
                "timestamp": datetime.now(),
            }
            
            st.success(f"✅ 백테스트 완료! ({strategy.display_name})")
            
        except Exception as e:
            st.error(f"분석 실패: {e}")


def compare_all_strategies(exchange_name: str, symbol: str, initial_balance: float):
    """모든 전략 비교"""
    with st.spinner("전체 전략 비교 중..."):
        try:
            exchange = get_exchange(exchange_name)
            candles = exchange.get_candles(symbol, interval="1d", limit=100)
            
            if not candles:
                st.error("캔들 데이터를 가져올 수 없습니다.")
                return
            
            results = []
            for strategy_name in STRATEGIES.keys():
                strategy = get_strategy(strategy_name)
                engine = SimulationEngine(
                    strategy=strategy,
                    exchange=exchange,
                    initial_balance=initial_balance,
                )
                result = engine.backtest(symbol, candles)
                results.append(result)
            
            st.session_state.comparison_results = {
                "results": results,
                "symbol": symbol,
                "exchange": exchange_name,
                "timestamp": datetime.now(),
            }
            
            st.success("✅ 전체 전략 비교 완료!")
            
        except Exception as e:
            st.error(f"비교 실패: {e}")


def show_analysis_results():
    """분석 결과 표시"""
    st.subheader("🎯 백테스트 결과")
    
    if not st.session_state.simulation_results:
        st.info("사이드바에서 '백테스트 실행'을 클릭하세요.")
        return
    
    latest_key = list(st.session_state.simulation_results.keys())[-1]
    data = st.session_state.simulation_results[latest_key]
    result = data["result"]
    candles = data["candles"]
    
    if "error" in result:
        st.error(result["error"])
        return
    
    portfolio = result.get("portfolio", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 자산", f"₩{portfolio.get('total_value', 0):,.0f}")
    
    with col2:
        profit = portfolio.get('profit_loss', 0)
        profit_pct = portfolio.get('profit_loss_pct', 0)
        st.metric("수익/손실", f"₩{profit:,.0f}", f"{profit_pct:+.2f}%")
    
    with col3:
        st.metric("총 거래", portfolio.get('total_trades', 0))
    
    with col4:
        signals = result.get('signals', {})
        st.metric("매수/매도", f"{signals.get('buy', 0)} / {signals.get('sell', 0)}")
    
    st.divider()
    
    # 캔들 차트
    st.subheader(f"📊 {result.get('symbol', '')} 가격 차트")
    
    df = pd.DataFrame(candles)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="가격",
    ))
    fig.update_layout(xaxis_rangeslider_visible=False, height=400)
    st.plotly_chart(fig, use_container_width=True)


def show_strategy_comparison():
    """전략 비교 표시"""
    st.subheader("📊 전략별 수익률 비교")
    
    if "comparison_results" not in st.session_state:
        st.info("'전체 전략 비교' 버튼을 클릭하세요.")
        return
    
    data = st.session_state.comparison_results
    results = data["results"]
    
    comparison = []
    for r in results:
        if "error" in r:
            continue
        portfolio = r.get("portfolio", {})
        comparison.append({
            "전략": STRATEGIES[r["strategy"]].display_name,
            "총 자산": f"₩{portfolio.get('total_value', 0):,.0f}",
            "수익률": f"{portfolio.get('profit_loss_pct', 0):+.2f}%",
            "수익금": f"₩{portfolio.get('profit_loss', 0):,.0f}",
            "거래 횟수": portfolio.get('total_trades', 0),
        })
    
    if not comparison:
        st.warning("비교 결과가 없습니다.")
        return
    
    comparison.sort(
        key=lambda x: float(x["수익률"].replace("%", "").replace("+", "")),
        reverse=True,
    )
    
    df = pd.DataFrame(comparison)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 차트
    returns = [float(c["수익률"].replace("%", "").replace("+", "")) for c in comparison]
    strategies = [c["전략"] for c in comparison]
    colors = ["green" if r >= 0 else "red" for r in returns]
    
    fig = go.Figure(data=[
        go.Bar(x=strategies, y=returns, marker_color=colors,
               text=[f"{r:+.2f}%" for r in returns], textposition="outside")
    ])
    fig.update_layout(title="전략별 수익률", yaxis_title="%", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    best = comparison[0]
    st.success(f"🏆 최고 성과: **{best['전략']}** ({best['수익률']})")


if __name__ == "__main__":
    main()
