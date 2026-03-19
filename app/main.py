from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import analyze, users, export
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트 처리"""
    await init_db()
    print("[PersonaAI] 서버 시작 완료")
    yield
    print("[PersonaAI] 서버 종료")


app = FastAPI(
    title="PersonaAI",
    description="SNS 공개 프로필 분석 AI - 성격/가치관/라이프스타일 분석",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router)
app.include_router(analyze.router)
app.include_router(export.router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def root():
    """헬스 체크 엔드포인트"""
    return {
        "service": "PersonaAI",
        "status": "running",
        "version": "1.0.0",
        "notice": "공개 프로필만 분석합니다. 개인정보 보호 정책을 준수합니다.",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok"}
