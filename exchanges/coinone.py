"""
코인원 거래소 API
문서: https://doc.coinone.co.kr/
"""
from typing import List, Optional
from exchanges.base import ExchangeBase, Ticker
import logging

logger = logging.getLogger(__name__)


class CoinoneExchange(ExchangeBase):
    """코인원 거래소"""
    
    name = "coinone"
    base_url = "https://api.coinone.co.kr"
    
    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """단일 코인 시세 조회"""
        try:
            data = self._get("/ticker", params={
                "currency": symbol.lower(),
                "quote_currency": "krw",
            })
            
            if data.get("result") != "success":
                logger.warning(f"[coinone] API 오류: {data.get('errorMsg')}")
                return None
            
            tickers = data.get("tickers", [])
            if not tickers:
                return None
            
            item = tickers[0]
            
            return Ticker(
                symbol=symbol.upper(),
                price=float(item.get("last", 0)),
                volume_24h=float(item.get("volume", 0)),
                change_24h=float(item.get("yesterday_last_pct", 0)),
                high_24h=float(item.get("high", 0)),
                low_24h=float(item.get("low", 0)),
                exchange=self.name,
            )
        except Exception as e:
            logger.error(f"[coinone] 시세 조회 실패 ({symbol}): {e}")
            return None
    
    def get_tickers(self, symbols: List[str] = None) -> List[Ticker]:
        """여러 코인 시세 조회"""
        try:
            # 전체 시세 조회
            data = self._get("/ticker_utc_new", params={
                "quote_currency": "krw",
            })
            
            if data.get("result") != "success":
                logger.warning(f"[coinone] API 오류: {data.get('errorMsg')}")
                return []
            
            tickers = []
            for item in data.get("tickers", []):
                symbol = item.get("target_currency", "").upper()
                
                if symbols and symbol not in [s.upper() for s in symbols]:
                    continue
                
                tickers.append(Ticker(
                    symbol=symbol,
                    price=float(item.get("last", 0)),
                    volume_24h=float(item.get("volume", 0)),
                    change_24h=float(item.get("yesterday_last_pct", 0)),
                    high_24h=float(item.get("high", 0)),
                    low_24h=float(item.get("low", 0)),
                    exchange=self.name,
                ))
            
            return tickers
            
        except Exception as e:
            logger.error(f"[coinone] 시세 목록 조회 실패: {e}")
            return []
    
    def get_orderbook(self, symbol: str) -> dict:
        """호가창 조회"""
        try:
            data = self._get("/orderbook", params={
                "currency": symbol.lower(),
                "quote_currency": "krw",
            })
            
            if data.get("result") != "success":
                return {"bids": [], "asks": []}
            
            return {
                "bids": [
                    {"price": float(b["price"]), "quantity": float(b["qty"])}
                    for b in data.get("bids", [])
                ],
                "asks": [
                    {"price": float(a["price"]), "quantity": float(a["qty"])}
                    for a in data.get("asks", [])
                ],
            }
        except Exception as e:
            logger.error(f"[coinone] 호가창 조회 실패 ({symbol}): {e}")
            return {"bids": [], "asks": []}
    
    def get_candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> List[dict]:
        """
        캔들 데이터 조회
        Note: 코인원 Public API에서 캔들 데이터는 제한적입니다.
        """
        try:
            # 코인원은 candle API가 제한적이므로 업비트 데이터 활용 권장
            logger.warning(f"[coinone] 캔들 조회는 지원하지 않습니다. 업비트 데이터를 사용하세요.")
            return []
        except Exception as e:
            logger.error(f"[coinone] 캔들 조회 실패 ({symbol}): {e}")
            return []
