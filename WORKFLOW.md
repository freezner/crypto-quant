# 크립토 퀀트 시뮬레이터 (Crypto Quant Simulator)

> 가상 투자 시뮬레이션을 통한 퀀트 전략 수익률 비교 플랫폼

---

## 🏗 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                          클라이언트                              │
├───────────────────────────────┬─────────────────────────────────┤
│   실시간 대시보드 (HTML/JS)     │   분석 대시보드 (Streamlit)      │
│   http://localhost:8000       │   http://localhost:8501         │
│   - WebSocket 실시간 시세      │   - 시세 조회 (일봉 차트)        │
│   - 코인별 거래소 가격 비교     │   - 전략 백테스트 결과           │
│   - 가격 변동 플래시 효과       │   - 기간별 수익률 비교           │
│                               │   - 종합 투자 의견               │
└──────────────┬────────────────┴────────────────┬────────────────┘
               │                                 │
               ▼                                 ▼
┌───────────────────────────────┐  ┌──────────────────────────────┐
│   FastAPI 서버 (api/)          │  │   분석 엔진 (simulator/)      │
│   - WebSocket 브로드캐스트      │  │   - 백테스팅 엔진             │
│   - REST API (/api/prices)    │  │   - 포트폴리오 관리            │
│   - PriceStore 통합 관리       │  │   - 수익률 리포트 생성         │
└──────────────┬────────────────┘  └──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│               거래소 WebSocket (exchanges/websocket/)            │
├─────────────────────┬─────────────────────┬─────────────────────┤
│      업비트          │       빗썸          │       코인원         │
│   wss://api.upbit   │  wss://pubwss.      │   REST API 폴링      │
│   실시간 스트리밍     │  bithumb.com        │   (2초 간격)         │
│                     │   실시간 스트리밍     │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│               거래소 REST API (exchanges/)                       │
├─────────────────────┬─────────────────────┬─────────────────────┤
│      업비트          │       빗썸          │       코인원         │
│   /v1/candles       │  /candlestick       │  /public/v2/chart   │
│   /v1/ticker        │  /ticker            │  /public/v2/ticker  │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

---

## 📋 프로젝트 개요

### 목적
- 실제 거래 없이 **가상 투자 시뮬레이션**으로 퀀트 전략 검증
- 여러 퀀트 알고리즘의 **수익률 비교** (일/주/월간)
- 국내 주요 거래소(업비트, 빗썸, 코인원) 실시간 시세 활용
- **종합 투자 의견** 제공으로 의사결정 지원

### 주요 기능
1. **실시간 시세**: WebSocket으로 3개 거래소 실시간 가격 수신
2. **시세 수집**: 거래소 Open API로 과거 캔들 데이터 수집
3. **퀀트 전략**: 4가지 투자 알고리즘 (SMA, RSI, Bollinger, MACD)
4. **시뮬레이션**: 가상 자금으로 매수/매도 백테스트
5. **수익률 분석**: 기간별(일/주/월) 전략 수익률 비교
6. **투자 의견**: 시장 상황 분석 및 전략 추천

---

## 🛠 기술 스택

### 핵심 기술
| 기술 | 용도 | 선택 이유 |
|------|------|----------|
| **Python 3.10+** | 메인 언어 | 퀀트 라이브러리(pandas, numpy) 풍부 |
| **Streamlit** | 분석 대시보드 | Python만으로 대시보드 구현, 무료 배포 |
| **FastAPI** | 실시간 API 서버 | 비동기 WebSocket 지원, 자동 문서화 |
| **websockets** | 실시간 연결 | 업비트/빗썸 WebSocket 클라이언트 |
| **aiohttp** | 비동기 HTTP | 코인원 REST 폴링 |
| **Plotly** | 차트 시각화 | 인터랙티브 캔들스틱 차트 |

### 의존성 패키지
```
streamlit>=1.28.0      # 분석 대시보드
fastapi>=0.104.0       # API 서버
uvicorn>=0.24.0        # ASGI 서버
websockets>=12.0       # WebSocket 클라이언트
aiohttp>=3.9.0         # 비동기 HTTP
pandas>=2.0.0          # 데이터 분석
numpy>=1.24.0          # 수치 연산
plotly>=5.18.0         # 차트 시각화
python-dotenv>=1.0.0   # 환경변수
requests>=2.31.0       # HTTP 클라이언트
```

---

## 📁 프로젝트 구조

