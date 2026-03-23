"""
RSI (Relative Strength Index) 전략

전략 설명:
- RSI가 과매도 구간(30 이하)에서 반등 → 매수
- RSI가 과매수 구간(70 이상)에서 하락 → 매도
"""
import pandas as pd
import numpy as np
from strategies.base import StrategyBase, Signal, TradeSignal
from app.config import STRATEGY_DEFAULTS


class RSIStrategy(StrategyBase):
    """RSI 전략"""
    
    name = "rsi"
    display_name = "RSI 과매수/과매도"
    description = "RSI 지표로 과매수/과매도 구간 매매"
    
    def __init__(self, **params):
        defaults = STRATEGY_DEFAULTS["rsi"]
        self.period = params.get("period", defaults["period"])
        self.oversold = params.get("oversold", defaults["oversold"])
        self.overbought = params.get("overbought", defaults["overbought"])
        super().__init__(
            period=self.period,
            oversold=self.oversold,
            overbought=self.overbought,
        )
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI 지표 계산"""
        df = df.copy()
        
        # 가격 변화
        delta = df["close"].diff()
        
        # 상승/하락 분리
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        # 평균 계산 (EMA 방식)
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()
        
        # RSI 계산
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # 이전 RSI
        df["rsi_prev"] = df["rsi"].shift(1)
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        """매매 신호 생성"""
        if len(df) < self.period + 2:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason=f"데이터 부족 (최소 {self.period + 2}개 필요)",
            )
        
        current = df.iloc[-1]
        rsi = current["rsi"]
        rsi_prev = current["rsi_prev"]
        
        # NaN 체크
        if pd.isna(rsi) or pd.isna(rsi_prev):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason="지표 계산 중",
            )
        
        # 과매도 구간에서 반등 (매수 신호)
        if rsi_prev < self.oversold and rsi >= self.oversold:
            return TradeSignal(
                signal=Signal.BUY,
                symbol="",
                price=0,
                confidence=0.7 + (self.oversold - rsi_prev) / 100,
                reason=f"과매도 반등 (RSI: {rsi:.1f})",
            )
        
        # 과매수 구간에서 하락 (매도 신호)
        if rsi_prev > self.overbought and rsi <= self.overbought:
            return TradeSignal(
                signal=Signal.SELL,
                symbol="",
                price=0,
                confidence=0.7 + (rsi_prev - self.overbought) / 100,
                reason=f"과매수 하락 (RSI: {rsi:.1f})",
            )
        
        # 현재 상태
        if rsi < self.oversold:
            status = f"과매도 구간 (RSI: {rsi:.1f})"
        elif rsi > self.overbought:
            status = f"과매수 구간 (RSI: {rsi:.1f})"
        else:
            status = f"중립 (RSI: {rsi:.1f})"
        
        return TradeSignal(
            signal=Signal.HOLD,
            symbol="",
            price=0,
            reason=status,
        )
