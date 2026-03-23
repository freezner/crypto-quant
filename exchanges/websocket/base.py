"""
WebSocket 기본 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Callable, List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import threading
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class TickerUpdate:
    """실시간 시세 업데이트"""
    symbol: str
    price: float
    volume: float
    change_pct: float
    timestamp: datetime
    exchange: str
    bid_price: float = 0       # 매수 호가
    ask_price: float = 0       # 매도 호가
    trade_volume: float = 0    # 체결량
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "change_pct": self.change_pct,
            "timestamp": self.timestamp.isoformat(),
            "exchange": self.exchange,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
        }


class PriceStore:
    """스레드 안전한 가격 저장소"""
    
    def __init__(self):
        self._prices: Dict[str, TickerUpdate] = {}
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
    
    def update(self, ticker: TickerUpdate):
        """가격 업데이트"""
        with self._lock:
            key = f"{ticker.exchange}:{ticker.symbol}"
            self._prices[key] = ticker
        
        # 콜백 실행
        for callback in self._callbacks:
            try:
                callback(ticker)
            except Exception as e:
                logger.error(f"콜백 실행 실패: {e}")
    
    def get(self, exchange: str, symbol: str) -> Optional[TickerUpdate]:
        """가격 조회"""
        with self._lock:
            return self._prices.get(f"{exchange}:{symbol}")
    
    def get_all(self, exchange: str = None) -> List[TickerUpdate]:
        """전체 가격 조회"""
        with self._lock:
            if exchange:
                return [t for t in self._prices.values() if t.exchange == exchange]
            return list(self._prices.values())
    
    def add_callback(self, callback: Callable):
        """업데이트 콜백 추가"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """콜백 제거"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


# 전역 가격 저장소
price_store = PriceStore()


class WebSocketBase(ABC):
    """WebSocket 기본 클래스"""
    
    name: str = "base"
    ws_url: str = ""
    
    def __init__(self):
        self.is_connected = False
        self.is_running = False
        self._ws = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._symbols: List[str] = []
    
    @abstractmethod
    async def _connect(self):
        """웹소켓 연결"""
        pass
    
    @abstractmethod
    async def _subscribe(self, symbols: List[str]):
        """심볼 구독"""
        pass
    
    @abstractmethod
    async def _handle_message(self, message: str):
        """메시지 처리"""
        pass
    
    async def _run_async(self, symbols: List[str]):
        """비동기 실행 루프"""
        self._symbols = symbols
        self.is_running = True
        
        while self.is_running:
            try:
                await self._connect()
                await self._subscribe(symbols)
                
                # 메시지 수신 루프
                async for message in self._ws:
                    if not self.is_running:
                        break
                    await self._handle_message(message)
                    
            except Exception as e:
                logger.error(f"[{self.name}] WebSocket 오류: {e}")
                self.is_connected = False
                if self.is_running:
                    await asyncio.sleep(5)  # 재연결 대기
    
    def _run_in_thread(self, symbols: List[str]):
        """스레드에서 실행"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_async(symbols))
        finally:
            self._loop.close()
    
    def start(self, symbols: List[str]):
        """웹소켓 시작 (백그라운드 스레드)"""
        if self._thread and self._thread.is_alive():
            logger.warning(f"[{self.name}] 이미 실행 중")
            return
        
        logger.info(f"[{self.name}] WebSocket 시작: {symbols}")
        self._thread = threading.Thread(
            target=self._run_in_thread,
            args=(symbols,),
            daemon=True,
        )
        self._thread.start()
    
    def stop(self):
        """웹소켓 중지"""
        logger.info(f"[{self.name}] WebSocket 중지")
        self.is_running = False
        self.is_connected = False
        
        if self._ws:
            try:
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._ws.close(),
                        self._loop
                    )
            except Exception:
                pass
    
    def get_prices(self) -> List[TickerUpdate]:
        """현재 가격 조회"""
        return price_store.get_all(self.name)
    
    def get_price(self, symbol: str) -> Optional[TickerUpdate]:
        """특정 심볼 가격 조회"""
        return price_store.get(self.name, symbol)
