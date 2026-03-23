"""
데이터베이스 연결 및 모델 정의
"""
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import DATABASE_URL, DATA_DIR

# 데이터 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)

# 데이터베이스 엔진 생성
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class PriceHistory(Base):
    """시세 히스토리 테이블"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    exchange = Column(String(20), nullable=False)      # 거래소
    symbol = Column(String(10), nullable=False)        # 코인 심볼 (BTC, ETH 등)
    price = Column(Float, nullable=False)              # 현재가
    volume_24h = Column(Float)                         # 24시간 거래량
    change_24h = Column(Float)                         # 24시간 변동률
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Price {self.exchange}:{self.symbol} @ {self.price:,.0f}>"


class Trade(Base):
    """가상 거래 기록 테이블"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    strategy = Column(String(50), nullable=False)      # 전략 이름
    exchange = Column(String(20), nullable=False)      # 거래소
    symbol = Column(String(10), nullable=False)        # 코인 심볼
    side = Column(String(4), nullable=False)           # buy / sell
    price = Column(Float, nullable=False)              # 체결가
    quantity = Column(Float, nullable=False)           # 수량
    amount = Column(Float, nullable=False)             # 총액 (KRW)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trade {self.strategy} {self.side} {self.symbol} @ {self.price:,.0f}>"


class Portfolio(Base):
    """포트폴리오 스냅샷 테이블"""
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True)
    strategy = Column(String(50), nullable=False)      # 전략 이름
    cash = Column(Float, nullable=False)               # 보유 현금 (KRW)
    total_value = Column(Float, nullable=False)        # 총 자산 가치
    profit_loss = Column(Float, default=0)             # 손익
    profit_loss_pct = Column(Float, default=0)         # 손익률 (%)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Portfolio {self.strategy}: {self.total_value:,.0f} KRW ({self.profit_loss_pct:+.2f}%)>"


def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(engine)


def get_session():
    """데이터베이스 세션 반환"""
    return SessionLocal()


# 모듈 로드 시 테이블 생성
init_db()
