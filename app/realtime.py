"""
실시간 시세 관리 모듈
WebSocket 연결 및 가격 스트리밍
"""
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from exchanges.websocket import get_websocket, WEBSOCKETS
from exchanges.websocket.base import price_store, TickerUpdate

logger = logging.getLogger(__name__)


class RealtimePriceManager:
    """실시간 가격 매니저 (싱글톤)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._websockets = {}
        self._is_running = False
        self._initialized = True
    
    def start(self, exchanges: List[str], symbols: List[str]):
        """웹소켓 연결 시작"""
        if self._is_running:
            logger.info("이미 실행 중")
            return
        
        self._is_running = True
        
        for exchange in exchanges:
            if exchange not in WEBSOCKETS:
                logger.warning(f"웹소켓 미지원 거래소: {exchange}")
                continue
            
            try:
                ws = get_websocket(exchange)
                ws.start(symbols)
                self._websockets[exchange] = ws
                logger.info(f"[{exchange}] WebSocket 시작")
            except Exception as e:
                logger.error(f"[{exchange}] WebSocket 시작 실패: {e}")
    
    def stop(self):
        """모든 웹소켓 중지"""
        self._is_running = False
        
        for name, ws in self._websockets.items():
            try:
                ws.stop()
                logger.info(f"[{name}] WebSocket 중지")
            except Exception as e:
                logger.error(f"[{name}] WebSocket 중지 실패: {e}")
        
        self._websockets.clear()
    
    def get_all_prices(self) -> List[TickerUpdate]:
        """모든 가격 조회"""
        return price_store.get_all()
    
    def get_prices_by_exchange(self, exchange: str) -> List[TickerUpdate]:
        """거래소별 가격 조회"""
        return price_store.get_all(exchange)
    
    def get_price(self, exchange: str, symbol: str) -> Optional[TickerUpdate]:
        """특정 가격 조회"""
        return price_store.get(exchange, symbol)
    
    def is_connected(self, exchange: str) -> bool:
        """연결 상태 확인"""
        ws = self._websockets.get(exchange)
        return ws.is_connected if ws else False
    
    def get_status(self) -> Dict:
        """전체 상태 조회"""
        return {
            "is_running": self._is_running,
            "exchanges": {
                name: {
                    "connected": ws.is_connected,
                    "prices_count": len(ws.get_prices()),
                }
                for name, ws in self._websockets.items()
            },
            "total_prices": len(self.get_all_prices()),
        }


# 전역 인스턴스
realtime_manager = RealtimePriceManager()


def format_price_for_display(ticker: TickerUpdate) -> dict:
    """표시용 가격 포맷"""
    change_emoji = "🟢" if ticker.change_pct >= 0 else "🔴"
    
    # 가격 포맷 (1억 이상이면 억 단위)
    if ticker.price >= 100_000_000:
        price_str = f"{ticker.price / 100_000_000:.2f}억"
    elif ticker.price >= 10_000:
        price_str = f"{ticker.price:,.0f}"
    else:
        price_str = f"{ticker.price:,.2f}"
    
    # 시간차 계산
    seconds_ago = (datetime.now() - ticker.timestamp).total_seconds()
    if seconds_ago < 1:
        time_str = "방금"
    elif seconds_ago < 60:
        time_str = f"{int(seconds_ago)}초 전"
    else:
        time_str = f"{int(seconds_ago / 60)}분 전"
    
    return {
        "symbol": ticker.symbol,
        "price": price_str,
        "price_raw": ticker.price,
        "change": f"{change_emoji} {ticker.change_pct:+.2f}%",
        "change_raw": ticker.change_pct,
        "exchange": ticker.exchange.upper(),
        "updated": time_str,
        "timestamp": ticker.timestamp,
    }
