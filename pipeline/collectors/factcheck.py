"""
事實查核 collector
來源：台灣事實查核中心 (factcheck.tw) — 透過 Google News RSS 搜尋
存入 factchecks 表，並更新 politicians.factcheck_count / factcheck_false_count
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

# Google News 搜尋 factcheck.tw 的結果
FACTCHECK_RSS = "https://news.google.com/rss/search?q={name}+site:factcheck.tw&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
FACTCHECK_DIRECT = "https://factcheck.tw/search/?q={name}"

VERDICT_MAP = {
    "正確":    "true",
    "大致正確": "mostly-true",
    "部分正確": "partly-true",
    "待查":    "unverified",
    "錯誤":    "false",
    "錯誤訊息": "false",
    "誤導":    "misleading",
    "查無此事": "false",
}

CLASSIFY_PROMPT = """你是事實查核分析師。以下是關於「{name}」的一篇查核報導標題與摘要。

請分析並輸出 JSON：
{{
  "claim": "被查核的具體言論（30字內）",
  "verdict": "正確/部分正確/錯誤/誤導/待查",
  "summary": "查核結論一句話"
}}

若這篇文章與 {name} 無關，輸出 {{"skip": true}}。
只輸出 JSON。

標題：{title}
摘要：{summary}"""


def _get_politicians() -> list[dict]:
    return supabase.from_("politicians").select("id,name").execute().data or []


def collect_factchecks(politicians: list[dict] | None = None):
    if politicians is None:
        politicians = _get_politicians()

    total_checks = 0
    total_false  = 0

    for pol in politicians:
        name = pol["name"]
        pid  = pol["id"]
        inserted = 0
        false_cnt = 0

        # Google News 搜尋 factcheck.tw
        url  = FACTCHECK_RSS.format(name=requests.utils.quote(name))
        feed = feedparser.parse(url)

        for entry in (feed.entries or [])[:10]:
            title   = entry.get("title", "")
            summary = entry.get("summary", "")
            link    = entry.get("link", "")
            pub     = entry.get("published", "")

            if "factcheck.tw" not in link and "factcheck" not in title.lower():
                continue

            # Claude 分析
            try:
                resp = claude.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=200,
                    messages=[{"role": "user", "content":
                        CLASSIFY_PROMPT.format(
                            name=name, title=title, summary=summary
                        )
                    }]
                )
                raw = re.sub(r"```(?:json)?\s*|\s*```", "",
                             resp.content[0].text.strip())
                result = json.loads(raw)
            except Exception:
                continue

            if result.get("skip"):
                continue

            verdict    = result.get("verdict", "待查")
            verdict_en = VERDICT_MAP.get(verdict, "unverified")

            supabase.from_("factchecks").insert({
                "politician_id": pid,
                "claim":         result.get("claim", title[:100]),
                "verdict":       verdict,
                "verdict_en":    verdict_en,
                "source_name":   "台灣事實查核中心",
                "source_url":    link,
                "check_date":    _parse_date(pub),
                "summary":       result.get("summary", ""),
            }).execute()

            inserted += 1
            if verdict_en in ("false", "misleading"):
                false_cnt += 1

            time.sleep(0.3)

        if inserted > 0:
            # 更新統計
            existing = supabase.from_("politicians")\
                .select("factcheck_count,factcheck_false_count")\
                .eq("id", pid).single().execute().data or {}
            supabase.from_("politicians").update({
                "factcheck_count":       (existing.get("factcheck_count") or 0) + inserted,
                "factcheck_false_count": (existing.get("factcheck_false_count") or 0) + false_cnt,
            }).eq("id", pid).execute()

            logger.info(f"  {name}: {inserted} 筆查核（{false_cnt} 筆錯誤/誤導）")
            total_checks += inserted
            total_false  += false_cnt

        time.sleep(0.5)

    logger.success(f"事實查核完成：{total_checks} 筆，其中 {total_false} 筆錯誤/誤導")
    return total_checks


def _parse_date(pub: str) -> str | None:
    from datetime import datetime
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(pub, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None
