"""
거래소 WebSocket 모듈
실시간 시세 스트리밍
"""
from exchanges.websocket.base import WebSocketBase, TickerUpdate
from exchanges.websocket.upbit_ws import UpbitWebSocket
from exchanges.websocket.bithumb_ws import BithumbWebSocket
from exchanges.websocket.coinone_ws import CoinoneWebSocket

# 지원 거래소 웹소켓
WEBSOCKETS = {
    "upbit": UpbitWebSocket,
    "bithumb": BithumbWebSocket,
    "coinone": CoinoneWebSocket,
}


def get_websocket(name: str) -> WebSocketBase:
    """웹소켓 클라이언트 인스턴스 반환"""
    name = name.lower()
    if name not in WEBSOCKETS:
        raise ValueError(f"웹소켓 지원하지 않는 거래소: {name}")
    return WEBSOCKETS[name]()


__all__ = ["get_websocket", "WebSocketBase", "TickerUpdate", "WEBSOCKETS"]
