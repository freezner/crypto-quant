"""
MACD (Moving Average Convergence Divergence) 전략

전략 설명:
- MACD 라인이 시그널 라인을 상향 돌파 → 매수
- MACD 라인이 시그널 라인을 하향 돌파 → 매도
"""
import pandas as pd
from strategies.base import StrategyBase, Signal, TradeSignal
from app.config import STRATEGY_DEFAULTS


class MACDStrategy(StrategyBase):
    """MACD 전략"""
    
    name = "macd"
    display_name = "MACD"
    description = "MACD 시그널 교차 전략"
    
    def __init__(self, **params):
        defaults = STRATEGY_DEFAULTS["macd"]
        self.fast_period = params.get("fast_period", defaults["fast_period"])
        self.slow_period = params.get("slow_period", defaults["slow_period"])
        self.signal_period = params.get("signal_period", defaults["signal_period"])
        super().__init__(
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            signal_period=self.signal_period,
        )
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD 지표 계산"""
        df = df.copy()
        
        # EMA 계산
        ema_fast = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow_period, adjust=False).mean()
        
        # MACD 라인
        df["macd"] = ema_fast - ema_slow
        
        # 시그널 라인
        df["macd_signal"] = df["macd"].ewm(span=self.signal_period, adjust=False).mean()
        
        # 히스토그램
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        df["macd_hist_prev"] = df["macd_hist"].shift(1)
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        """매매 신호 생성"""
        min_periods = self.slow_period + self.signal_period
        if len(df) < min_periods + 2:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason=f"데이터 부족 (최소 {min_periods + 2}개 필요)",
            )
        
        current = df.iloc[-1]
        macd = current["macd"]
        signal_line = current["macd_signal"]
        hist = current["macd_hist"]
        hist_prev = current["macd_hist_prev"]
        
        # NaN 체크
        if pd.isna(hist) or pd.isna(hist_prev):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason="지표 계산 중",
            )
        
        # MACD 상향 돌파 (매수)
        if hist > 0 and hist_prev <= 0:
            confidence = min(0.9, 0.7 + abs(hist) / abs(macd) * 0.2) if macd != 0 else 0.7
            return TradeSignal(
                signal=Signal.BUY,
                symbol="",
                price=0,
                confidence=confidence,
                reason=f"MACD 골든크로스 (MACD: {macd:.2f}, Signal: {signal_line:.2f})",
            )
        
        # MACD 하향 돌파 (매도)
        if hist < 0 and hist_prev >= 0:
            confidence = min(0.9, 0.7 + abs(hist) / abs(macd) * 0.2) if macd != 0 else 0.7
            return TradeSignal(
                signal=Signal.SELL,
                symbol="",
                price=0,
                confidence=confidence,
                reason=f"MACD 데드크로스 (MACD: {macd:.2f}, Signal: {signal_line:.2f})",
            )
        
        # 현재 상태
        if hist > 0:
            status = f"상승 추세 (Histogram: {hist:.2f})"
        else:
            status = f"하락 추세 (Histogram: {hist:.2f})"
        
        return TradeSignal(
            signal=Signal.HOLD,
            symbol="",
            price=0,
            reason=status,
        )
