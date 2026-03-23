"""
빗썸 거래소 API
문서: https://apidocs.bithumb.com/
"""
from typing import List, Optional
from exchanges.base import ExchangeBase, Ticker
import logging

logger = logging.getLogger(__name__)


class BithumbExchange(ExchangeBase):
    """빗썸 거래소"""
    
    name = "bithumb"
    base_url = "https://api.bithumb.com/public"
    
    def _to_market(self, symbol: str) -> str:
        """심볼을 빗썸 형식으로 변환"""
        return f"{symbol.upper()}_KRW"
    
    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """단일 코인 시세 조회"""
        try:
            market = self._to_market(symbol)
            data = self._get(f"/ticker/{market}")
            
            if data.get("status") != "0000":
                logger.warning(f"[bithumb] API 오류: {data.get('message')}")
                return None
            
            item = data["data"]
            
            # 변동률 계산
            closing = float(item.get("closing_price", 0))
            prev_closing = float(item.get("prev_closing_price", closing))
            change_pct = ((closing - prev_closing) / prev_closing * 100) if prev_closing else 0
            
            return Ticker(
                symbol=symbol.upper(),
                price=float(item.get("closing_price", 0)),
                volume_24h=float(item.get("units_traded_24H", 0)),
                change_24h=change_pct,
                high_24h=float(item.get("max_price", 0)),
                low_24h=float(item.get("min_price", 0)),
                exchange=self.name,
            )
        except Exception as e:
            logger.error(f"[bithumb] 시세 조회 실패 ({symbol}): {e}")
            return None
    
    def get_tickers(self, symbols: List[str] = None) -> List[Ticker]:
        """여러 코인 시세 조회"""
        try:
            # 전체 시세 조회
            data = self._get("/ticker/ALL_KRW")
            
            if data.get("status") != "0000":
                logger.warning(f"[bithumb] API 오류: {data.get('message')}")
                return []
            
            items = data.get("data", {})
            date_info = items.pop("date", None)  # date 필드 제거
            
            tickers = []
            for symbol, item in items.items():
                if symbols and symbol not in [s.upper() for s in symbols]:
                    continue
                
                if not isinstance(item, dict):
                    continue
                
                # 변동률 계산
                closing = float(item.get("closing_price", 0))
                prev_closing = float(item.get("prev_closing_price", closing))
                change_pct = ((closing - prev_closing) / prev_closing * 100) if prev_closing else 0
                
                tickers.append(Ticker(
                    symbol=symbol,
                    price=closing,
                    volume_24h=float(item.get("units_traded_24H", 0)),
                    change_24h=change_pct,
                    high_24h=float(item.get("max_price", 0)),
                    low_24h=float(item.get("min_price", 0)),
                    exchange=self.name,
                ))
            
            return tickers
            
        except Exception as e:
            logger.error(f"[bithumb] 시세 목록 조회 실패: {e}")
            return []
    
    def get_orderbook(self, symbol: str) -> dict:
        """호가창 조회"""
        try:
            market = self._to_market(symbol)
            data = self._get(f"/orderbook/{market}")
            
            if data.get("status") != "0000":
                return {"bids": [], "asks": []}
            
            orderbook = data.get("data", {})
            return {
                "bids": [
                    {"price": float(b["price"]), "quantity": float(b["quantity"])}
                    for b in orderbook.get("bids", [])
                ],
                "asks": [
                    {"price": float(a["price"]), "quantity": float(a["quantity"])}
                    for a in orderbook.get("asks", [])
                ],
            }
        except Exception as e:
            logger.error(f"[bithumb] 호가창 조회 실패 ({symbol}): {e}")
            return {"bids": [], "asks": []}
    
    def get_candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> List[dict]:
        """캔들 데이터 조회"""
        try:
            market = self._to_market(symbol)
            
            # 빗썸 차트 인터벌
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "10m": "10m",
                "30m": "30m",
                "1h": "1h",
                "6h": "6h",
                "12h": "12h",
                "1d": "24h",
            }
            
            chart_interval = interval_map.get(interval, "24h")
            data = self._get(f"/candlestick/{market}/{chart_interval}")
            
            if data.get("status") != "0000":
                return []
            
            candles = []
            items = data.get("data", [])[-limit:]  # 최근 limit개
            
            for item in items:
                # [timestamp, open, close, high, low, volume]
                candles.append({
                    "timestamp": item[0],
                    "open": float(item[1]),
                    "close": float(item[2]),
                    "high": float(item[3]),
                    "low": float(item[4]),
                    "volume": float(item[5]),
                })
            
            return candles
            
        except Exception as e:
            logger.error(f"[bithumb] 캔들 조회 실패 ({symbol}): {e}")
            return []
