"""
설정 관리 모듈
환경변수와 기본 설정값을 관리합니다.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
load_dotenv()

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# 데이터베이스
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{DATA_DIR}/crypto_quant.db"
)

# 시뮬레이션 설정
INITIAL_BALANCE = int(os.getenv("INITIAL_BALANCE", "10000000"))  # 1천만원
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))  # 60초

# 지원 암호화폐 (KRW 마켓)
SUPPORTED_COINS = [
    "BTC",   # 비트코인
    "ETH",   # 이더리움
    "XRP",   # 리플
    "SOL",   # 솔라나
    "DOGE",  # 도지코인
]

# 거래소 API 엔드포인트
EXCHANGE_ENDPOINTS = {
    "upbit": "https://api.upbit.com/v1",
    "bithumb": "https://api.bithumb.com/public",
    "coinone": "https://api.coinone.co.kr",
}

# 전략 파라미터 기본값
STRATEGY_DEFAULTS = {
    "sma_cross": {
        "short_window": 5,   # 단기 이동평균 (5일)
        "long_window": 20,   # 장기 이동평균 (20일)
    },
    "rsi": {
        "period": 14,        # RSI 기간
        "oversold": 30,      # 과매도 기준
        "overbought": 70,    # 과매수 기준
    },
    "bollinger": {
        "period": 20,        # 볼린저 밴드 기간
        "std_dev": 2,        # 표준편차 배수
    },
    "macd": {
        "fast_period": 12,   # 빠른 EMA
        "slow_period": 26,   # 느린 EMA
        "signal_period": 9,  # 시그널 라인
    },
}
