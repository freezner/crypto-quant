"""
빗썸 WebSocket 클라이언트
문서: https://apidocs.bithumb.com/docs/websocket_public
"""
import json
from datetime import datetime
from typing import List
import websockets
import logging

from exchanges.websocket.base import WebSocketBase, TickerUpdate, price_store

logger = logging.getLogger(__name__)


class BithumbWebSocket(WebSocketBase):
    """빗썸 WebSocket"""
    
    name = "bithumb"
    ws_url = "wss://pubwss.bithumb.com/pub/ws"
    
    def __init__(self):
        super().__init__()
        self._prev_prices = {}  # 변동률 계산용
    
    async def _connect(self):
        """웹소켓 연결"""
        logger.info(f"[bithumb] WebSocket 연결 중: {self.ws_url}")
        self._ws = await websockets.connect(
            self.ws_url,
            ping_interval=30,
            ping_timeout=10,
        )
        self.is_connected = True
        logger.info("[bithumb] WebSocket 연결 성공")
    
    async def _subscribe(self, symbols: List[str]):
        """시세 구독"""
        # 빗썸 형식: ["BTC_KRW", "ETH_KRW"]
        codes = [f"{s.upper()}_KRW" for s in symbols]
        
        # Ticker 구독
        subscribe_msg = {
            "type": "ticker",
            "symbols": codes,
            "tickTypes": ["24H"],  # 24시간 통계
        }
        
        await self._ws.send(json.dumps(subscribe_msg))
        logger.info(f"[bithumb] 구독: {codes}")
        
        # Transaction (체결) 구독 - 더 빠른 업데이트
        transaction_msg = {
            "type": "transaction",
            "symbols": codes,
        }
        await self._ws.send(json.dumps(transaction_msg))
    
    async def _handle_message(self, message):
        """메시지 처리"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "ticker":
                await self._handle_ticker(data)
            elif msg_type == "transaction":
                await self._handle_transaction(data)
                
        except json.JSONDecodeError:
            logger.warning(f"[bithumb] JSON 파싱 실패: {message[:100]}")
        except Exception as e:
            logger.error(f"[bithumb] 메시지 처리 오류: {e}")
    
    async def _handle_ticker(self, data: dict):
        """Ticker 메시지 처리"""
        content = data.get("content", {})
        symbol_raw = content.get("symbol", "")
        
        if not symbol_raw or "_KRW" not in symbol_raw:
            return
        
        symbol = symbol_raw.replace("_KRW", "")
        
        closing_price = float(content.get("closePrice", 0))
        prev_price = float(content.get("prevClosePrice", closing_price))
        
        # 변동률 계산
        change_pct = ((closing_price - prev_price) / prev_price * 100) if prev_price else 0
        
        ticker = TickerUpdate(
            symbol=symbol,
            price=closing_price,
            volume=float(content.get("volume", 0)),
            change_pct=change_pct,
            timestamp=datetime.now(),
            exchange=self.name,
            bid_price=float(content.get("buyPrice", 0)),
            ask_price=float(content.get("sellPrice", 0)),
        )
        
        price_store.update(ticker)
        self._prev_prices[symbol] = closing_price
    
    async def _handle_transaction(self, data: dict):
        """Transaction (체결) 메시지 처리"""
        content = data.get("content", {})
        
        if not content or "list" not in content:
            return
        
        for tx in content.get("list", []):
            symbol_raw = tx.get("symbol", "")
            if "_KRW" not in symbol_raw:
                continue
            
            symbol = symbol_raw.replace("_KRW", "")
            price = float(tx.get("contPrice", 0))
            
            if price <= 0:
                continue
            
            # 이전 가격으로 변동률 계산
            prev_price = self._prev_prices.get(symbol, price)
            change_pct = ((price - prev_price) / prev_price * 100) if prev_price else 0
            
            ticker = TickerUpdate(
                symbol=symbol,
                price=price,
                volume=float(tx.get("contQty", 0)),
                change_pct=change_pct,
                timestamp=datetime.now(),
                exchange=self.name,
                trade_volume=float(tx.get("contQty", 0)),
            )
            
            price_store.update(ticker)