```
crypto-quant/
├── README.md                    # 프로젝트 소개
├── WORKFLOW.md                  # 개발 워크플로우 (이 문서)
├── requirements.txt             # Python 패키지
├── .env.example                 # 환경변수 예시
├── .gitignore                   # Git 제외 파일
├── run.py                       # 통합 실행 스크립트
│
├── app/                         # Streamlit 애플리케이션
│   ├── __init__.py
│   ├── main.py                  # 메인 대시보드
│   │   ├── 시세 조회 탭        # 일봉 차트, 이동평균선
│   │   ├── 분석 결과 탭        # 전략별 백테스트 결과
│   │   └── 전략 비교 탭        # 기간별 수익률 + 투자 의견
│   ├── config.py                # 설정 관리 (코인 목록, 초기자금)
│   ├── realtime.py              # 실시간 가격 매니저
│   └── database.py              # DB 연결 (SQLite/PostgreSQL)
│
├── api/                         # FastAPI 서버
│   ├── __init__.py
│   └── server.py                # WebSocket 브로드캐스트 서버
│       ├── GET /                # 실시간 시세 UI (static/realtime.html)
│       ├── GET /health          # 서버 상태 확인
│       ├── GET /api/prices      # 현재 가격 REST API
│       └── WS /ws/prices        # 실시간 가격 WebSocket
│
├── exchanges/                   # 거래소 API 모듈
│   ├── __init__.py              # get_exchange() 팩토리
│   ├── base.py                  # ExchangeBase 인터페이스
│   ├── upbit.py                 # 업비트 REST API
│   ├── bithumb.py               # 빗썸 REST API
│   ├── coinone.py               # 코인원 REST API (v2)
│   └── websocket/               # WebSocket 클라이언트
│       ├── __init__.py          # get_websocket() 팩토리
│       ├── base.py              # WebSocketBase, PriceStore
│       ├── upbit_ws.py          # 업비트 WebSocket
│       ├── bithumb_ws.py        # 빗썸 WebSocket
│       └── coinone_ws.py        # 코인원 REST 폴링 (2초)
│
├── strategies/                  # 퀀트 전략 모듈
│   ├── __init__.py              # get_strategy() 팩토리
│   ├── base.py                  # StrategyBase 인터페이스
│   ├── sma_cross.py             # SMA 크로스오버 (5/20일)
│   ├── rsi.py                   # RSI (14일, 30/70)
│   ├── bollinger.py             # 볼린저 밴드 (20일, 2σ)
│   └── macd.py                  # MACD (12/26/9)
│
├── simulator/                   # 시뮬레이션 엔진
│   ├── __init__.py
│   ├── engine.py                # SimulationEngine - 백테스트 실행
│   ├── portfolio.py             # Portfolio - 자산/포지션 관리
│   └── report.py                # 수익률 리포트 생성
│
├── static/                      # 정적 파일
│   └── realtime.html            # 실시간 시세 UI
│       ├── 코인별 카드 레이아웃
│       ├── 거래소 3열 비교
│       └── 가격 변동 플래시 효과
│
├── data/                        # 데이터 저장
│   └── .gitkeep
│
├── tests/                       # 테스트 코드
│   └── test_strategies.py
│
└── .github/
    └── workflows/
        └── deploy.yml           # CI/CD (Streamlit Cloud)
```

---

## 🔌 거래소 API 정보

### 업비트 (Upbit)
| 항목 | 내용 |
|------|------|
| **문서** | https://docs.upbit.com/ |
| **REST Base** | `https://api.upbit.com/v1` |
| **WebSocket** | `wss://api.upbit.com/websocket/v1` |
| **캔들 조회** | `/candles/days?market=KRW-BTC&count=100` |
| **시세 조회** | `/ticker?markets=KRW-BTC` |
| **API 키** | 시세 조회는 불필요 ✅ |

### 빗썸 (Bithumb)
| 항목 | 내용 |
|------|------|
| **문서** | https://apidocs.bithumb.com/ |
| **REST Base** | `https://api.bithumb.com/public` |
| **WebSocket** | `wss://pubwss.bithumb.com/pub/ws` |
| **캔들 조회** | `/candlestick/BTC_KRW/24h` |
| **시세 조회** | `/ticker/BTC_KRW` |
| **API 키** | 시세 조회는 불필요 ✅ |

### 코인원 (Coinone)
| 항목 | 내용 |
|------|------|
| **문서** | https://doc.coinone.co.kr/ |
| **REST Base** | `https://api.coinone.co.kr` |
| **WebSocket** | 공개 API 제한적 (REST 폴링으로 대체) |
| **캔들 조회** | `/public/v2/chart/KRW/BTC?interval=1d` |
| **시세 조회** | `/public/v2/ticker_new/KRW/BTC` |
| **API 키** | 시세 조회는 불필요 ✅ |

---

## 📊 퀀트 전략

### 구현된 전략

