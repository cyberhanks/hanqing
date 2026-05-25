"""
選舉得票率歷史 collector
來源：中選會開放資料 + Google News 搜尋
存入 election_results 表，計算得票率趨勢
"""
import re
import json
import time
import requests
import feedparser
from config import supabase, ANTHROPIC_KEY
from loguru import logger
import anthropic

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
CEC_API  = "https://db.cec.gov.tw/ElecTable/Election"   # 中選會資料庫（需實際確認 endpoint）

ELECTIONS = [2004, 2008, 2012, 2016, 2020, 2024]

EXTRACT_PROMPT = """以下是關於「{name}」在 {year} 年選舉的新聞。
請提取得票資訊，輸出 JSON（若找不到明確數字輸出 null）：
{{
  "vote_count": 得票數(整數),
  "vote_share": 得票率(小數，如0.523表示52.3%),
  "result": "elected 或 lost",
  "constituency": "選區名稱"
}}
只輸出 JSON 或 null。

新聞：{content}"""


def _get_politicians() -> list[dict]:
    return supabase.from_("politicians")\
        .select("id,name,party,role,region").execute().data or []


def collect_election_results(politicians: list[dict] | None = None):
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]
        results_by_year = []

        for year in ELECTIONS:
            query = f"{name} {year} 選舉 得票"
            url   = NEWS_RSS.format(query=requests.utils.quote(query))
            feed  = feedparser.parse(url)

            snippets = []
            for entry in (feed.entries or [])[:5]:
                t = entry.get("title", "")
                s = entry.get("summary", "")
                if name in t + s:
                    snippets.append(f"【{t}】{s[:100]}")

            if not snippets:
                time.sleep(0.2)
                continue

            try:
                resp = claude.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=200,
                    messages=[{"role": "user", "content":
                        EXTRACT_PROMPT.format(
                            name=name, year=year,
                            content="\n".join(snippets[:3])
                        )
                    }]
                )
                raw = re.sub(r"```(?:json)?\s*|\s*```", "",
                             resp.content[0].text.strip())
                result = json.loads(raw)
            except Exception:
                time.sleep(0.3)
                continue

            if not result or result == "null":
                time.sleep(0.3)
                continue

            vote_share = result.get("vote_share")
            if not vote_share:
                time.sleep(0.3)
                continue

            # 轉換：若已是百分比格式則除以100
            if isinstance(vote_share, float) and vote_share > 1:
                vote_share = vote_share / 100

            record = {
                "politician_id": pid,
                "election_year": year,
                "election_type": "立法委員",
                "constituency":  result.get("constituency") or pol.get("region", ""),
                "vote_count":    result.get("vote_count"),
                "vote_share":    round(float(vote_share) * 100, 2),
                "result":        result.get("result", "unknown"),
            }

            try:
                supabase.from_("election_results").upsert(
                    record, on_conflict="politician_id,election_year,election_type"
                ).execute()
                results_by_year.append((year, float(vote_share) * 100))
                total += 1
                logger.info(f"  {name} {year}: {record['vote_share']}% ({record['result']})")
            except Exception as e:
                logger.debug(f"  {name} {year} 寫入失敗: {e}")

            time.sleep(0.5)

        # 計算趨勢（最新兩次相差）
        if len(results_by_year) >= 2:
            results_by_year.sort()
            trend = results_by_year[-1][1] - results_by_year[-2][1]
            latest = results_by_year[-1][1]
            supabase.from_("politicians").update({
                "vote_share_latest": round(latest, 2),
                "vote_share_trend":  round(trend, 2),
            }).eq("id", pid).execute()

    logger.success(f"選舉得票率收集完成：{total} 筆")
    return total
