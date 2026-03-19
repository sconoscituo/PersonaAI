# PersonaAI

SNS 공개 프로필 링크 또는 사용자명을 입력하면 AI가 성격/가치관/라이프스타일을 분석해주는 서비스입니다.

## 주요 기능

- **SNS 스크래핑**: 인스타그램/트위터 공개 프로필 정보 수집 (bio, 팔로워, 해시태그)
- **AI 성격 분석**: Google Gemini AI를 통한 MBTI 추정, 성격 유형, 가치관, 관심사 분석
- **리포트 생성**: 강점/약점, 라이프스타일 등 상세 분석 결과 제공
- **구독 모델**: 무료 분석 (일 5회) + 프리미엄 상세 리포트 PDF (건당 결제)

## 주의사항

- **공개 프로필만 분석**합니다. 비공개 계정은 분석이 불가능합니다.
- 개인정보 보호를 위해 수집된 데이터는 분석 후 저장하지 않습니다.
- 분석 결과는 AI의 추정이며 실제 성격과 다를 수 있습니다.

## 시작하기

### 환경 설정

```bash
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY 설정
```

### 설치 및 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Docker로 실행

```bash
docker-compose up -d
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /analyze | SNS URL/사용자명 분석 요청 |
| GET | /analyze/{id} | 분석 결과 조회 |
| POST | /users/register | 회원가입 |
| POST | /users/login | 로그인 |
| GET | /users/me | 내 정보 조회 |

## 분석 결과 예시

```json
{
  "mbti_guess": "ENFP",
  "personality_type": "열정적인 탐험가",
  "values": ["자유", "창의성", "연결"],
  "interests": ["여행", "사진", "음식"],
  "lifestyle": "활동적이고 사교적인 라이프스타일",
  "strengths": ["공감 능력", "창의적 사고"],
  "weaknesses": ["계획성 부족", "집중력 분산"],
  "description": "..."
}
```

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy, aiosqlite
- **AI**: Google Gemini 1.5 Flash
- **스크래핑**: httpx, BeautifulSoup4
- **Auth**: JWT (python-jose)
- **배포**: Docker, docker-compose
