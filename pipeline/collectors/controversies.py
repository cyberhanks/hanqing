"""
爭議事件 collector
來源 1：Google News RSS（近 10 年）
來源 2：維基百科爭議段落

存入 events 表
"""
import re
import time
import requests
import feedparser
from datetime import datetime
from config import supabase, ANTHROPIC_KEY
from loguru import logger
import anthropic

CONTROVERSY_KEYWORDS = [
    "爭議", "失言", "醜聞", "貪腐", "起訴", "收賄",
    "性騷擾", "抄襲", "造假", "違規", "被批", "遭批",
    "風波", "弊案", "炎上", "下台", "辭職", "停職",
]

NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
WIKI_API = "https://zh.wikipedia.org/api/rest_v1/page/summary/{name}"
WIKI_FULL = "https://zh.wikipedia.org/w/api.php"

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


def _get_politicians() -> list[dict]:
    res = supabase.from_("politicians").select("id, name").execute()
    return res.data or []


def collect_news_controversies(politicians: list[dict] | None = None):
    """從 Google News 蒐集每位政治人物的爭議新聞"""
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]
        inserted = 0

        for kw in CONTROVERSY_KEYWORDS[:6]:   # 每人前 6 個關鍵字
            query = f"{name} {kw}"
            url = NEWS_RSS.format(query=requests.utils.quote(query))
            feed = feedparser.parse(url)

            for entry in (feed.entries or [])[:5]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                link    = entry.get("link", "")
                pub     = entry.get("published", "")

                if not title or name not in title + summary:
                    continue

                # 判斷嚴重程度
                severity = _assess_severity(title + " " + summary)
                pub_date = _parse_date(pub)

                record = {
                    "title":       title[:200],
                    "description": summary[:500],
                    "event_type":  "controversy",
                    "category":    _classify_controversy(title + summary),
                    "severity":    severity,
                    "status":      "open",
                    "source_url":  link,
                    "source_name": _extract_source(title),
                    "source_date": pub_date,
                    "verified":    False,
                }

                # 先插 event
                ev_res = supabase.from_("events").insert(record).execute()
                if not ev_res.data:
                    continue

                event_id = ev_res.data[0]["id"]

                # 關聯政治人物
                supabase.from_("event_politicians").upsert({
                    "event_id":     event_id,
                    "politician_id": pid,
                }).execute()

                inserted += 1
                total += 1

            time.sleep(0.3)

        if inserted > 0:
            logger.info(f"  {name}: {inserted} 筆爭議事件")

    logger.success(f"爭議新聞收集完成，共 {total} 筆")
    return total


def collect_wikipedia_controversies(politicians: list[dict] | None = None):
    """從維基百科抓取爭議段落"""
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]

        # 取得完整 wiki 頁面 wikitext
        try:
            r = requests.get(WIKI_FULL, params={
                "action": "query",
                "titles": name,
                "prop": "revisions",
                "rvprop": "content",
                "format": "json",
                "formatversion": 2,
            }, timeout=15)
            pages = r.json().get("query", {}).get("pages", [])
            if not pages:
                continue
            content = pages[0].get("revisions", [{}])[0].get("content", "")
        except Exception as e:
            logger.warning(f"Wiki 取得失敗 {name}: {e}")
            continue

        if not content or "爭議" not in content and "批評" not in content:
            continue

        # 用 Claude Haiku 擷取爭議段落
        try:
            resp = claude.messages.create(
                model="claude-haiku-4-5",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": f"""以下是維基百科關於「{name}」的內容。
請擷取所有爭議、批評、醜聞、失言相關段落，每筆輸出 JSON 陣列：
[{{"title":"事件標題","description":"簡述","year":YYYY,"category":"爭議/失言/醜聞/貪腐"}}]
若無爭議，輸出空陣列 []。只輸出 JSON，不要其他文字。

內容：
{content[:3000]}"""
                }]
            )
            raw = resp.content[0].text.strip()
            # 清理 markdown
            raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            items = __import__("json").loads(raw)
        except Exception as e:
            logger.debug(f"Wiki AI 解析失敗 {name}: {e}")
            continue

        for item in (items or []):
            if not item.get("title") or not item.get("description"):
                continue

            ev_res = supabase.from_("events").insert({
                "title":       item["title"][:200],
                "description": item["description"][:500],
                "event_type":  "controversy",
                "category":    item.get("category", "爭議"),
                "severity":    3,
                "status":      "open",
                "source_name": "維基百科",
                "source_date": f"{item['year']}-01-01" if item.get("year") else None,
                "verified":    False,
            }).execute()

            if ev_res.data:
                event_id = ev_res.data[0]["id"]
                supabase.from_("event_politicians").upsert({
                    "event_id": event_id, "politician_id": pid
                }).execute()
                total += 1

        if items:
            logger.info(f"  {name}: {len(items)} 筆 Wiki 爭議")
        time.sleep(1)

    logger.success(f"維基爭議收集完成，共 {total} 筆")
    return total


def _assess_severity(text: str) -> int:
    """1-5 分嚴重程度"""
    high = ["起訴", "收賄", "貪腐", "性騷擾", "判決"]
    mid  = ["爭議", "失言", "醜聞", "下台", "辭職"]
    if any(w in text for w in high):
        return 5
    if any(w in text for w in mid):
        return 3
    return 2


def _classify_controversy(text: str) -> str:
    if any(w in text for w in ["貪腐", "收賄", "弊案", "起訴"]):
        return "貪腐"
    if any(w in text for w in ["失言", "言論", "被批", "炎上"]):
        return "失言"
    if any(w in text for w in ["性騷擾", "性侵"]):
        return "性騷擾"
    if any(w in text for w in ["醜聞", "緋聞"]):
        return "醜聞"
    return "爭議"


def _parse_date(pub: str) -> str | None:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(pub, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def _extract_source(title: str) -> str:
    media = ["聯合新聞網", "自由時報", "中時", "ETtoday", "TVBS",
             "三立", "民視", "公視", "風傳媒", "上報"]
    for m in media:
        if m in title:
            return m
    return "Google News"
