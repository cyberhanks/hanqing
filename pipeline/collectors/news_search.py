"""新聞搜尋器：搜尋承諾相關新聞"""
import time
import requests
from loguru import logger


def search_news_rss(keywords: list[str], politician: str) -> list[dict]:
    """Google News RSS（不需 API Key）"""
    try:
        import feedparser
        query = f"{politician} {' '.join(keywords[:2])}"
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        return [
            {"title": e.title, "url": e.link,
             "snippet": e.get("summary", ""), "date": e.get("published", "")}
            for e in feed.entries[:5]
        ]
    except Exception as e:
        logger.error(f"RSS 搜尋失敗：{e}")
        return []


def search_news(keywords: list[str], politician: str,
                google_api_key: str = "", google_cse_id: str = "") -> list[dict]:
    """優先用 Google API，否則用 RSS"""
    if google_api_key and google_cse_id:
        try:
            query = f"{politician} {' '.join(keywords[:3])}"
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": google_api_key, "cx": google_cse_id,
                        "q": query, "lr": "lang_zh-TW", "num": 5, "sort": "date"},
                timeout=15
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            time.sleep(0.5)
            return [{"title": i.get("title", ""), "url": i.get("link", ""),
                     "snippet": i.get("snippet", ""), "date": ""}
                    for i in items]
        except Exception as e:
            logger.warning(f"Google API 失敗，改用 RSS：{e}")

    return search_news_rss(keywords, politician)
