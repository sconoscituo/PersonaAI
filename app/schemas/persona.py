from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AnalysisRequest(BaseModel):
    """분석 요청 스키마 - SNS URL 또는 사용자명 입력"""
    input_url: str = Field(
        ...,
        description="분석할 SNS URL 또는 사용자명 (예: https://instagram.com/username 또는 @username)",
        examples=["https://www.instagram.com/cristiano/", "@elonmusk"],
    )


class PersonaResult(BaseModel):
    """Gemini AI 성격 분석 결과 스키마"""
    mbti_guess: str = Field(default="", description="추정 MBTI 유형 (예: ENFP)")
    personality_type: str = Field(default="", description="성격 유형 명칭 (예: 열정적인 탐험가)")
    values: List[str] = Field(default=[], description="핵심 가치관 목록")
    interests: List[str] = Field(default=[], description="관심사/취미 목록")
    lifestyle: str = Field(default="", description="라이프스타일 설명")
    strengths: List[str] = Field(default=[], description="강점 목록")
    weaknesses: List[str] = Field(default=[], description="약점 목록")
    description: str = Field(default="", description="종합 성격 분석 설명")


class AnalysisResponse(BaseModel):
    """분석 결과 응답 스키마"""
    id: int
    input_url: str
    platform: str
    persona: Optional[PersonaResult] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListItem(BaseModel):
    """분석 목록 아이템 스키마"""
    id: int
    input_url: str
    platform: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """회원가입 요청 스키마"""
    email: str = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")


class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: str
    password: str


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""
    id: int
    email: str
    is_premium: bool
    analysis_count: int

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
