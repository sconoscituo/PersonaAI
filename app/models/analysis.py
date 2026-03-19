from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PersonaAnalysis(Base):
    """SNS 프로필 분석 결과 모델"""

    __tablename__ = "persona_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # 소유 사용자 (비회원도 허용하기 위해 nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # 입력된 SNS URL 또는 사용자명
    input_url = Column(String(500), nullable=False)

    # 감지된 플랫폼 (instagram / twitter / unknown)
    platform = Column(String(50), default="unknown")

    # Gemini 분석 결과 JSON 문자열
    # {mbti_guess, personality_type, values[], interests[], lifestyle, strengths[], weaknesses[], description}
    persona_json = Column(Text, default="{}")

    # 프리미엄 PDF 리포트 경로 (생성된 경우)
    report_pdf_path = Column(String(500), default="")

    # 처리 상태 (pending / processing / done / error)
    status = Column(String(20), default="pending", nullable=False)

    # 오류 메시지
    error_message = Column(Text, default="")

    # 생성 시각
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 사용자 역참조
    user = relationship("User", back_populates="analyses")
