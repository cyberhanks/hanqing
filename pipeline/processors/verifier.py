"""承諾核實器：每週掃描進行中的承諾，搜尋新聞，AI 判斷狀態"""
import json
import anthropic
from pathlib import Path
from loguru import logger
from config import ANTHROPIC_KEY
from collectors.news_search import search_news, search_news_rss

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
VERIFY_PROMPT = Path("prompts/verify.txt").read_text(encoding="utf-8")
REQUIRES_HUMAN_CONFIRM = {"fulfilled", "broken"}


def verify_promise(promise: dict, politician_name: str) -> dict:
    keywords = promise.get("keywords") or []
    if not keywords:
        keywords = [w for w in (promise.get("summary") or "") if len(w) > 1][:4]

    news = search_news(keywords, politician_name)
    if not news:
        news = search_news_rss(keywords, politician_name)
    if not news:
        return {"status": "active", "confidence": 0.3, "reasoning": "無相關新聞"}

    news_summary = "\n\n".join([
        f"標題：{n['title']}\n摘要：{n['snippet']}\n網址：{n['url']}"
        for n in news[:5]
    ])

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": (
                f"{VERIFY_PROMPT}\n\n"
                f"政治人物：{politician_name}\n"
                f"承諾內容：{promise.get('text', '')}\n"
                f"承諾摘要：{promise.get('summary', '')}\n"
                f"承諾期限：{promise.get('deadline', '未知')}\n\n"
                f"相關新聞：\n{news_summary}"
            )}]
        )
        raw = response.content[0].text.strip()
        raw = raw.removeprefix("```json").removesuffix("```").strip()
        result = json.loads(raw)

        if result["status"] != promise.get("status", "active"):
            logger.info(
                f"狀態變更：{politician_name} / "
                f"{promise.get('summary', '')[:20]} -> {result['status']}"
            )
        return result
    except Exception as e:
        logger.error(f"核實失敗：{e}")
        return {"status": "active", "confidence": 0, "reasoning": f"核實失敗：{e}"}
