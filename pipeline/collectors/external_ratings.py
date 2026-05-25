"""
外部評鑑 collector
來源：
  1. 公民監督國會聯盟 (ccw.org.tw) — 問政評鑑
  2. Google News 搜尋「{name} 評鑑 問政」
  3. 廉政署/監察院相關紀錄

存入 external_ratings 表，並更新 politicians.external_rating
"""
import re
import json
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from config import supabase, ANTHROPIC_KEY
from loguru import logger
import anthropic

urllib_import = __import__("urllib3")
urllib_import.disable_warnings(urllib_import.exceptions.InsecureRequestWarning)

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

CCW_SEARCH   = "https://ccw.org.tw/?s={name}"
NEWS_RSS     = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
HEADERS      = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}

GRADE_SCORE  = {"A+": 97, "A": 92, "A-": 88, "B+": 83, "B": 77, "B-": 72,
                "C+": 67, "C": 62, "C-": 58, "D": 45, "F": 25,
                "優": 90, "良": 75, "可": 60, "劣": 35}

EXTRACT_PROMPT = """以下是關於「{name}」的問政評鑑相關文章標題與摘要。

請提取評鑑資訊，輸出 JSON（若無明確評鑑資訊輸出 null）：
{{
  "source": "評鑑機構名稱",
  "grade": "等第（如A/B/C或優/良/可/劣）",
  "score": 數值分數(0-100，若無則根據等第推算),
  "dimension": "評鑑面向（問政/出席/廉潔/綜合）",
  "year": 年份(整數),
  "notes": "簡短說明"
}}

只輸出 JSON 或 null。

文章：
{content}"""


def _get_politicians() -> list[dict]:
    return supabase.from_("politicians").select("id,name,party").execute().data or []


def collect_ccw_ratings(politicians: list[dict] | None = None):
    """收集公督盟及其他 NGO 評鑑"""
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]
        found = []

        # 1. 搜尋公督盟
        for query in [f"{name} 公督盟 評鑑", f"{name} 問政評鑑", f"{name} site:ccw.org.tw"]:
            url  = NEWS_RSS.format(query=requests.utils.quote(query))
            feed = feedparser.parse(url)
            for entry in (feed.entries or [])[:5]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                if name not in title + summary:
                    continue
                found.append(f"【{title}】{summary[:150]}")
            time.sleep(0.3)

        if not found:
            continue

        content = "\n".join(found[:4])
        try:
            resp = claude.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                messages=[{"role": "user", "content":
                    EXTRACT_PROMPT.format(name=name, content=content)
                }]
            )
            raw = re.sub(r"```(?:json)?\s*|\s*```", "",
                         resp.content[0].text.strip())
            result = json.loads(raw)
        except Exception:
            continue

        if not result or result == "null":
            continue

        grade = result.get("grade", "")
        score = result.get("score") or GRADE_SCORE.get(grade)
        if not score:
            continue

        supabase.from_("external_ratings").insert({
            "politician_id": pid,
            "source":        result.get("source", "公督盟"),
            "score":         float(score),
            "grade":         grade,
            "dimension":     result.get("dimension", "問政"),
            "year":          result.get("year"),
            "notes":         result.get("notes", "")[:200],
        }).execute()

        # 更新 politicians.external_rating（取平均）
        all_ratings = supabase.from_("external_ratings")\
            .select("score").eq("politician_id", pid).execute().data or []
        if all_ratings:
            avg = sum(r["score"] for r in all_ratings) / len(all_ratings)
            supabase.from_("politicians").update({
                "external_rating": round(avg, 2)
            }).eq("id", pid).execute()

        logger.info(f"  {name}: 外部評鑑 {grade}（{score}分）")
        total += 1
        time.sleep(0.5)

    logger.success(f"外部評鑑收集完成：{total} 筆")
    return total


def collect_monitoring_records(politicians: list[dict] | None = None):
    """收集監察院彈劾/糾正紀錄"""
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]

        query = f"{name} 監察院 彈劾 糾正"
        url   = NEWS_RSS.format(query=requests.utils.quote(query))
        feed  = feedparser.parse(url)

        for entry in (feed.entries or [])[:3]:
            title = entry.get("title", "")
            if name not in title or "監察" not in title + entry.get("summary",""):
                continue

            # 有監察院紀錄，作為負面外部評鑑
            supabase.from_("external_ratings").insert({
                "politician_id": pid,
                "source":        "監察院",
                "score":         20.0,   # 被彈劾/糾正 = 低分
                "grade":         "D",
                "dimension":     "廉潔",
                "notes":         title[:200],
            }).execute()
            total += 1
            logger.info(f"  {name}: 監察院紀錄")
            break

        time.sleep(0.3)

    logger.success(f"監察院紀錄收集完成：{total} 筆")
    return total
