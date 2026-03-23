"""
수익률 리포트 생성
"""
from typing import List, Dict
from datetime import datetime, timedelta
import pandas as pd


def generate_report(
    portfolios: List[dict],
    period: str = "all",  # "day", "week", "month", "all"
) -> dict:
    """
    여러 전략의 수익률 비교 리포트 생성
    
    Args:
        portfolios: 포트폴리오 요약 리스트
        period: 비교 기간
        
    Returns:
        비교 리포트
    """
    if not portfolios:
        return {"error": "비교할 포트폴리오 없음"}
    
    # 전략별 수익률 비교
    comparison = []
    for p in portfolios:
        comparison.append({
            "strategy": p.get("strategy", "unknown"),
            "total_value": p.get("total_value", 0),
            "profit_loss": p.get("profit_loss", 0),
            "profit_loss_pct": p.get("profit_loss_pct", 0),
            "total_trades": p.get("total_trades", 0),
            "positions": len(p.get("positions", [])),
        })
    
    # 수익률 순으로 정렬
    comparison.sort(key=lambda x: x["profit_loss_pct"], reverse=True)
    
    # 통계
    returns = [c["profit_loss_pct"] for c in comparison]
    
    return {
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "strategies_count": len(comparison),
        "comparison": comparison,
        "statistics": {
            "best_strategy": comparison[0]["strategy"] if comparison else None,
            "best_return_pct": max(returns) if returns else 0,
            "worst_return_pct": min(returns) if returns else 0,
            "avg_return_pct": sum(returns) / len(returns) if returns else 0,
        },
        "ranking": [c["strategy"] for c in comparison],
    }


def calculate_period_returns(
    trades: List[dict],
    initial_balance: float,
    current_value: float,
) -> dict:
    """
    기간별 수익률 계산
    
    Args:
        trades: 거래 기록
        initial_balance: 초기 자금
        current_value: 현재 자산 가치
        
    Returns:
        기간별 수익률
    """
    now = datetime.now()
    
    # 전체 수익률
    total_return = current_value - initial_balance
    total_return_pct = (total_return / initial_balance) * 100 if initial_balance else 0
    
    # 기간별 기준점 (실제로는 DB에서 스냅샷 조회 필요)
    # 여기서는 간단히 전체 수익률 사용
    
    return {
        "total": {
            "return": total_return,
            "return_pct": total_return_pct,
        },
        "daily": {
            "return": total_return,  # 실제로는 일일 스냅샷 필요
            "return_pct": total_return_pct,
        },
        "weekly": {
            "return": total_return,  # 실제로는 주간 스냅샷 필요
            "return_pct": total_return_pct,
        },
        "monthly": {
            "return": total_return,  # 실제로는 월간 스냅샷 필요
            "return_pct": total_return_pct,
        },
    }


def format_currency(value: float) -> str:
    """통화 형식으로 포맷"""
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.2f}K"
    else:
        return f"{value:,.0f}"


def format_percentage(value: float) -> str:
    """퍼센트 형식으로 포맷"""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"
