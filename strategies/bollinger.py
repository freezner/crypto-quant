"""
볼린저 밴드 전략

전략 설명:
- 가격이 하단 밴드 터치 후 반등 → 매수
- 가격이 상단 밴드 터치 후 하락 → 매도
"""
import pandas as pd
from strategies.base import StrategyBase, Signal, TradeSignal
from app.config import STRATEGY_DEFAULTS


class BollingerStrategy(StrategyBase):
    """볼린저 밴드 전략"""
    
    name = "bollinger"
    display_name = "볼린저 밴드"
    description = "볼린저 밴드 상/하단 터치 시 매매"
    
    def __init__(self, **params):
        defaults = STRATEGY_DEFAULTS["bollinger"]
        self.period = params.get("period", defaults["period"])
        self.std_dev = params.get("std_dev", defaults["std_dev"])
        super().__init__(
            period=self.period,
            std_dev=self.std_dev,
        )
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """볼린저 밴드 지표 계산"""
        df = df.copy()
        
        # 중심선 (SMA)
        df["bb_middle"] = df["close"].rolling(window=self.period).mean()
        
        # 표준편차
        rolling_std = df["close"].rolling(window=self.period).std()
        
        # 상단/하단 밴드
        df["bb_upper"] = df["bb_middle"] + (rolling_std * self.std_dev)
        df["bb_lower"] = df["bb_middle"] - (rolling_std * self.std_dev)
        
        # 밴드 위치 (0~1, 0=하단, 1=상단)
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
        df["bb_position_prev"] = df["bb_position"].shift(1)
        
        # 이전 종가
        df["close_prev"] = df["close"].shift(1)
        
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
        
        # NaN 체크
        if pd.isna(current["bb_position"]) or pd.isna(current["bb_position_prev"]):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol="",
                price=0,
                reason="지표 계산 중",
            )
        
        close = current["close"]
        bb_lower = current["bb_lower"]
        bb_upper = current["bb_upper"]
        bb_middle = current["bb_middle"]
        position = current["bb_position"]
        position_prev = current["bb_position_prev"]
        
        # 하단 밴드 터치 후 반등 (매수)
        if position_prev <= 0.05 and position > 0.05:
            return TradeSignal(
                signal=Signal.BUY,
                symbol="",
                price=0,
                confidence=0.75,
                reason=f"하단밴드 반등 (가격: {close:,.0f}, 하단: {bb_lower:,.0f})",
            )
        
        # 하단 밴드 아래로 하락 (강한 매수 기회)
        if position <= 0 and position_prev > 0:
            return TradeSignal(
                signal=Signal.BUY,
                symbol="",
                price=0,
                confidence=0.85,
                reason=f"하단밴드 이탈 (강한 과매도)",
            )
        
        # 상단 밴드 터치 후 하락 (매도)
        if position_prev >= 0.95 and position < 0.95:
            return TradeSignal(
                signal=Signal.SELL,
                symbol="",
                price=0,
                confidence=0.75,
                reason=f"상단밴드 이탈 (가격: {close:,.0f}, 상단: {bb_upper:,.0f})",
            )
        
        # 상단 밴드 위로 상승 (강한 매도 기회)
        if position >= 1 and position_prev < 1:
            return TradeSignal(
                signal=Signal.SELL,
                symbol="",
                price=0,
                confidence=0.85,
                reason=f"상단밴드 돌파 (강한 과매수)",
            )
        
        # 현재 상태
        if position < 0.2:
            status = "하단 근접"
        elif position > 0.8:
            status = "상단 근접"
        else:
            status = "밴드 내 중립"
        
        return TradeSignal(
            signal=Signal.HOLD,
            symbol="",
            price=0,
            reason=f"{status} (위치: {position:.1%})",
        )
