from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 로그인 정보
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # 프리미엄 여부
    is_premium = Column(Boolean, default=False, nullable=False)

    # 오늘 분석 횟수 (무료 플랜 일일 제한용)
    analysis_count = Column(Integer, default=0, nullable=False)

    # 일일 카운트 초기화 기준일 (YYYY-MM-DD 형태)
    count_reset_date = Column(String(10), default="", nullable=False)

    # 활성 계정 여부
    is_active = Column(Boolean, default=True, nullable=False)

    # 가입 및 수정 시각
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 분석 목록 (역참조)
    analyses = relationship("PersonaAnalysis", back_populates="user", cascade="all, delete-orphan")
