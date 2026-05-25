"""
媒體輿情分析 processor — v5
來源：Google News RSS（每位政治人物 × 4 個查詢）
存入 news_sentiment 表，並更新 politicians.sentiment_score + news_positive_ratio

情緒分類邏輯（Claude Haiku）：
  positive  → 正面報導（政績/讚揚/獲獎）
  negative  → 負面報導（醜聞/批評/錯誤）
  neutral   → 中性報導（出席/說明/聲明）

sentiment_score = positive_ratio * 0.6 + neutral_ratio * 0.3 + (1-negative_ratio) * 0.1 × 100
"""
import re
import json
import time
import requests
import feedparser
from datetime import datetime
from config import supabase, ANTHROPIC_KEY
from loguru import logger
import anthropic

urllib_import = __import__("urllib3")
urllib_import.disable_warnings(urllib_import.exceptions.InsecureRequestWarning)

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

CLASSIFY_PROMPT = """你是台灣新聞分析師。以下是關於「{name}」的新聞標題清單。
請逐一分類每條標題的情緒傾向，輸出 JSON 陣列：

[
  {{"title": "標題", "sentiment": "positive/negative/neutral", "reason": "5字內"}},
  ...
]

分類準則：
- positive：政績展現、獲肯定、推動有益政策
- negative：醜聞/貪腐、出錯/失言、被批評/被告
- neutral：一般出席、例行發言、政策說明

只輸出 JSON 陣列，不要說明。

標題：
{titles}"""

QUERIES = [
    "{name} 政績",
    "{name} 爭議",
    "{name} 批評",
    "{name} 表現",
]


def _get_politicians() -> list[dict]:
    return supabase.from_("politicians").select("id,name").execute().data or []


def _current_period() -> str:
    now = datetime.now()
    q = (now.month - 1) // 3 + 1
    return f"{now.year}-Q{q}"


def analyse_sentiment(politicians: list[dict] | None = None) -> int:
    if politicians is None:
        politicians = _get_politicians()

    period = _current_period()
    total_written = 0

    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]

        # 收集新聞標題
        titles: list[str] = []
        for tmpl in QUERIES:
            query = tmpl.format(name=name)
            url   = NEWS_RSS.format(query=requests.utils.quote(query))
            feed  = feedparser.parse(url)
            for entry in (feed.entries or [])[:8]:
                t = entry.get("title", "").strip()
                if name in t and t not in titles:
                    titles.append(t)
            time.sleep(0.2)

        if not titles:
            continue

        # Claude 分類
        try:
            resp = claude.messages.create(
                model="claude-haiku-4-5",
                max_tokens=800,
                messages=[{"role": "user", "content":
                    CLASSIFY_PROMPT.format(
                        name=name,
                        titles="\n".join(f"- {t}" for t in titles[:20])
                    )
                }]
            )
            raw = re.sub(r"```(?:json)?\s*|\s*```", "",
                         resp.content[0].text.strip())
            items: list[dict] = json.loads(raw)
        except Exception as e:
            logger.debug(f"  {name} sentiment parse error: {e}")
            time.sleep(0.5)
            continue

        # 統計
        pos_count = sum(1 for i in items if i.get("sentiment") == "positive")
        neg_count = sum(1 for i in items if i.get("sentiment") == "negative")
        neu_count = sum(1 for i in items if i.get("sentiment") == "neutral")
        total     = pos_count + neg_count + neu_count or 1

        pos_ratio = round(pos_count / total * 100, 2)
        neg_ratio = round(neg_count / total * 100, 2)
        neu_ratio = round(neu_count / total * 100, 2)

        # sentiment_score：以正面為主，中性中立，負面拉低
        sentiment_score = round(
            pos_ratio * 0.6 +
            neu_ratio * 0.3 +
            (100 - neg_ratio) * 0.1,
            2
        )

        # 主要議題標籤（取負面標題關鍵詞）
        sample_topics = [
            i["title"][:30] for i in items
            if i.get("sentiment") == "negative"
        ][:5]

        # 寫入 news_sentiment
        try:
            supabase.from_("news_sentiment").upsert({
                "politician_id":  pid,
                "period":         period,
                "positive_count": pos_count,
                "negative_count": neg_count,
                "neutral_count":  neu_count,
                "total_count":    total,
                "positive_ratio": pos_ratio,
                "sample_topics":  sample_topics,
            }, on_conflict="politician_id,period").execute()

            # 更新 politicians 欄位
            supabase.from_("politicians").update({
                "sentiment_score":     sentiment_score,
                "news_positive_ratio": pos_ratio,
            }).eq("id", pid).execute()

            logger.info(f"  {name}: +{pos_count} -{neg_count} ={neu_count} → score {sentiment_score}")
            total_written += 1
        except Exception as e:
            logger.debug(f"  {name} write error: {e}")

        time.sleep(0.5)

    logger.success(f"輿情分析完成：{total_written} 位")
    return total_written
