"""
코인원 실시간 시세 (REST API 폴링)
공개 WebSocket이 제한적이므로 폴링 방식으로 구현
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import List
import logging

from exchanges.websocket.base import WebSocketBase, TickerUpdate, price_store

logger = logging.getLogger(__name__)


class CoinoneWebSocket(WebSocketBase):
    """코인원 실시간 시세 (REST 폴링)"""
    
    name = "coinone"
    ws_url = "https://api.coinone.co.kr/public/v2/ticker_new/KRW"  # REST API
    poll_interval = 2  # 2초마다 폴링
    
    def __init__(self):
        super().__init__()
        self._session = None
        self._poll_symbols = []
        self._prev_prices = {}
    
    async def _connect(self):
        """HTTP 세션 생성"""
        logger.info(f"[coinone] REST 폴링 모드 시작")
        self._session = aiohttp.ClientSession()
        self.is_connected = True
        logger.info("[coinone] 연결 성공 (폴링 모드)")
    
    async def _subscribe(self, symbols: List[str]):
        """심볼 구독 (폴링 대상 설정)"""
        self._poll_symbols = [s.upper() for s in symbols]
        logger.info(f"[coinone] 구독: {self._poll_symbols}")
    
    async def _run_async(self, symbols: List[str]):
        """비동기 실행 루프 (폴링 방식으로 오버라이드)"""
        self._symbols = symbols
        self.is_running = True
        
        await self._connect()
        await self._subscribe(symbols)
        
        # 폴링 루프
        while self.is_running:
            try:
                await self._poll_prices()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[coinone] 폴링 오류: {e}")
                await asyncio.sleep(5)
        
        # 세션 종료
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _poll_prices(self):
        """REST API로 가격 조회"""
        if not self._session or not self._poll_symbols:
            return
        
        try:
            async with self._session.get(self.ws_url) as response:
                if response.status != 200:
                    return
                
                data = await response.json()
                
                if data.get("result") != "success":
                    return
                
                for item in data.get("tickers", []):
                    symbol = item.get("target_currency", "").upper()
                    
                    if symbol not in self._poll_symbols:
                        continue
                    
                    await self._handle_ticker(item)
                    
        except Exception as e:
            logger.error(f"[coinone] API 호출 오류: {e}")
    
    async def _handle_ticker(self, item: dict):
        """Ticker 데이터 처리"""
        symbol = item.get("target_currency", "").upper()
        
        last_price = float(item.get("last", 0))
        first_price = float(item.get("first", last_price))
        
        # 시가 대비 변동률
        change_pct = ((last_price - first_price) / first_price * 100) if first_price else 0
        
        ticker = TickerUpdate(
            symbol=symbol,
            price=last_price,
            volume=float(item.get("target_volume", 0)),
            change_pct=change_pct,
            timestamp=datetime.now(),
            exchange=self.name,
            bid_price=float(item.get("best_bids", [{}])[0].get("price", 0)) if item.get("best_bids") else 0,
            ask_price=float(item.get("best_asks", [{}])[0].get("price", 0)) if item.get("best_asks") else 0,
        )
        
        price_store.update(ticker)
        self._prev_prices[symbol] = last_price
    
    async def _handle_message(self, message):
        """WebSocket 메시지 처리 (폴링 모드에서는 미사용)"""
        pass
    
    def stop(self):
        """종료"""
        self.is_running = False
        self.is_connected = False
        logger.info("[coinone] 종료")
