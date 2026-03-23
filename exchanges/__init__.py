"""
거래소 API 모듈
새로운 거래소 추가: base.py의 ExchangeBase 상속하여 구현
"""
from exchanges.base import ExchangeBase
from exchanges.upbit import UpbitExchange
from exchanges.bithumb import BithumbExchange
from exchanges.coinone import CoinoneExchange

# 지원 거래소 목록
EXCHANGES = {
    "upbit": UpbitExchange,
    "bithumb": BithumbExchange,
    "coinone": CoinoneExchange,
}


def get_exchange(name: str) -> ExchangeBase:
    """거래소 인스턴스 반환"""
    name = name.lower()
    if name not in EXCHANGES:
        raise ValueError(f"지원하지 않는 거래소: {name}")
    return EXCHANGES[name]()


def get_all_exchanges() -> list:
    """모든 거래소 인스턴스 반환"""
    return [cls() for cls in EXCHANGES.values()]
