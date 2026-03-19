import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.analysis import PersonaAnalysis
from app.schemas.persona import AnalysisRequest, AnalysisResponse, AnalysisListItem, PersonaResult
from app.services.scraper import scrape_profile
from app.services.persona_analyzer import analyze_persona
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/analyze", tags=["analyze"])
settings = get_settings()


def _check_daily_limit(user: User) -> None:
    """
    무료 사용자의 일일 분석 횟수 초과 여부 확인.
    날짜가 바뀌면 카운트 자동 초기화.
    """
    if user.is_premium:
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if user.count_reset_date != today:
        user.analysis_count = 0
        user.count_reset_date = today

    if user.analysis_count >= settings.free_daily_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"무료 플랜은 하루 {settings.free_daily_limit}회까지 분석 가능합니다. "
                "내일 다시 시도하거나 프리미엄으로 업그레이드하세요."
            ),
        )


def _build_response(analysis: PersonaAnalysis) -> AnalysisResponse:
    """PersonaAnalysis ORM 객체를 응답 스키마로 변환"""
    persona = None
    try:
        raw = json.loads(analysis.persona_json or "{}")
        if raw:
            persona = PersonaResult(**raw)
    except (json.JSONDecodeError, TypeError, Exception):
        persona = None

    return AnalysisResponse(
        id=analysis.id,
        input_url=analysis.input_url,
        platform=analysis.platform,
        persona=persona,
        status=analysis.status,
        error_message=analysis.error_message or None,
        created_at=analysis.created_at,
    )


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    SNS 공개 프로필 분석

    1. 일일 사용 횟수 확인 (무료 플랜)
    2. URL/사용자명에서 플랫폼 감지
    3. 공개 프로필 스크래핑
    4. Gemini AI로 성격 분석
    5. 결과 DB 저장 후 반환
    """
    # 무료 플랜 일일 한도 확인
    _check_daily_limit(current_user)

    # DB에 처리 중 상태로 기록
    analysis = PersonaAnalysis(
        user_id=current_user.id,
        input_url=request.input_url,
        status="processing",
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    try:
        # SNS 프로필 스크래핑
        scrape_result = await scrape_profile(request.input_url)
        platform = scrape_result["platform"]
        profile_data = scrape_result["data"]

        analysis.platform = platform

        # Gemini AI 성격 분석
        persona = await analyze_persona(platform, profile_data)

        # 결과 저장
        analysis.persona_json = json.dumps(persona, ensure_ascii=False)
        analysis.status = "done"

        # 무료 사용 횟수 증가
        if not current_user.is_premium:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            current_user.count_reset_date = today
            current_user.analysis_count += 1

        await db.flush()

    except HTTPException:
        analysis.status = "error"
        analysis.error_message = "플랜 제한 초과"
        await db.flush()
        raise
    except Exception as e:
        analysis.status = "error"
        analysis.error_message = str(e)
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}",
        )

    return _build_response(analysis)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """특정 분석 결과 조회"""
    result = await db.execute(
        select(PersonaAnalysis).where(
            PersonaAnalysis.id == analysis_id,
            PersonaAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="분석 결과를 찾을 수 없습니다.",
        )
    return _build_response(analysis)


@router.get("", response_model=list[AnalysisListItem])
async def list_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 분석 목록 조회 (최신순)"""
    result = await db.execute(
        select(PersonaAnalysis)
        .where(PersonaAnalysis.user_id == current_user.id)
        .order_by(PersonaAnalysis.created_at.desc())
    )
    return result.scalars().all()
