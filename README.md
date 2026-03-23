# 🪙 크립토 퀀트 시뮬레이터

> 실제 거래 없이 **가상 투자 시뮬레이션**으로 퀀트 전략을 비교하는 플랫폼

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)

## 📋 주요 기능

- **실시간 시세 수집**: 업비트, 빗썸, 코인원 API 연동
- **퀀트 전략 비교**: SMA, RSI, Bollinger Band 등
- **수익률 분석**: 일/주/월간 수익률 시각화
- **가상 투자**: 실제 거래 없이 전략 검증

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
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 실행
```bash
streamlit run app/main.py
```

브라우저에서 `http://localhost:8501` 접속

## 📁 프로젝트 구조

```
crypto-quant/
├── app/                 # 메인 애플리케이션
│   ├── main.py         # Streamlit 대시보드
│   ├── config.py       # 설정
│   └── database.py     # DB 연결
├── exchanges/          # 거래소 API (확장 가능)
│   ├── upbit.py
│   ├── bithumb.py
│   └── coinone.py
├── strategies/         # 퀀트 전략 (확장 가능)
│   ├── sma_cross.py
│   ├── rsi.py
│   └── bollinger.py
└── simulator/          # 시뮬레이션 엔진
    ├── engine.py
    └── portfolio.py
```

## 📊 지원 전략

| 전략 | 설명 |
|------|------|
| **SMA Cross** | 이동평균선 골든/데드 크로스 |
| **RSI** | 과매수/과매도 지표 기반 |
| **Bollinger Band** | 밴드 터치 기반 매매 |
| **MACD** | 시그널 교차 전략 |

## 🌐 배포

### Streamlit Cloud (무료)
1. GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. 저장소 연결 → 자동 배포!

## 📝 환경변수

시세 조회는 **API 키 없이** 가능합니다.

```bash
cp .env.example .env
# 필요시 .env 파일 수정
```

## 🔧 개발

```bash
# 테스트 실행
pytest

# 린트
flake8 .
```

## 📚 문서

- [WORKFLOW.md](./WORKFLOW.md) - 상세 개발 가이드
- [업비트 API](https://docs.upbit.com/)
- [빗썸 API](https://apidocs.bithumb.com/)

## 📄 라이선스

MIT License
