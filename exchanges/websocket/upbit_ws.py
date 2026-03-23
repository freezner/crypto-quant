"""
업비트 WebSocket 클라이언트
문서: https://docs.upbit.com/docs/upbit-quotation-websocket
"""
import json
import uuid
from datetime import datetime
from typing import List
import websockets
import logging

from exchanges.websocket.base import WebSocketBase, TickerUpdate, price_store

logger = logging.getLogger(__name__)


class UpbitWebSocket(WebSocketBase):
    """업비트 WebSocket"""
    
    name = "upbit"
    ws_url = "wss://api.upbit.com/websocket/v1"
    
    async def _connect(self):
        """웹소켓 연결"""
        logger.info(f"[upbit] WebSocket 연결 중: {self.ws_url}")
        self._ws = await websockets.connect(
            self.ws_url,
            ping_interval=30,
            ping_timeout=10,
        )
        self.is_connected = True
        logger.info("[upbit] WebSocket 연결 성공")
    
    async def _subscribe(self, symbols: List[str]):
        """시세 구독"""
        # 마켓 코드 변환 (BTC -> KRW-BTC)
        codes = [f"KRW-{s.upper()}" for s in symbols]
        
        # 구독 메시지
        subscribe_msg = [
            {"ticket": str(uuid.uuid4())},
            {
                "type": "ticker",
                "codes": codes,
                "isOnlyRealtime": True,
            },
            {"format": "SIMPLE"},  # 간소화된 필드명
        ]
        
        await self._ws.send(json.dumps(subscribe_msg))
        logger.info(f"[upbit] 구독: {codes}")
    
    async def _handle_message(self, message):
        """메시지 처리"""
        try:
            # 바이너리 메시지 디코딩
            if isinstance(message, bytes):
                data = json.loads(message.decode('utf-8'))
            else:
                data = json.loads(message)
            
            # 시세 업데이트 파싱
            if data.get("ty") == "ticker":
                ticker = TickerUpdate(
                    symbol=data["cd"].replace("KRW-", ""),  # KRW-BTC -> BTC
                    price=float(data["tp"]),                 # trade_price
                    volume=float(data.get("atv24h", 0)),     # acc_trade_volume_24h
                    change_pct=float(data.get("scr", 0)) * 100,  # signed_change_rate
                    timestamp=datetime.fromtimestamp(data["tms"] / 1000),
                    exchange=self.name,
                    bid_price=float(data.get("bp", 0)),      # best_bid_price
                    ask_price=float(data.get("ap", 0)),      # best_ask_price
                    trade_volume=float(data.get("tv", 0)),   # trade_volume
                )
                
                # 가격 저장소 업데이트
                price_store.update(ticker)
                
        except json.JSONDecodeError:
            logger.warning(f"[upbit] JSON 파싱 실패: {message[:100]}")
        except Exception as e:
            logger.error(f"[upbit] 메시지 처리 오류: {e}")
