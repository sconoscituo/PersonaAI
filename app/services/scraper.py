import re
import httpx
from bs4 import BeautifulSoup
from app.config import get_settings

settings = get_settings()

# 플랫폼 감지 패턴
INSTAGRAM_PATTERNS = [
    r"instagram\.com/([^/?#]+)",
    r"@([a-zA-Z0-9_.]+)",  # @username 형식
]
TWITTER_PATTERNS = [
    r"(?:twitter|x)\.com/([^/?#]+)",
    r"@([a-zA-Z0-9_]+)",
]

# 공통 HTTP 헤더 (봇 차단 우회용 일반 브라우저 헤더)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def detect_platform(input_url: str) -> tuple[str, str]:
    """
    입력값에서 플랫폼과 사용자명을 감지

    Returns:
        (platform, username) - platform: "instagram" | "twitter" | "unknown"
    """
    url = input_url.strip().rstrip("/")

    # 인스타그램 URL 패턴
    if "instagram.com" in url:
        match = re.search(r"instagram\.com/([^/?#\s]+)", url)
        if match:
            return "instagram", match.group(1)

    # 트위터/X URL 패턴
    if "twitter.com" in url or "x.com" in url:
        match = re.search(r"(?:twitter|x)\.com/([^/?#\s]+)", url)
        if match:
            username = match.group(1)
            # 예약어 제외
            if username not in ("home", "explore", "notifications", "messages"):
                return "twitter", username

    # @username 형식 처리 (플랫폼 미지정 → 인스타그램으로 기본 처리)
    if url.startswith("@"):
        return "instagram", url[1:]

    # 순수 사용자명 (알파벳/숫자/._만 포함)
    if re.match(r"^[a-zA-Z0-9_.]+$", url):
        return "instagram", url

    return "unknown", url


async def scrape_instagram(username: str) -> dict:
    """
    인스타그램 공개 프로필 정보 수집

    Instagram의 공개 프로필 페이지에서 메타 태그와 구조화 데이터를 파싱.
    로그인 없이 접근 가능한 공개 정보만 수집.

    Returns:
        {
            "username": str,
            "bio": str,
            "followers": str,
            "following": str,
            "post_count": str,
            "hashtags": [str],   # bio에서 추출한 해시태그
            "raw_text": str      # 분석용 원본 텍스트
        }
    """
    url = f"https://www.instagram.com/{username}/"

    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=settings.scrape_timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return _empty_profile(username, f"HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        # meta description에서 팔로워/게시물 수 파싱
        # 형식: "2,450 Followers, 1,234 Following, 890 Posts - See Instagram photos..."
        meta_desc = ""
        meta_tag = soup.find("meta", {"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        # bio는 og:description에 포함되는 경우가 많음
        og_desc = ""
        og_tag = soup.find("meta", {"property": "og:description"})
        if og_tag:
            og_desc = og_tag.get("content", "")

        # title에서 사용자 표시명 추출
        og_title = ""
        title_tag = soup.find("meta", {"property": "og:title"})
        if title_tag:
            og_title = title_tag.get("content", "")

        # 팔로워 수 파싱 시도
        followers = _extract_count(meta_desc, "Followers") or _extract_count(meta_desc, "팔로워")
        following = _extract_count(meta_desc, "Following") or _extract_count(meta_desc, "팔로잉")
        post_count = _extract_count(meta_desc, "Posts") or _extract_count(meta_desc, "게시물")

        # bio 텍스트 (og:description 우선, 없으면 meta description 사용)
        bio = og_desc or meta_desc

        # bio에서 해시태그 추출
        hashtags = re.findall(r"#(\w+)", bio)

        raw_text = f"사용자명: {username}\n표시명: {og_title}\nbio: {bio}\n팔로워: {followers}\n팔로잉: {following}\n게시물 수: {post_count}\n해시태그: {', '.join(hashtags)}"

        return {
            "username": username,
            "bio": bio,
            "followers": followers,
            "following": following,
            "post_count": post_count,
            "hashtags": hashtags,
            "raw_text": raw_text,
        }

    except httpx.TimeoutException:
        return _empty_profile(username, "요청 시간 초과")
    except Exception as e:
        return _empty_profile(username, str(e))


async def scrape_twitter(username: str) -> dict:
    """
    트위터/X 공개 프로필 정보 수집

    공개 프로필 페이지의 메타 태그에서 bio와 기본 정보 파싱.

    Returns:
        {
            "username": str,
            "bio": str,
            "followers": str,
            "tweet_count": str,
            "hashtags": [str],
            "raw_text": str
        }
    """
    # nitter (오픈소스 트위터 프론트엔드)를 우선 시도, 실패 시 twitter.com 직접 접근
    nitter_url = f"https://nitter.net/{username}"
    twitter_url = f"https://twitter.com/{username}"

    for url in [nitter_url, twitter_url]:
        try:
            async with httpx.AsyncClient(
                headers=HEADERS,
                timeout=settings.scrape_timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # og:description에서 bio 추출
            bio = ""
            og_desc = soup.find("meta", {"property": "og:description"})
            if og_desc:
                bio = og_desc.get("content", "")

            og_title = ""
            title_tag = soup.find("meta", {"property": "og:title"})
            if title_tag:
                og_title = title_tag.get("content", "")

            # 팔로워 수 (nitter 형식)
            followers = ""
            follower_tag = soup.find(class_="followers")
            if follower_tag:
                followers = follower_tag.get_text(strip=True)

            # bio에서 해시태그 추출
            hashtags = re.findall(r"#(\w+)", bio)

            raw_text = f"사용자명: @{username}\n표시명: {og_title}\nbio: {bio}\n팔로워: {followers}\n해시태그: {', '.join(hashtags)}"

            return {
                "username": username,
                "bio": bio,
                "followers": followers,
                "tweet_count": "",
                "hashtags": hashtags,
                "raw_text": raw_text,
            }

        except Exception:
            continue

    return _empty_profile(username, "프로필 정보를 가져올 수 없습니다.")


async def scrape_profile(input_url: str) -> dict:
    """
    플랫폼 자동 감지 후 SNS 프로필 스크래핑 수행

    Args:
        input_url: SNS URL 또는 사용자명

    Returns:
        {"platform": str, "data": dict, "error": str}
    """
    platform, username = detect_platform(input_url)

    if platform == "instagram":
        data = await scrape_instagram(username)
    elif platform == "twitter":
        data = await scrape_twitter(username)
    else:
        # 알 수 없는 플랫폼은 URL 자체를 텍스트로 넘겨 분석
        data = {
            "username": input_url,
            "bio": "",
            "raw_text": f"입력값: {input_url}",
        }

    return {"platform": platform, "username": username, "data": data}


def _extract_count(text: str, keyword: str) -> str:
    """텍스트에서 'N Keyword' 패턴으로 숫자 추출"""
    pattern = rf"([\d,]+)\s+{keyword}"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def _empty_profile(username: str, error: str = "") -> dict:
    """스크래핑 실패 시 빈 프로필 반환"""
    return {
        "username": username,
        "bio": "",
        "followers": "",
        "following": "",
        "post_count": "",
        "hashtags": [],
        "raw_text": f"사용자명: {username}\n(프로필 정보 수집 실패: {error})",
        "error": error,
    }
