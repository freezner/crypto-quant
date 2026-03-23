"""
FastAPI 서버 - WebSocket 실시간 시세 브로드캐스트
"""
import asyncio
import json
from typing import Set
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import SUPPORTED_COINS
from exchanges.websocket import get_websocket, WEBSOCKETS
from exchanges.websocket.base import price_store, TickerUpdate


# 연결된 클라이언트 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[WS] 클라이언트 연결 (총 {len(self.active_connections)}명)")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"[WS] 클라이언트 연결 해제 (총 {len(self.active_connections)}명)")
    
    async def broadcast(self, message: dict):
        """모든 클라이언트에 메시지 전송"""
        if not self.active_connections:
            return
        
        data = json.dumps(message, ensure_ascii=False)
        dead_connections = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                dead_connections.add(connection)
        
        # 죽은 연결 제거
        self.active_connections -= dead_connections


manager = ConnectionManager()

# 거래소 WebSocket 클라이언트들
exchange_clients = {}


async def start_exchange_websockets():
    """거래소 WebSocket 연결 시작"""
    print("[Server] 거래소 WebSocket 연결 시작...")
    
    for exchange_name in ["upbit", "bithumb"]:
        try:
            ws = get_websocket(exchange_name)
            ws.start(SUPPORTED_COINS)
            exchange_clients[exchange_name] = ws
            print(f"[{exchange_name}] WebSocket 시작됨")
        except Exception as e:
            print(f"[{exchange_name}] WebSocket 시작 실패: {e}")
    
    # 연결 대기
    await asyncio.sleep(2)


async def stop_exchange_websockets():
    """거래소 WebSocket 연결 중지"""
    print("[Server] 거래소 WebSocket 연결 중지...")
    for name, ws in exchange_clients.items():
        try:
            ws.stop()
        except Exception:
            pass


async def broadcast_prices():
    """가격 업데이트 브로드캐스트 루프"""
    last_prices = {}
    
    while True:
        try:
            all_prices = price_store.get_all()
            
            # 변경된 가격만 전송
            updates = []
            for ticker in all_prices:
                key = f"{ticker.exchange}:{ticker.symbol}"
                
                if key not in last_prices or last_prices[key] != ticker.price:
                    last_prices[key] = ticker.price
                    updates.append({
                        "symbol": ticker.symbol,
                        "exchange": ticker.exchange,
                        "price": ticker.price,
                        "change_pct": ticker.change_pct,
                        "timestamp": ticker.timestamp.isoformat(),
                    })
            
            if updates:
                await manager.broadcast({
                    "type": "price_update",
                    "data": updates,
                    "server_time": datetime.now().isoformat(),
                })
            
            await asyncio.sleep(0.1)  # 100ms 간격
            
        except Exception as e:
            print(f"[Broadcast] 오류: {e}")
            await asyncio.sleep(1)


# Lifespan 컨텍스트 매니저
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    await start_exchange_websockets()
    
    # 브로드캐스트 태스크 시작
    broadcast_task = asyncio.create_task(broadcast_prices())
    
    yield
    
    # 종료 시
    broadcast_task.cancel()
    await stop_exchange_websockets()


# FastAPI 앱
app = FastAPI(
    title="Crypto Quant - Realtime API",
    lifespan=lifespan,
)

# 정적 파일 서빙
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """메인 페이지 - 실시간 대시보드"""
    return FileResponse(static_path / "realtime.html")


@app.get("/health")
async def health():
    """헬스 체크"""
    return {
        "status": "ok",
        "connections": len(manager.active_connections),
        "exchanges": {
            name: ws.is_connected 
            for name, ws in exchange_clients.items()
        },
        "prices_count": len(price_store.get_all()),
    }


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """실시간 가격 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    
    try:
        # 초기 데이터 전송
        all_prices = price_store.get_all()
        if all_prices:
            await websocket.send_json({
                "type": "initial",
                "data": [
                    {
                        "symbol": t.symbol,
                        "exchange": t.exchange,
                        "price": t.price,
                        "change_pct": t.change_pct,
                        "timestamp": t.timestamp.isoformat(),
                    }
                    for t in all_prices
                ],
            })
        
        # 연결 유지 (ping/pong)
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30
                )
                # 클라이언트 메시지 처리 (ping 등)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # 타임아웃 시 ping 전송
                await websocket.send_text("ping")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS] 오류: {e}")
        manager.disconnect(websocket)


@app.get("/api/prices")
async def get_prices():
    """현재 가격 REST API"""
    all_prices = price_store.get_all()
    return {
        "prices": [
            {
                "symbol": t.symbol,
                "exchange": t.exchange,
                "price": t.price,
                "change_pct": t.change_pct,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in all_prices
        ],
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
