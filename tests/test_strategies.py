"""
전략 테스트
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies import get_strategy, list_strategies
from strategies.base import Signal


def generate_mock_candles(days: int = 50, trend: str = "up") -> list:
    """테스트용 캔들 데이터 생성"""
    candles = []
    base_price = 50000000  # 5천만원
    
    for i in range(days):
        if trend == "up":
            price = base_price * (1 + i * 0.01)  # 1%씩 상승
        elif trend == "down":
            price = base_price * (1 - i * 0.01)  # 1%씩 하락
        else:
            price = base_price * (1 + np.sin(i / 5) * 0.1)  # 횡보
        
        candles.append({
            "timestamp": (datetime.now() - timedelta(days=days-i)).isoformat(),
            "open": price * 0.99,
            "high": price * 1.02,
            "low": price * 0.98,
            "close": price,
            "volume": 1000 + i * 10,
        })
    
    return candles


class TestStrategies:
    """전략 테스트"""
    
    def test_list_strategies(self):
        """전략 목록 조회"""
        strategies = list_strategies()
        assert len(strategies) >= 4
        
        names = [s["name"] for s in strategies]
        assert "sma_cross" in names
        assert "rsi" in names
        assert "bollinger" in names
        assert "macd" in names
    
    def test_sma_cross_strategy(self):
        """SMA 교차 전략 테스트"""
        strategy = get_strategy("sma_cross")
        candles = generate_mock_candles(50, trend="up")
        
        signal = strategy.analyze(candles, "BTC")
        
        assert signal is not None
        assert signal.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        assert signal.symbol == "BTC"
        assert signal.price > 0
    
    def test_rsi_strategy(self):
        """RSI 전략 테스트"""
        strategy = get_strategy("rsi")
        candles = generate_mock_candles(50, trend="sideways")
        
        signal = strategy.analyze(candles, "ETH")
        
        assert signal is not None
        assert signal.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        assert signal.symbol == "ETH"
    
    def test_bollinger_strategy(self):
        """볼린저 밴드 전략 테스트"""
        strategy = get_strategy("bollinger")
        candles = generate_mock_candles(50, trend="sideways")
        
        signal = strategy.analyze(candles, "XRP")
        
        assert signal is not None
        assert signal.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
    
    def test_macd_strategy(self):
        """MACD 전략 테스트"""
        strategy = get_strategy("macd")
        candles = generate_mock_candles(50, trend="up")
        
        signal = strategy.analyze(candles, "SOL")
        
        assert signal is not None
        assert signal.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
    
    def test_insufficient_data(self):
        """데이터 부족 시 처리"""
        strategy = get_strategy("sma_cross")
        candles = generate_mock_candles(5)  # 5개만
        
        signal = strategy.analyze(candles, "BTC")
        
        assert signal.signal == Signal.HOLD
        assert "부족" in signal.reason or "계산" in signal.reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
