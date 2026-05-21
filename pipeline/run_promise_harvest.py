"""
承諾大規模採集：針對每位政治人物搜尋政見新聞 → Claude 提取承諾 → 寫入 DB
執行：python run_promise_harvest.py
"""
import sys
import json
import time
import random
import requests
import feedparser
import anthropic
from loguru import logger
from config import ANTHROPIC_KEY, SUPABASE_URL, SUPABASE_KEY
from db.supabase_client import get_client

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | {level} | {message}")

ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SEARCH_QUERIES = [
    "{name} 政見",
    "{name} 承諾 選舉",
    "{name} 政策 宣示",
    "{name} 施政 目標",
]

EXTRACT_PROMPT = """你是台灣政治承諾分析專家。

以下是關於「{name}」的新聞摘要，請從中提取他/她的所有**具體承諾或政見宣示**。

規則：
- 只取明確的承諾（「我要…」「將會…」「保證…」「目標…」）
- 排除評論、批評他人的言論
- 若同一承諾出現多次，只保留一筆

以 JSON 陣列回傳，每筆：
{{
  "text": "承諾原文（保留原話，50字內）",
  "summary": "15字內摘要",
  "deadline": "YYYY-MM-DD" 或 "任期內" 或 "儘速" 或 null,
  "scope": "全國/特定縣市/特定族群",
  "keywords": ["關鍵字1", "關鍵字2"],
  "source_url": "新聞網址",
  "confidence": 0.0~1.0
}}

只回傳 JSON 陣列，沒有承諾則回傳 []。"""


def search_promises_rss(name: str) -> list[dict]:
    """用 Google News RSS 搜尋政治人物的承諾相關新聞"""
    articles = []
    for query_template in SEARCH_QUERIES[:2]:
        query = query_template.format(name=name)
        url = (
            f"https://news.google.com/rss/search"
            f"?q={requests.utils.quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        )
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                articles.append({
                    "title": entry.get("title", ""),
                    "snippet": entry.get("summary", "")[:300],
                    "url": entry.get("link", ""),
                    "date": entry.get("published", ""),
                })
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"RSS 搜尋失敗 {name}：{e}")

    # 去重（依 title）
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique


def extract_promises_with_ai(name: str, articles: list[dict]) -> list[dict]:
    """用 Claude 從新聞中提取承諾"""
    if not articles:
        return []

    news_text = "\n\n".join([
        f"標題：{a['title']}\n日期：{a['date']}\n摘要：{a['snippet']}\n網址：{a['url']}"
        for a in articles
    ])

    prompt = EXTRACT_PROMPT.format(name=name) + f"\n\n---新聞資料---\n{news_text}"

    try:
        resp = ai.messages.create(
            model="claude-haiku-4-5",   # 用 Haiku 節省 token
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        promises = json.loads(raw)
        return [p for p in promises if p.get("confidence", 0) >= 0.55]
    except json.JSONDecodeError:
        logger.warning(f"JSON 解析失敗：{name}")
        return []
    except Exception as e:
        logger.error(f"AI 提取失敗 {name}：{e}")
        if "rate_limit" in str(e).lower():
            logger.info("Rate limit，等待 60 秒...")
            time.sleep(60)
        return []


def run():
    db = get_client()

    # 取得所有政治人物
    politicians = db.table("politicians").select("id, name, party, role").execute().data
    logger.info(f"共 {len(politicians)} 位政治人物，開始採集承諾")

    total_new = 0
    total_skip = 0

    for i, pol in enumerate(politicians, 1):
        name = pol["name"]
        pol_id = pol["id"]
        logger.info(f"[{i:02d}/{len(politicians)}] {pol['party']} {name}")

        # 搜尋新聞
        articles = search_promises_rss(name)
        if not articles:
            logger.debug(f"  無新聞：{name}")
            continue
        logger.debug(f"  找到 {len(articles)} 篇新聞")

        # AI 提取承諾
        promises = extract_promises_with_ai(name, articles)
        if not promises:
            logger.debug(f"  未提取到承諾：{name}")
            continue
        logger.info(f"  提取到 {len(promises)} 筆承諾")

        # 寫入 DB（直接 insert，避免重複靠 summary+politician_id 比對）
        existing_summaries = {
            r["summary"]
            for r in db.table("promises")
               .select("summary")
               .eq("politician_id", pol_id)
               .execute().data
        }

        for p in promises:
            summary = p.get("summary", "")[:100]
            if summary in existing_summaries:
                total_skip += 1
                continue

            deadline_raw = p.get("deadline")
            # 只保留合法的 date 格式，文字型的放 None
            import re
            deadline = deadline_raw if (deadline_raw and re.match(r"\d{4}-\d{2}-\d{2}", str(deadline_raw))) else None

            record = {
                "politician_id": pol_id,
                "text":          p.get("text", "")[:500],
                "summary":       summary,
                "status":        "active",
                "deadline":      deadline,
                "source_url":    p.get("source_url", ""),
                "confidence":    p.get("confidence", 0.6),
                "verified_by":   "auto:harvest",
            }
            try:
                db.table("promises").insert(record).execute()
                existing_summaries.add(summary)
                total_new += 1
                logger.debug(f"    [+] {summary[:30]}")
            except Exception as e:
                logger.error(f"    寫入失敗：{e}")
                total_skip += 1

        # 禮貌等待，避免打爆 Google News
        time.sleep(random.uniform(1.5, 3.0))

    logger.success(f"採集完成｜新增 {total_new} 筆承諾，跳過 {total_skip} 筆")


if __name__ == "__main__":
    run()
