# 크립토 퀀트 시뮬레이터 (Crypto Quant Simulator)

> 가상 투자 시뮬레이션을 통한 퀀트 전략 수익률 비교 플랫폼

## 📋 프로젝트 개요

### 목적
- 실제 거래 없이 **가상 투자 시뮬레이션**으로 퀀트 전략 검증
- 여러 퀀트 알고리즘의 **수익률 비교** (일/주/월간)
- 국내 주요 거래소(업비트, 빗썸, 코인원) 실시간 시세 활용

### 주요 기능
1. **시세 수집**: 거래소 Open API로 실시간/과거 시세 수집
2. **퀀트 전략**: 여러 투자 알고리즘 적용 (SMA, RSI, Bollinger 등)
3. **시뮬레이션**: 가상 자금으로 매수/매도 시뮬레이션
4. **수익률 분석**: 전략별 수익률 비교 대시보드

---

## 🛠 기술 스택

### 선택 이유
| 기술 | 선택 | 이유 |
|------|------|------|
| **언어** | Python | 퀀트 분석 라이브러리(pandas, numpy) 풍부, 비개발자도 읽기 쉬움 |
| **백엔드** | FastAPI | 빠르고 간단한 API 서버, 자동 문서화 |
| **프론트엔드** | Streamlit | Python만으로 대시보드 구현, 배포 무료 |
| **데이터베이스** | SQLite → PostgreSQL | 로컬 개발은 SQLite, 프로덕션은 PostgreSQL |
| **배포** | Streamlit Cloud (무료) | Python 앱 무료 호스팅, GitHub 연동 자동 배포 |

### 대안 (선택 가능)
- **프론트엔드**: Next.js (더 정교한 UI 필요시) → Vercel 무료 배포
- **백엔드 배포**: Railway, Render (무료 tier 있음)

---

## 📁 프로젝트 구조

```
crypto-quant/
├── README.md                 # 프로젝트 소개
├── WORKFLOW.md              # 이 문서
├── requirements.txt          # Python 패키지
├── .env.example             # 환경변수 예시
├── .gitignore
│
├── app/                      # 메인 애플리케이션
│   ├── main.py              # Streamlit 대시보드 진입점
│   ├── config.py            # 설정 관리
│   └── database.py          # DB 연결
│
├── exchanges/               # 거래소 API 모듈 (확장 용이)
│   ├── __init__.py
│   ├── base.py              # 거래소 기본 인터페이스
│   ├── upbit.py             # 업비트 API
│   ├── bithumb.py           # 빗썸 API
│   └── coinone.py           # 코인원 API
│
├── strategies/              # 퀀트 전략 모듈 (확장 용이)
│   ├── __init__.py
│   ├── base.py              # 전략 기본 인터페이스
│   ├── sma_cross.py         # 이동평균 교차 전략
│   ├── rsi.py               # RSI 전략
│   ├── bollinger.py         # 볼린저 밴드 전략
│   └── macd.py              # MACD 전략
│
├── simulator/               # 시뮬레이션 엔진
│   ├── __init__.py
│   ├── engine.py            # 시뮬레이션 실행
│   ├── portfolio.py         # 포트폴리오 관리
│   └── report.py            # 수익률 리포트
│
├── data/                    # 데이터 저장
│   └── crypto_quant.db      # SQLite 데이터베이스
│
└── tests/                   # 테스트 코드
    └── test_strategies.py
```

---

## 🔌 거래소 API 정보

### 업비트 (Upbit)
- **문서**: https://docs.upbit.com/
- **시세 조회**: API 키 없이 가능 ✅
- **엔드포인트**: `https://api.upbit.com/v1/ticker?markets=KRW-BTC`

### 빗썸 (Bithumb)
- **문서**: https://apidocs.bithumb.com/
- **시세 조회**: API 키 없이 가능 ✅
- **엔드포인트**: `https://api.bithumb.com/public/ticker/BTC_KRW`

### 코인원 (Coinone)
- **문서**: https://doc.coinone.co.kr/
- **시세 조회**: API 키 없이 가능 ✅
- **엔드포인트**: `https://api.coinone.co.kr/ticker/?currency=btc`

