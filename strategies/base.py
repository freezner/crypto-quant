"""
전략 기본 인터페이스
모든 퀀트 전략은 이 클래스를 상속받아 구현합니다.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Signal(Enum):
    """매매 신호"""
    BUY = "buy"       # 매수
    SELL = "sell"     # 매도
    HOLD = "hold"     # 관망


@dataclass
class TradeSignal:
    """매매 신호 데이터 클래스"""
    signal: Signal              # 매매 신호
    symbol: str                 # 코인 심볼
    price: float                # 현재가
    confidence: float = 1.0     # 신뢰도 (0.0 ~ 1.0)
    reason: str = ""            # 신호 발생 이유
    timestamp: str = ""         # 시간
    
    def __str__(self):
        return f"[{self.signal.value.upper()}] {self.symbol} @ {self.price:,.0f} ({self.reason})"


class StrategyBase(ABC):
    """전략 기본 클래스"""
    
    name: str = "base"
    display_name: str = "기본 전략"
    description: str = "전략 설명"
    
    def __init__(self, **params):
        """
        전략 초기화
        
        Args:
            **params: 전략별 파라미터
        """
        self.params = params
        self._last_signal: Optional[TradeSignal] = None
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 계산
        
        Args:
            df: OHLCV 데이터프레임
                columns: [timestamp, open, high, low, close, volume]
                
        Returns:
            지표가 추가된 데이터프레임
        """
        pass
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        """
        매매 신호 생성
        
        Args:
            df: 지표가 계산된 데이터프레임
            
        Returns:
            TradeSignal 객체
        """
        pass
    
    def analyze(self, candles: List[dict], symbol: str = "BTC") -> TradeSignal:
        """
        캔들 데이터 분석하여 매매 신호 생성
        
        Args:
            candles: 캔들 데이터 리스트
            symbol: 코인 심볼
            
        Returns:
            TradeSignal 객체
        """
        if not candles or len(candles) < 2:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=0,
                reason="데이터 부족"
            )
        
        # DataFrame 변환
        df = pd.DataFrame(candles)
        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)
        
        # 지표 계산
        df = self.calculate_indicators(df)
        
        # 신호 생성
        signal = self.generate_signal(df)
        signal.symbol = symbol
        signal.price = df["close"].iloc[-1]
        signal.timestamp = str(df["timestamp"].iloc[-1]) if "timestamp" in df else ""
        
        self._last_signal = signal
        return signal
    
    def get_params(self) -> dict:
        """현재 파라미터 반환"""
        return self.params.copy()
    
    def set_params(self, **params):
        """파라미터 설정"""
        self.params.update(params)
    
    def get_info(self) -> dict:
        """전략 정보 반환"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "params": self.get_params(),
        }
