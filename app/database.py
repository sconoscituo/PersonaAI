from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# 비동기 SQLAlchemy 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """모든 SQLAlchemy 모델의 기본 클래스"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입용 DB 세션 제공"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """애플리케이션 시작 시 테이블 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
