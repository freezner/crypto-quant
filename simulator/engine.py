"""
시뮬레이션 엔진
백테스팅 및 실시간 시뮬레이션 실행
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

from simulator.portfolio import VirtualPortfolio
from strategies.base import StrategyBase, Signal
from exchanges.base import ExchangeBase

logger = logging.getLogger(__name__)


class SimulationEngine:
    """시뮬레이션 엔진"""
    
    def __init__(
        self,
        strategy: StrategyBase,
        exchange: ExchangeBase,
        initial_balance: float = 10_000_000,
        trade_amount: float = 1_000_000,  # 1회 거래 금액
    ):
        self.strategy = strategy
        self.exchange = exchange
        self.trade_amount = trade_amount
        
        self.portfolio = VirtualPortfolio(
            initial_balance=initial_balance,
            strategy_name=strategy.name,
        )
        
        self.signals_history: List[dict] = []
        self.is_running = False
    
    def backtest(
        self,
        symbol: str,
        candles: List[dict],
        trade_pct: float = 0.1,  # 자산의 10%씩 거래
    ) -> dict:
        """
        백테스팅 실행
        
        Args:
            symbol: 코인 심볼
            candles: 과거 캔들 데이터
            trade_pct: 거래 비율 (자산 대비)
            
        Returns:
            백테스팅 결과
        """
        if not candles or len(candles) < 30:
            return {"error": "캔들 데이터 부족 (최소 30개 필요)"}
        
        logger.info(f"[Backtest] {symbol} - {len(candles)}개 캔들, 전략: {self.strategy.name}")
        
        # 캔들을 순차적으로 분석
        for i in range(30, len(candles)):
            window = candles[:i+1]  # 현재까지의 데이터
            current_price = float(window[-1]["close"])
            
            # 신호 생성
            signal = self.strategy.analyze(window, symbol)
            
            # 거래 실행
            if signal.signal == Signal.BUY:
                # 현금의 일정 비율로 매수
                amount = self.portfolio.cash * trade_pct
                if amount >= 10000:  # 최소 1만원
                    self.portfolio.buy(
                        symbol=symbol,
                        price=current_price,
                        amount=amount,
                        reason=signal.reason,
                    )
                    
            elif signal.signal == Signal.SELL:
                # 보유 수량의 일정 비율 매도
                if symbol in self.portfolio.positions:
                    pos = self.portfolio.positions[symbol]
                    quantity = pos.quantity * trade_pct
                    if quantity * current_price >= 10000:  # 최소 1만원
                        self.portfolio.sell(
                            symbol=symbol,
                            price=current_price,
                            quantity=quantity,
                            reason=signal.reason,
                        )
            
            # 신호 기록
            self.signals_history.append({
                "timestamp": window[-1].get("timestamp"),
                "price": current_price,
                "signal": signal.signal.value,
                "reason": signal.reason,
            })
        
        # 최종 결과
        final_price = float(candles[-1]["close"])
        prices = {symbol: final_price}
        
        return {
            "symbol": symbol,
            "strategy": self.strategy.name,
            "period": {
                "start": candles[0].get("timestamp"),
                "end": candles[-1].get("timestamp"),
                "candles": len(candles),
            },
            "portfolio": self.portfolio.get_summary(prices),
            "signals": {
                "total": len(self.signals_history),
                "buy": len([s for s in self.signals_history if s["signal"] == "buy"]),
                "sell": len([s for s in self.signals_history if s["signal"] == "sell"]),
                "hold": len([s for s in self.signals_history if s["signal"] == "hold"]),
            },
        }
    
    def run_once(self, symbol: str) -> dict:
        """
        단일 실행 (현재 시점 분석)
        
        Args:
            symbol: 코인 심볼
            
        Returns:
            분석 결과
        """
        # 캔들 데이터 조회
        try:
            candles = self.exchange.get_candles(symbol, interval="1d", limit=100)
        except Exception as e:
            logger.error(f"캔들 조회 실패: {e}")
            return {"error": str(e)}
        
        if not candles:
            return {"error": "캔들 데이터 없음"}
        
        # 현재 시세
        ticker = self.exchange.get_ticker(symbol)
        current_price = ticker.price if ticker else float(candles[-1]["close"])
        
        # 신호 생성
        signal = self.strategy.analyze(candles, symbol)
        
        return {
            "symbol": symbol,
            "strategy": self.strategy.name,
            "exchange": self.exchange.name,
            "current_price": current_price,
            "signal": {
                "action": signal.signal.value,
                "confidence": signal.confidence,
                "reason": signal.reason,
            },
            "portfolio": self.portfolio.get_summary({symbol: current_price}),
            "timestamp": datetime.now().isoformat(),
        }
    
    def execute_signal(self, symbol: str, signal: Signal, price: float, reason: str = ""):
        """
        신호에 따라 거래 실행
        
        Args:
            symbol: 코인 심볼
            signal: 매매 신호
            price: 현재가
            reason: 거래 사유
        """
        if signal == Signal.BUY:
            # 잔고의 일정 비율 매수
            amount = min(self.trade_amount, self.portfolio.cash * 0.3)
            if amount >= 10000:
                self.portfolio.buy(symbol, price, amount=amount, reason=reason)
                
        elif signal == Signal.SELL:
            # 보유 시 전량 매도
            if symbol in self.portfolio.positions:
                self.portfolio.sell(symbol, price, reason=reason)
    
    def get_performance(self, prices: Dict[str, float]) -> dict:
        """
        성과 지표 계산
        
        Args:
            prices: 현재 가격 딕셔너리
            
        Returns:
            성과 지표
        """
        summary = self.portfolio.get_summary(prices)
        trades = self.portfolio.trades
        
        # 승률 계산
        if not trades:
            win_rate = 0
        else:
            # 매수/매도 쌍으로 손익 계산 (간단화)
            profitable_trades = 0
            total_closed = 0
            
            buy_prices = {}
            for trade in trades:
                if trade.side == "buy":
                    if trade.symbol not in buy_prices:
                        buy_prices[trade.symbol] = []
                    buy_prices[trade.symbol].append(trade.price)
                elif trade.side == "sell" and trade.symbol in buy_prices and buy_prices[trade.symbol]:
                    avg_buy = sum(buy_prices[trade.symbol]) / len(buy_prices[trade.symbol])
                    if trade.price > avg_buy:
                        profitable_trades += 1
                    total_closed += 1
                    buy_prices[trade.symbol] = []
            
            win_rate = (profitable_trades / total_closed * 100) if total_closed > 0 else 0
        
        return {
            "total_return": summary["profit_loss"],
            "total_return_pct": summary["profit_loss_pct"],
            "total_trades": summary["total_trades"],
            "win_rate": win_rate,
            "current_cash": summary["cash"],
            "current_positions": len(summary["positions"]),
        }
