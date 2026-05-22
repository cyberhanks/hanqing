"""
選舉政見 collector
來源 1：Google News 搜尋「{name} YYYY 選舉 政見」
來源 2：維基百科選舉段落
來源 3：中選會選舉公報 PDF（若有直連）

對每位政治人物搜尋其歷次選舉年份，
用 Claude Haiku 從新聞/公報中抽取政見承諾，
存入 election_pledges 表。
"""
import re
import time
import requests
import feedparser
from config import supabase, ANTHROPIC_KEY
from loguru import logger
import anthropic
import json

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

# 台灣主要選舉年份（立委+地方）
ELECTION_YEARS = [2004, 2008, 2012, 2016, 2020, 2024]

EXTRACT_PROMPT = """你是台灣政治分析師。以下是關於「{name}」在 {year} 年選舉的新聞摘要。

請擷取所有選舉政見或政策承諾，以 JSON 陣列格式回傳：
[
  {{"pledge":"政見內容","category":"政策分類（如：經濟/教育/環境/社福/交通/國防/司法/其他）"}}
]

要求：
- 只包含明確的政策主張或承諾，不包含攻擊對手的言論
- 每條政見獨立一筆
- 若無明確政見，回傳 []
- 只輸出 JSON，不加說明

新聞內容：
{content}"""


def _get_politicians() -> list[dict]:
    res = supabase.from_("politicians").select("id, name, party, role").execute()
    return res.data or []


def collect_election_pledges(politicians: list[dict] | None = None,
                              years: list[int] = ELECTION_YEARS):
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]
        inserted = 0

        for year in years:
            # Google News 搜尋
            query = f"{name} {year} 選舉 政見"
            url   = NEWS_RSS.format(query=requests.utils.quote(query))
            feed  = feedparser.parse(url)

            snippets = []
            for entry in (feed.entries or [])[:8]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                if name not in title + summary:
                    continue
                snippets.append(f"【{title}】{summary}")

            if not snippets:
                continue

            content = "\n".join(snippets[:5])

            # Claude Haiku 抽取
            try:
                resp = claude.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=600,
                    messages=[{"role": "user", "content":
                        EXTRACT_PROMPT.format(name=name, year=year, content=content)
                    }]
                )
                raw = resp.content[0].text.strip()
                raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
                pledges = json.loads(raw)
            except Exception as e:
                logger.debug(f"政見解析失敗 {name} {year}: {e}")
                continue

            if not pledges:
                continue

            records = []
            for p in pledges:
                text = (p.get("pledge") or "").strip()
                if not text or len(text) < 8:
                    continue
                records.append({
                    "politician_id":  pid,
                    "election_year":  year,
                    "election_type":  _infer_election_type(pol["role"]),
                    "pledge_text":    text[:500],
                    "category":       p.get("category", "其他"),
                    "source":         "Google News",
                })

            if records:
                supabase.from_("election_pledges").insert(records).execute()
                inserted += len(records)
                total += len(records)
                logger.info(f"  {name} {year}: {len(records)} 條政見")

            time.sleep(0.5)

        if inserted > 0:
            logger.success(f"{name}: 共 {inserted} 條歷史政見")

    logger.success(f"選舉政見收集完成，共 {total} 條")
    return total


def _infer_election_type(role: str) -> str:
    if "立委" in role or "委員" in role:
        return "立法委員"
    if "市長" in role:
        return "市長"
    if "縣長" in role:
        return "縣長"
    if "總統" in role:
        return "總統"
    return "立法委員"
