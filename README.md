# 🪙 크립토 퀀트 시뮬레이터

> 실제 거래 없이 **가상 투자 시뮬레이션**으로 퀀트 전략을 비교하는 플랫폼

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)

## ✨ 주요 기능

### 📊 Streamlit 대시보드 (포트 8501)
- **시세 조회**: 거래소별 일봉 차트 및 이동평균선
- **전략 분석**: 4가지 퀀트 전략 백테스팅
- **수익률 비교**: 일/주/월간 기간별 수익률 분석
- **투자 의견**: 시장 상황 분석 및 전략 추천

### 📡 실시간 시세 (포트 8000)
- **WebSocket 스트리밍**: 3개 거래소 실시간 가격
- **코인별 그룹 뷰**: 거래소간 가격 비교
- **가격 변동 알림**: 플래시 효과로 변동 표시

### 🏦 지원 거래소
| 거래소 | REST API | WebSocket |
|--------|----------|-----------|
| **업비트** | ✅ | ✅ 실시간 |
| **빗썸** | ✅ | ✅ 실시간 |
| **코인원** | ✅ | ✅ 폴링(2초) |

### 📈 퀀트 전략
| 전략 | 설명 | 특징 |
|------|------|------|
| **SMA Cross** | 이동평균선 골든/데드 크로스 | 추세 추종형 |
| **RSI** | 과매수(70)/과매도(30) 지표 | 역추세형 |
| **Bollinger Band** | 밴드 터치 기반 매매 | 변동성 활용 |
| **MACD** | 시그널 라인 교차 전략 | 모멘텀 기반 |

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/crypto-quant.git
cd crypto-quant
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# 시세 조회는 API 키 없이 가능
```

### 4. 실행

#### 방법 1: 통합 실행 (run.py)
```bash
# Streamlit 대시보드 (기본)
python run.py

# 실시간 시세 서버
python run.py --mode api

# 둘 다 실행
python run.py --mode all
```

#### 방법 2: 개별 실행
```bash
# Streamlit 대시보드
streamlit run app/main.py --server.port 8501

# FastAPI 실시간 서버
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

### 5. 접속
- **대시보드**: http://localhost:8501
- **실시간 시세**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 📁 프로젝트 구조

```
crypto-quant/
├── app/                      # Streamlit 애플리케이션
│   ├── main.py              # 메인 대시보드
│   ├── config.py            # 설정 관리
│   ├── realtime.py          # 실시간 가격 매니저
│   └── database.py          # DB 연결
│
├── api/                      # FastAPI 서버
│   └── server.py            # WebSocket 브로드캐스트
│
├── exchanges/                # 거래소 API
│   ├── base.py              # 기본 인터페이스
│   ├── upbit.py             # 업비트
│   ├── bithumb.py           # 빗썸
│   ├── coinone.py           # 코인원
│   └── websocket/           # WebSocket 클라이언트
│       ├── base.py          # 기본 클래스 & PriceStore
│       ├── upbit_ws.py      # 업비트 WS
│       ├── bithumb_ws.py    # 빗썸 WS
│       └── coinone_ws.py    # 코인원 (REST 폴링)
│
├── strategies/               # 퀀트 전략
│   ├── base.py              # 전략 인터페이스
│   ├── sma_cross.py         # SMA 크로스오버
│   ├── rsi.py               # RSI
│   ├── bollinger.py         # 볼린저 밴드
│   └── macd.py              # MACD
│
├── simulator/                # 시뮬레이션 엔진
│   ├── engine.py            # 백테스트 엔진
│   ├── portfolio.py         # 포트폴리오 관리
│   └── report.py            # 리포트 생성
│
├── static/                   # 정적 파일
│   └── realtime.html        # 실시간 시세 UI
│
├── tests/                    # 테스트
├── run.py                    # 실행 스크립트
├── requirements.txt          # 의존성
└── WORKFLOW.md              # 개발 가이드
```

## 🖥️ 스크린샷

### 대시보드 - 전략 비교
```
┌─────────────────────────────────────────────────┐
│ 📊 전략별 수익률 비교 - UPBIT / BTC             │
├─────────────────────────────────────────────────┤
│ 전체(12/24~03/23) │ 주간(03/17~03/23) │ ...     │
├─────────────────────────────────────────────────┤
│ 🥇 SMA 크로스오버  │ +5.23% │ ⭐ 최우선 추천   │
│ 🥈 MACD           │ +3.45% │ ✅ 양호          │
│ 🥉 볼린저 밴드    │ +2.11% │ ✅ 양호          │
└─────────────────────────────────────────────────┘
```

### 실시간 시세
```
┌─────────────────────────────────────────────────┐
│  ₿  BTC 비트코인                  ₩103,320,000  │
├─────────────────┬─────────────────┬─────────────┤
│ UPBIT           │ BITHUMB         │ COINONE     │
│ ₩103,320,000    │ ₩103,280,000    │ ₩103,300,000│
│ +1.25%          │ +1.21%          │ +1.23%      │
└─────────────────┴─────────────────┴─────────────┘
```

## 🔧 API 엔드포인트

### REST API
| 엔드포인트 | 설명 |
|-----------|------|
| `GET /` | 실시간 시세 UI |
| `GET /health` | 서버 상태 |
| `GET /api/prices` | 현재 가격 조회 |

### WebSocket
| 엔드포인트 | 설명 |
|-----------|------|
| `WS /ws/prices` | 실시간 가격 스트림 |

## 🌐 배포

### Streamlit Cloud (무료)
1. GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. 저장소 연결 → 자동 배포

### Docker (예정)
```bash
docker-compose up -d
```

## 🧪 개발

```bash
# 테스트 실행
pytest

# 테스트 커버리지
pytest --cov=.

# 린트
flake8 .
```

## 📚 참고 문서

- [WORKFLOW.md](./WORKFLOW.md) - 상세 개발 워크플로우
- [업비트 API](https://docs.upbit.com/)
- [빗썸 API](https://apidocs.bithumb.com/)
- [코인원 API](https://doc.coinone.co.kr/)

## ⚠️ 면책 조항

본 프로젝트는 **교육 및 연구 목적**으로 제작되었습니다.
- 실제 투자 수익을 보장하지 않습니다
- 과거 데이터 기반 시뮬레이션 결과입니다
- 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능
