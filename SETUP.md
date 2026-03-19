# PersonaAI - AI 페르소나 분석 서비스

## 필요한 API 키 및 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 (페르소나 분석용) | https://aistudio.google.com/app/apikey |
| `SECRET_KEY` | JWT 토큰 서명용 시크릿 키 (임의 문자열) | - |
| `DATABASE_URL` | 데이터베이스 연결 URL (기본: SQLite) | - |
| `FREE_DAILY_LIMIT` | 무료 사용자 일일 분석 횟수 제한 (기본: `5`) | - |
| `SCRAPE_TIMEOUT` | 웹 스크래핑 요청 타임아웃 (초, 기본: `10`) | - |

## GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `SECRET_KEY` | JWT 시크릿 키 (랜덤 32자 이상 문자열) |

## 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/PersonaAI.git
cd PersonaAI

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 아래 항목 입력:
# GEMINI_API_KEY=your_gemini_api_key
# SECRET_KEY=your_random_secret_key

# 5. 서버 실행
uvicorn app.main:app --reload
```

서버 기동 후 http://localhost:8000/docs 에서 API 문서를 확인할 수 있습니다.

## Docker로 실행

```bash
docker-compose up --build
```

## 주요 기능 사용법

### AI 페르소나 분석
- 소셜 미디어 프로필 URL, 텍스트 샘플 등을 입력하면 Gemini AI가 성격 유형, 관심사, 행동 패턴을 분석합니다.
- `beautifulsoup4`를 사용한 웹 콘텐츠 스크래핑을 지원합니다.

### 페르소나 프로필 생성
- 분석 결과를 바탕으로 상세한 페르소나 프로필 카드를 생성합니다.
- MBTI, 빅파이브(Big Five), 관심사, 선호 채널 등을 포함합니다.

### 사용 제한
- 무료 사용자: 일일 5회 분석 제한 (`FREE_DAILY_LIMIT` 설정 가능)
- 프리미엄 사용자: 무제한 분석

### 인증
- JWT 기반 인증 (토큰 유효기간: 24시간)
- `/api/auth/register` - 회원가입
- `/api/auth/login` - 로그인 및 토큰 발급

## 프로젝트 구조

```
PersonaAI/
├── app/
│   ├── config.py       # 환경변수 설정
│   ├── database.py     # DB 연결 관리
│   ├── main.py         # FastAPI 앱 진입점
│   ├── models/         # SQLAlchemy 모델
│   ├── routers/        # API 라우터
│   ├── schemas/        # Pydantic 스키마
│   ├── services/       # AI 분석 서비스
│   └── utils/          # 유틸리티 함수
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
