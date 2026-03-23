"""
거래소 기본 인터페이스
모든 거래소 클래스는 이 클래스를 상속받아 구현합니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests
import logging

logger = logging.getLogger(__name__)


@dataclass
class Ticker:
    """시세 정보 데이터 클래스"""
    symbol: str           # 코인 심볼 (BTC, ETH 등)
    price: float          # 현재가 (KRW)
    volume_24h: float     # 24시간 거래량
    change_24h: float     # 24시간 변동률 (%)
    high_24h: float       # 24시간 최고가
    low_24h: float        # 24시간 최저가
    exchange: str         # 거래소 이름
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume_24h": self.volume_24h,
            "change_24h": self.change_24h,
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "exchange": self.exchange,
        }


class ExchangeBase(ABC):
    """거래소 기본 클래스"""
    
    name: str = "base"
    base_url: str = ""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CryptoQuantSimulator/1.0"
        })
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """GET 요청 헬퍼"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"[{self.name}] API 요청 실패: {e}")
            raise
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """
        단일 코인 시세 조회
        
        Args:
            symbol: 코인 심볼 (예: "BTC", "ETH")
            
        Returns:
            Ticker 객체 또는 None
        """
        pass
    
    @abstractmethod
    def get_tickers(self, symbols: List[str] = None) -> List[Ticker]:
        """
        여러 코인 시세 조회
        
        Args:
            symbols: 코인 심볼 리스트 (None이면 전체)
            
        Returns:
            Ticker 리스트
        """
        pass
    
    @abstractmethod
    def get_orderbook(self, symbol: str) -> dict:
        """
        호가창 조회
        
        Args:
            symbol: 코인 심볼
            
        Returns:
            {"bids": [...], "asks": [...]}
        """
        pass
    
    def get_candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> List[dict]:
        """
        캔들(OHLCV) 데이터 조회
        기본 구현 - 필요시 오버라이드
        
        Args:
            symbol: 코인 심볼
            interval: 캔들 간격 (1m, 5m, 1h, 1d 등)
            limit: 조회 개수
            
        Returns:
            [{"timestamp", "open", "high", "low", "close", "volume"}, ...]
        """
        raise NotImplementedError(f"[{self.name}] 캔들 조회 미구현")
