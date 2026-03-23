"""
코인원 거래소 API
문서: https://doc.coinone.co.kr/
API v2: https://api.coinone.co.kr/public/v2/
"""
from typing import List, Optional
from exchanges.base import ExchangeBase, Ticker
import logging

logger = logging.getLogger(__name__)


class CoinoneExchange(ExchangeBase):
    """코인원 거래소"""
    
    name = "coinone"
    base_url = "https://api.coinone.co.kr"
    
    def _calc_change_pct(self, first: float, last: float) -> float:
        """변동률 계산 (시가 대비)"""
        if first <= 0:
            return 0.0
        return ((last - first) / first) * 100
    
    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """단일 코인 시세 조회 (v2 API)"""
        try:
            # v2 API: /public/v2/ticker_new/KRW/{SYMBOL}
            data = self._get(f"/public/v2/ticker_new/KRW/{symbol.upper()}")
            
            if data.get("result") != "success":
                logger.warning(f"[coinone] API 오류: {data.get('error_code')}")
                return None
            
            tickers = data.get("tickers", [])
            if not tickers:
                return None
            
            item = tickers[0]
            first_price = float(item.get("first", 0))
            last_price = float(item.get("last", 0))
            
            return Ticker(
                symbol=symbol.upper(),
                price=last_price,
                volume_24h=float(item.get("target_volume", 0)),
                change_24h=self._calc_change_pct(first_price, last_price),
                high_24h=float(item.get("high", 0)),
                low_24h=float(item.get("low", 0)),
                exchange=self.name,
            )
        except Exception as e:
            logger.error(f"[coinone] 시세 조회 실패 ({symbol}): {e}")
            return None
    
    def get_tickers(self, symbols: List[str] = None) -> List[Ticker]:
        """여러 코인 시세 조회 (v2 API)"""
        try:
            # v2 API: /public/v2/ticker_new/KRW
            data = self._get("/public/v2/ticker_new/KRW")
            
            if data.get("result") != "success":
                logger.warning(f"[coinone] API 오류: {data.get('error_code')}")
                return []
            
            tickers = []
            for item in data.get("tickers", []):
                symbol = item.get("target_currency", "").upper()
                
                if symbols and symbol not in [s.upper() for s in symbols]:
                    continue
                
                first_price = float(item.get("first", 0))
                last_price = float(item.get("last", 0))
                
                tickers.append(Ticker(
                    symbol=symbol,
                    price=last_price,
                    volume_24h=float(item.get("target_volume", 0)),
                    change_24h=self._calc_change_pct(first_price, last_price),
                    high_24h=float(item.get("high", 0)),
                    low_24h=float(item.get("low", 0)),
                    exchange=self.name,
                ))
            
            return tickers
            
        except Exception as e:
            logger.error(f"[coinone] 시세 목록 조회 실패: {e}")
            return []
    
    def get_orderbook(self, symbol: str) -> dict:
        """호가창 조회 (v2 API)"""
        try:
            # v2 API: /public/v2/orderbook/KRW/{SYMBOL}
            data = self._get(f"/public/v2/orderbook/KRW/{symbol.upper()}")
            
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
