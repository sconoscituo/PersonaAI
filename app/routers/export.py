"""
페르소나 내보내기 라우터
"""
import json
import io
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/export", tags=["내보내기"])

try:
    from app.models.persona import Persona
    HAS_PERSONA = True
except ImportError:
    HAS_PERSONA = False


@router.get("/{persona_id}/json")
async def export_persona_json(
    persona_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """페르소나 JSON 내보내기"""
    if not HAS_PERSONA:
        raise HTTPException(404, "페르소나 모델이 없습니다")

    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "페르소나를 찾을 수 없습니다")

    # 페르소나 데이터 직렬화
    data = {
        "id": persona.id,
        "name": getattr(persona, "name", ""),
        "description": getattr(persona, "description", ""),
        "traits": getattr(persona, "traits", {}),
        "created_at": str(getattr(persona, "created_at", "")),
    }
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="persona_{persona_id}.json"'},
    )


@router.get("/{persona_id}/markdown")
async def export_persona_markdown(
    persona_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """페르소나 Markdown 내보내기"""
    if not HAS_PERSONA:
        raise HTTPException(404, "페르소나 모델이 없습니다")

    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "페르소나를 찾을 수 없습니다")

    name = getattr(persona, "name", "페르소나")
    description = getattr(persona, "description", "")
    traits = getattr(persona, "traits", {})

    md = f"# {name}\n\n## 설명\n{description}\n\n## 특성\n"
    if isinstance(traits, dict):
        for k, v in traits.items():
            md += f"- **{k}**: {v}\n"

    return Response(
        content=md.encode("utf-8"),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="persona_{persona_id}.md"'},
    )
