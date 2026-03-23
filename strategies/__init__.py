"""
퀀트 전략 모듈
새로운 전략 추가: base.py의 StrategyBase 상속하여 구현
"""
from strategies.base import StrategyBase, Signal
from strategies.sma_cross import SMACrossStrategy
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerStrategy
from strategies.macd import MACDStrategy

# 지원 전략 목록
STRATEGIES = {
    "sma_cross": SMACrossStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "macd": MACDStrategy,
}


def get_strategy(name: str, **params) -> StrategyBase:
    """전략 인스턴스 반환"""
    name = name.lower()
    if name not in STRATEGIES:
        raise ValueError(f"지원하지 않는 전략: {name}")
    return STRATEGIES[name](**params)


def get_all_strategies(**params) -> list:
    """모든 전략 인스턴스 반환"""
    return [cls(**params) for cls in STRATEGIES.values()]


def list_strategies() -> list:
    """전략 정보 목록 반환"""
    return [
        {
            "name": name,
            "display_name": cls.display_name,
            "description": cls.description,
        }
        for name, cls in STRATEGIES.items()
    ]
