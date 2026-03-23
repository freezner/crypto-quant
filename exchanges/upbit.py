"""
업비트 거래소 API
문서: https://docs.upbit.com/
"""
from typing import List, Optional
from exchanges.base import ExchangeBase, Ticker
import logging

logger = logging.getLogger(__name__)


class UpbitExchange(ExchangeBase):
    """업비트 거래소"""
    
    name = "upbit"
    base_url = "https://api.upbit.com/v1"
    
    def _to_market(self, symbol: str) -> str:
        """심볼을 업비트 마켓 코드로 변환 (BTC -> KRW-BTC)"""
        return f"KRW-{symbol.upper()}"
    
    def _from_market(self, market: str) -> str:
        """업비트 마켓 코드를 심볼로 변환 (KRW-BTC -> BTC)"""
        if market.startswith("KRW-"):
            return market[4:]
        return market
    
    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """단일 코인 시세 조회"""
        try:
            market = self._to_market(symbol)
            data = self._get("/ticker", params={"markets": market})
            
            if not data:
                return None
            
            item = data[0]
            return Ticker(
                symbol=symbol.upper(),
                price=float(item["trade_price"]),
                volume_24h=float(item.get("acc_trade_volume_24h", 0)),
                change_24h=float(item.get("signed_change_rate", 0)) * 100,
                high_24h=float(item.get("high_price", 0)),
                low_24h=float(item.get("low_price", 0)),
                exchange=self.name,
            )
        except Exception as e:
            logger.error(f"[upbit] 시세 조회 실패 ({symbol}): {e}")
            return None
    
    def get_tickers(self, symbols: List[str] = None) -> List[Ticker]:
        """여러 코인 시세 조회"""
        try:
            # 마켓 목록 조회
            if symbols:
                markets = ",".join([self._to_market(s) for s in symbols])
            else:
                # KRW 마켓 전체 조회
                all_markets = self._get("/market/all")
                markets = ",".join([
                    m["market"] for m in all_markets 
                    if m["market"].startswith("KRW-")
                ])
            
            data = self._get("/ticker", params={"markets": markets})
            
            tickers = []
            for item in data:
                symbol = self._from_market(item["market"])
                tickers.append(Ticker(
                    symbol=symbol,
                    price=float(item["trade_price"]),
                    volume_24h=float(item.get("acc_trade_volume_24h", 0)),
                    change_24h=float(item.get("signed_change_rate", 0)) * 100,
                    high_24h=float(item.get("high_price", 0)),
                    low_24h=float(item.get("low_price", 0)),
                    exchange=self.name,
                ))
            
            return tickers
            
        except Exception as e:
            logger.error(f"[upbit] 시세 목록 조회 실패: {e}")
            return []
    
    def get_orderbook(self, symbol: str) -> dict:
        """호가창 조회"""
        try:
            market = self._to_market(symbol)
            data = self._get("/orderbook", params={"markets": market})
            
            if not data:
                return {"bids": [], "asks": []}
            
            units = data[0].get("orderbook_units", [])
            return {
                "bids": [{"price": u["bid_price"], "quantity": u["bid_size"]} for u in units],
                "asks": [{"price": u["ask_price"], "quantity": u["ask_size"]} for u in units],
            }
        except Exception as e:
            logger.error(f"[upbit] 호가창 조회 실패 ({symbol}): {e}")
            return {"bids": [], "asks": []}
    
    def get_candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> List[dict]:
        """캔들 데이터 조회"""
        try:
            market = self._to_market(symbol)
            
            # 인터벌 매핑
            interval_map = {
                "1m": ("minutes/1", limit),
                "5m": ("minutes/5", limit),
                "15m": ("minutes/15", limit),
                "1h": ("minutes/60", limit),
                "4h": ("minutes/240", limit),
                "1d": ("days", limit),
                "1w": ("weeks", limit),
                "1M": ("months", limit),
            }
            
            if interval not in interval_map:
                interval = "1d"
            
            endpoint, count = interval_map[interval]
            data = self._get(f"/candles/{endpoint}", params={
                "market": market,
                "count": count,
            })
            
            candles = []
            for item in reversed(data):  # 오래된 것부터
                candles.append({
                    "timestamp": item["candle_date_time_kst"],
                    "open": float(item["opening_price"]),
                    "high": float(item["high_price"]),
                    "low": float(item["low_price"]),
                    "close": float(item["trade_price"]),
                    "volume": float(item["candle_acc_trade_volume"]),
                })
            
            return candles
            
        except Exception as e:
            logger.error(f"[upbit] 캔들 조회 실패 ({symbol}): {e}")
            return []