> 💡 **시세 조회는 API 키 불필요** - 실제 매매 기능이 없으므로 API 키 없이 시작 가능!

---

## 📊 퀀트 전략 목록

### 1단계 구현 (MVP)
| 전략 | 설명 | 복잡도 |
|------|------|--------|
| **SMA Cross** | 단기/장기 이동평균선 교차 시 매매 | ⭐ |
| **RSI** | RSI 30 이하 매수, 70 이상 매도 | ⭐ |
| **Bollinger Band** | 하단 터치 매수, 상단 터치 매도 | ⭐⭐ |

### 2단계 확장
| 전략 | 설명 | 복잡도 |
|------|------|--------|
| **MACD** | MACD 시그널 교차 전략 | ⭐⭐ |
| **Momentum** | 모멘텀 기반 추세 추종 | ⭐⭐ |
| **Mean Reversion** | 평균 회귀 전략 | ⭐⭐⭐ |

---

## 🚀 개발 단계

### Phase 1: 기본 구조 (Day 1)
- [x] 프로젝트 구조 생성
- [ ] 거래소 API 모듈 구현 (업비트 우선)
- [ ] 기본 데이터베이스 설정
- [ ] 시세 수집 기능

### Phase 2: 퀀트 엔진 (Day 2-3)
- [ ] 전략 기본 인터페이스 설계
- [ ] SMA Cross 전략 구현
- [ ] RSI 전략 구현
- [ ] 시뮬레이션 엔진 구현

### Phase 3: 대시보드 (Day 4-5)
- [ ] Streamlit 대시보드 UI
- [ ] 실시간 시세 표시
- [ ] 전략별 수익률 차트
- [ ] 일/주/월 기간별 분석

### Phase 4: 배포 (Day 6)
- [ ] GitHub 연동
- [ ] Streamlit Cloud 배포
- [ ] 자동 배포 설정 (GitHub Actions)

### Phase 5: 확장 (이후)
- [ ] 추가 거래소 연동
- [ ] 추가 퀀트 전략
- [ ] 사용자 인증 (선택)

---

## 🌐 배포 가이드

### 옵션 1: Streamlit Cloud (추천 - 무료)
```bash
# 1. GitHub에 push
git push origin main

# 2. https://share.streamlit.io 접속
# 3. GitHub 저장소 연결
# 4. 메인 파일 선택: app/main.py
# 5. 배포 완료! (자동 재배포 설정됨)
```

### 옵션 2: Railway (백엔드 분리 필요시)
- 무료 tier: 월 500시간
- PostgreSQL 무료 제공
- https://railway.app

### 옵션 3: AWS Lightsail (저비용)
- 월 $3.5부터
- 더 많은 제어 필요시

---

## ⚙️ 로컬 실행 방법

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/crypto-quant.git
cd crypto-quant

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경변수 설정 (선택)
cp .env.example .env

# 5. 실행
streamlit run app/main.py
```

---

## 📝 환경변수

```env
# .env.example
# 시세 조회는 API 키 불필요
# 추후 실제 거래 기능 추가 시 필요

# UPBIT_ACCESS_KEY=
# UPBIT_SECRET_KEY=
# BITHUMB_API_KEY=
# BITHUMB_SECRET_KEY=

# 데이터베이스 (프로덕션용)
# DATABASE_URL=postgresql://user:pass@host:5432/crypto_quant
```

---

## 🎯 성공 지표

- [ ] 3개 이상 거래소 시세 수집 가능
- [ ] 3개 이상 퀀트 전략 비교 가능
- [ ] 일/주/월 수익률 시각화
- [ ] Streamlit Cloud 배포 완료
- [ ] GitHub push → 자동 배포

---

## 📚 참고 자료

- [Streamlit 문서](https://docs.streamlit.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [업비트 API 문서](https://docs.upbit.com/)
- [TA-Lib (기술적 분석)](https://ta-lib.org/)
- [Backtrader (백테스팅)](https://www.backtrader.com/)

---

*최종 수정: 2025-03-23*
