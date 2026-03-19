import json
import re
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()

# Gemini 클라이언트 초기화
genai.configure(api_key=settings.gemini_api_key)
_gemini_model = genai.GenerativeModel("gemini-1.5-flash")


def _clean_json_response(text: str) -> str:
    """Gemini 응답에서 마크다운 코드블록 제거 후 순수 JSON만 추출"""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


async def analyze_persona(platform: str, profile_data: dict) -> dict:
    """
    수집된 SNS 프로필 데이터를 Gemini AI로 분석하여 성격 리포트 생성

    Args:
        platform: "instagram" | "twitter" | "unknown"
        profile_data: scraper.py에서 수집한 프로필 딕셔너리

    Returns:
        {
            "mbti_guess": str,         # 추정 MBTI (예: ENFP)
            "personality_type": str,    # 성격 유형명 (예: 열정적인 탐험가)
            "values": [str],            # 핵심 가치관 3~5개
            "interests": [str],         # 관심사/취미 3~7개
            "lifestyle": str,           # 라이프스타일 한 문장 설명
            "strengths": [str],         # 강점 3~5개
            "weaknesses": [str],        # 약점 2~3개
            "description": str          # 종합 분석 2~3문단
        }
    """
    raw_text = profile_data.get("raw_text", "")

    # 수집된 데이터가 너무 적으면 제한된 분석 수행
    if not raw_text or len(raw_text.strip()) < 20:
        return _minimal_result(profile_data.get("username", "unknown"))

    platform_desc = {
        "instagram": "인스타그램",
        "twitter": "트위터/X",
    }.get(platform, "SNS")

    prompt = f"""
다음은 {platform_desc} 공개 프로필에서 수집한 정보입니다.

[프로필 정보]
{raw_text[:3000]}

이 사람의 공개 SNS 프로필을 분석하여 성격과 라이프스타일을 추론해주세요.
이것은 재미와 인사이트를 위한 분석이며, 공개된 정보만을 기반으로 합니다.

다른 설명 없이 아래 형식의 JSON만 반환하세요:

{{
  "mbti_guess": "MBTI 유형 (예: ENFP, 확실하지 않으면 'XXXX')",
  "personality_type": "성격 유형 별명 (예: 열정적인 탐험가, 창의적인 몽상가)",
  "values": ["핵심가치1", "핵심가치2", "핵심가치3"],
  "interests": ["관심사1", "관심사2", "관심사3", "관심사4"],
  "lifestyle": "라이프스타일을 한 문장으로 설명",
  "strengths": ["강점1", "강점2", "강점3"],
  "weaknesses": ["약점1", "약점2"],
  "description": "이 사람의 성격과 가치관에 대한 종합적인 분석을 2~3문단으로 작성. 긍정적이고 흥미로운 시각으로 서술."
}}

요구사항:
- 수집된 정보가 적더라도 가능한 범위에서 창의적으로 추론
- 모든 내용은 한국어로 작성
- 긍정적이고 흥미로운 톤 유지
- JSON 형식 엄수
"""

    try:
        response = _gemini_model.generate_content(prompt)
        raw_response = response.text
        clean_text = _clean_json_response(raw_response)
        result = json.loads(clean_text)

        # 필수 키 누락 보완
        result.setdefault("mbti_guess", "XXXX")
        result.setdefault("personality_type", "분석 중")
        result.setdefault("values", [])
        result.setdefault("interests", [])
        result.setdefault("lifestyle", "")
        result.setdefault("strengths", [])
        result.setdefault("weaknesses", [])
        result.setdefault("description", "")

        return result

    except json.JSONDecodeError as e:
        return _minimal_result(
            profile_data.get("username", "unknown"),
            error=f"JSON 파싱 오류: {str(e)}"
        )
    except Exception as e:
        return _minimal_result(
            profile_data.get("username", "unknown"),
            error=f"Gemini API 오류: {str(e)}"
        )


def _minimal_result(username: str, error: str = "") -> dict:
    """분석 실패 또는 데이터 부족 시 기본 결과 반환"""
    desc = (
        f"@{username} 프로필의 공개 정보가 충분하지 않아 상세 분석이 어렵습니다. "
        "더 많은 공개 정보가 있는 프로필을 시도해보세요."
    )
    if error:
        desc = f"{desc} (오류: {error})"

    return {
        "mbti_guess": "XXXX",
        "personality_type": "분석 불가",
        "values": [],
        "interests": [],
        "lifestyle": "공개 정보 부족으로 분석 불가",
        "strengths": [],
        "weaknesses": [],
        "description": desc,
    }