| 전략 | 파라미터 | 매수 조건 | 매도 조건 | 특징 |
|------|----------|----------|----------|------|
| **SMA Cross** | 단기 5일, 장기 20일 | 골든크로스 | 데드크로스 | 추세 추종형 |
| **RSI** | 14일, 30/70 | RSI < 30 | RSI > 70 | 역추세형 |
| **Bollinger** | 20일, 2σ | 하단밴드 터치 | 상단밴드 터치 | 변동성 활용 |
| **MACD** | 12/26/9 | MACD > Signal | MACD < Signal | 모멘텀 기반 |

### 전략 확장 방법
```python
# strategies/my_strategy.py
from strategies.base import StrategyBase

class MyStrategy(StrategyBase):
    name = "my_strategy"
    display_name = "나만의 전략"
    description = "설명..."
    
    def calculate_indicators(self, df):
        # 지표 계산
        return df
    
    def generate_signal(self, df, index):
        # 매수: 1, 매도: -1, 홀드: 0
        return 0
```

---

## 🚀 실행 방법

### 통합 실행 (run.py)
```bash
# Streamlit 대시보드만 (기본)
python run.py

# FastAPI 실시간 서버만
python run.py --mode api

# 둘 다 실행
python run.py --mode all
```

### 개별 실행
```bash
# Streamlit 대시보드
streamlit run app/main.py --server.port 8501

# FastAPI 서버
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 접속 URL
| 서비스 | URL | 설명 |
|--------|-----|------|
| 분석 대시보드 | http://localhost:8501 | Streamlit |
| 실시간 시세 | http://localhost:8000 | FastAPI |
| API 문서 | http://localhost:8000/docs | Swagger UI |

---

## ✅ 개발 진행 상황

### Phase 1: 기본 구조 ✅
- [x] 프로젝트 구조 생성
- [x] 거래소 REST API 모듈 (업비트, 빗썸, 코인원)
- [x] 기본 설정 관리 (config.py)
- [x] 시세 및 캔들 데이터 수집

### Phase 2: 퀀트 엔진 ✅
- [x] 전략 기본 인터페이스 설계
- [x] SMA Cross 전략 구현
- [x] RSI 전략 구현
- [x] Bollinger Band 전략 구현
- [x] MACD 전략 구현
- [x] 시뮬레이션 엔진 구현

### Phase 3: 대시보드 ✅
- [x] Streamlit 대시보드 UI
- [x] 시세 조회 탭 (일봉 차트)
- [x] 분석 결과 탭 (전략별 결과)
- [x] 전략 비교 탭 (기간별 수익률)
- [x] 종합 투자 의견 섹션
- [x] 거래소/코인 선택시 자동 분석

### Phase 4: 실시간 시세 ✅
- [x] FastAPI WebSocket 서버
- [x] 업비트 WebSocket 클라이언트
- [x] 빗썸 WebSocket 클라이언트
- [x] 코인원 REST 폴링 (2초)
- [x] 실시간 UI (코인별 그룹 레이아웃)
- [x] 가격 변동 플래시 효과

### Phase 5: 배포 준비 ✅
- [x] GitHub Actions CI/CD
- [x] .gitignore 정리
- [x] README.md 문서화
- [x] WORKFLOW.md 문서화

### 향후 계획
- [ ] Docker 컨테이너화
- [ ] 추가 전략 (모멘텀, 평균회귀)
- [ ] 알림 기능 (텔레그램, 슬랙)
- [ ] 사용자 인증 (선택)

---

## 🌐 배포 가이드

### Streamlit Cloud (추천 - 무료)
1. GitHub에 push
2. https://share.streamlit.io 접속
3. GitHub 저장소 연결
4. 메인 파일: `app/main.py`
5. 자동 배포 완료!

### Docker (예정)
```bash
docker-compose up -d
```

---

## ⚙️ 환경변수

```env
# .env.example

# 시뮬레이션 설정
INITIAL_BALANCE=10000000    # 초기 자금 (1천만원)
FETCH_INTERVAL=60           # 시세 수집 간격 (초)

# 데이터베이스 (프로덕션용)
# DATABASE_URL=postgresql://user:pass@host:5432/crypto_quant

# API 키 (시세 조회는 불필요)
# UPBIT_ACCESS_KEY=
# UPBIT_SECRET_KEY=
```

---

## 📚 참고 자료

- [Streamlit 문서](https://docs.streamlit.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [업비트 API 문서](https://docs.upbit.com/)
- [빗썸 API 문서](https://apidocs.bithumb.com/)
- [코인원 API 문서](https://doc.coinone.co.kr/)

---

*최종 수정: 2026-03-23*
