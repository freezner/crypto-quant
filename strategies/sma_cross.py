"""
SMA 교차 전략 (이동평균선 골든크로스/데드크로스)

전략 설명:
- 단기 이동평균선이 장기 이동평균선을 상향 돌파 → 매수 (골든크로스)
- 단기 이동평균선이 장기 이동평균선을 하향 돌파 → 매도 (데드크로스)
"""
import pandas as pd
from strategies.base import StrategyBase, Signal, TradeSignal
from app.config import STRATEGY_DEFAULTS


class SMACrossStrategy(StrategyBase):
    """SMA 교차 전략"""
    
    name = "sma_cross"
    display_name = "이동평균 교차"
    description = "단기/장기 이동평균선 교차 시점에 매매"
    
    def __init__(self, **params):
        defaults = STRATEGY_DEFAULTS["sma_cross"]
        self.short_window = params.get("short_window", defaults["short_window"])
        self.long_window = params.get("long_window", defaults["long_window"])
        super().__init__(
            short_window=self.short_window,
            long_window=self.long_window,
        )
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """SMA 지표 계산"""
        df = df.copy()
        
        # 단기/장기 이동평균
        df["sma_short"] = df["close"].rolling(window=self.short_window).mean()
        df["sma_long"] = df["close"].rolling(window=self.long_window).mean()
        
        # 크로스 감지
        df["cross"] = df["sma_short"] - df["sma_long"]
        df["cross_prev"] = df["cross"].shift(1)
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        """매매 신호 생성"""
        if len(df) < self.long_window + 1:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason=f"데이터 부족 (최소 {self.long_window + 1}개 필요)",
            )
        
        current = df.iloc[-1]
        
        # NaN 체크
        if pd.isna(current["cross"]) or pd.isna(current["cross_prev"]):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason="지표 계산 중",
            )
        
        # 골든크로스 (단기 > 장기, 이전에는 단기 < 장기)
        if current["cross"] > 0 and current["cross_prev"] <= 0:
            return TradeSignal(
                signal=Signal.BUY,
                symbol="",
                price=0,
                confidence=0.8,
                reason=f"골든크로스 (SMA{self.short_window} > SMA{self.long_window})",
            )
        
        # 데드크로스 (단기 < 장기, 이전에는 단기 > 장기)
        if current["cross"] < 0 and current["cross_prev"] >= 0:
            return TradeSignal(
                signal=Signal.SELL,
                symbol="",
                price=0,
                confidence=0.8,
                reason=f"데드크로스 (SMA{self.short_window} < SMA{self.long_window})",
            )
        
        # 관망
        position = "상승 추세" if current["cross"] > 0 else "하락 추세"
        return TradeSignal(
            signal=Signal.HOLD,
            symbol="",
            price=0,
            reason=f"신호 없음 ({position})",
        )
