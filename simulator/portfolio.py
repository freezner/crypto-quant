"""
가상 포트폴리오 관리
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """보유 포지션"""
    symbol: str              # 코인 심볼
    quantity: float          # 수량
    avg_price: float         # 평균 매수가
    total_cost: float        # 총 매수 비용
    
    @property
    def current_value(self) -> float:
        """현재 평가금액 (현재가 필요)"""
        return 0  # 외부에서 계산
    
    def __str__(self):
        return f"{self.symbol}: {self.quantity:.8f} @ {self.avg_price:,.0f}"


@dataclass
class TradeRecord:
    """거래 기록"""
    timestamp: datetime
    symbol: str
    side: str           # "buy" or "sell"
    price: float
    quantity: float
    amount: float       # 총액
    strategy: str
    reason: str = ""
    
    def __str__(self):
        return f"[{self.side.upper()}] {self.symbol} {self.quantity:.8f} @ {self.price:,.0f}"


class VirtualPortfolio:
    """가상 포트폴리오"""
    
    def __init__(
        self,
        initial_balance: float = 10_000_000,
        strategy_name: str = "default",
        fee_rate: float = 0.0005,  # 0.05% 수수료
    ):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.strategy_name = strategy_name
        self.fee_rate = fee_rate
        
        self.positions: Dict[str, Position] = {}  # 보유 포지션
        self.trades: List[TradeRecord] = []       # 거래 기록
        self.created_at = datetime.now()
    
    def buy(
        self,
        symbol: str,
        price: float,
        amount: float = None,       # KRW 금액
        quantity: float = None,     # 수량
        reason: str = "",
    ) -> Optional[TradeRecord]:
        """
        매수 실행
        
        Args:
            symbol: 코인 심볼
            price: 매수가
            amount: 매수 금액 (KRW) - quantity와 둘 중 하나 지정
            quantity: 매수 수량 - amount와 둘 중 하나 지정
            reason: 매수 사유
        """
        # 수량/금액 계산
        if amount:
            fee = amount * self.fee_rate
            net_amount = amount - fee
            quantity = net_amount / price
        elif quantity:
            amount = quantity * price
            fee = amount * self.fee_rate
            amount += fee
        else:
            logger.warning("amount 또는 quantity 필요")
            return None
        
        # 잔고 확인
        if amount > self.cash:
            logger.warning(f"잔고 부족: 필요 {amount:,.0f}, 보유 {self.cash:,.0f}")
            return None
        
        # 포지션 업데이트
        if symbol in self.positions:
            pos = self.positions[symbol]
            new_quantity = pos.quantity + quantity
            new_cost = pos.total_cost + amount
            pos.quantity = new_quantity
            pos.avg_price = new_cost / new_quantity
            pos.total_cost = new_cost
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                total_cost=amount,
            )
        
        # 잔고 차감
        self.cash -= amount
        
        # 거래 기록
        trade = TradeRecord(
            timestamp=datetime.now(),
            symbol=symbol,
            side="buy",
            price=price,
            quantity=quantity,
            amount=amount,
            strategy=self.strategy_name,
            reason=reason,
        )
        self.trades.append(trade)
        
        logger.info(f"[BUY] {symbol} {quantity:.8f} @ {price:,.0f} = {amount:,.0f} KRW")
        return trade
    
    def sell(
        self,
        symbol: str,
        price: float,
        quantity: float = None,     # 매도 수량 (None이면 전량)
        reason: str = "",
    ) -> Optional[TradeRecord]:
        """
        매도 실행
        
        Args:
            symbol: 코인 심볼
            price: 매도가
            quantity: 매도 수량 (None이면 전량)
            reason: 매도 사유
        """
        # 포지션 확인
        if symbol not in self.positions:
            logger.warning(f"보유 포지션 없음: {symbol}")
            return None
        
        pos = self.positions[symbol]
        
        # 수량 결정
        if quantity is None:
            quantity = pos.quantity  # 전량 매도
        elif quantity > pos.quantity:
            logger.warning(f"보유 수량 초과: 요청 {quantity}, 보유 {pos.quantity}")
            quantity = pos.quantity
        
        # 매도 금액 계산
        gross_amount = quantity * price
        fee = gross_amount * self.fee_rate
        net_amount = gross_amount - fee
        
        # 포지션 업데이트
        pos.quantity -= quantity
        if pos.quantity <= 0:
            del self.positions[symbol]
        else:
            pos.total_cost = pos.quantity * pos.avg_price
        
        # 잔고 증가
        self.cash += net_amount
        
        # 거래 기록
        trade = TradeRecord(
            timestamp=datetime.now(),
            symbol=symbol,
            side="sell",
            price=price,
            quantity=quantity,
            amount=net_amount,
            strategy=self.strategy_name,
            reason=reason,
        )
        self.trades.append(trade)
        
        logger.info(f"[SELL] {symbol} {quantity:.8f} @ {price:,.0f} = {net_amount:,.0f} KRW")
        return trade
    
    def get_total_value(self, prices: Dict[str, float]) -> float:
        """
        총 자산 가치 계산
        
        Args:
            prices: {symbol: current_price} 딕셔너리
        """
        position_value = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
        )
        return self.cash + position_value
    
    def get_profit_loss(self, prices: Dict[str, float]) -> tuple:
        """
        손익 계산
        
        Returns:
            (손익금액, 손익률%)
        """
        total_value = self.get_total_value(prices)
        profit = total_value - self.initial_balance
        profit_pct = (profit / self.initial_balance) * 100
        return profit, profit_pct
    
    def get_summary(self, prices: Dict[str, float] = None) -> dict:
        """포트폴리오 요약"""
        prices = prices or {}
        total_value = self.get_total_value(prices)
        profit, profit_pct = self.get_profit_loss(prices)
        
        return {
            "strategy": self.strategy_name,
            "initial_balance": self.initial_balance,
            "cash": self.cash,
            "position_value": total_value - self.cash,
            "total_value": total_value,
            "profit_loss": profit,
            "profit_loss_pct": profit_pct,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": prices.get(pos.symbol, pos.avg_price),
                    "value": pos.quantity * prices.get(pos.symbol, pos.avg_price),
                }
                for pos in self.positions.values()
            ],
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t.side == "buy"]),
            "sell_trades": len([t for t in self.trades if t.side == "sell"]),
        }
