"""
承諾核實加強版
- 對每個 active/unknown 狀態的承諾搜尋核實新聞
- 搜尋關鍵字：「{政治人物} {承諾摘要} (完成|落實|達成|跳票|食言)」
- 用 Claude Haiku 判斷狀態
- 更新 promises.status + evidence_title
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

VERIFY_PROMPT = """你是台灣政治分析師。

政治人物：{name}
承諾內容：{promise}

以下是搜尋到的相關新聞（可能不完整）：
{news}

請根據新聞內容判斷承諾狀態，輸出 JSON：
{{
  "status": "fulfilled/broken/active/unknown",
  "evidence": "判斷依據（引用具體新聞標題或事件，不超過80字）",
  "confidence": 0-100
}}

狀態定義：
- fulfilled: 新聞明確報導已完成/落實
- broken: 新聞明確報導跳票/食言/反向行動
- active: 仍在進行中
- unknown: 新聞不足以判斷

只輸出 JSON。"""


def verify_promises(limit: int = 200):
    """核實 active/unknown 狀態的承諾"""

    # 取待核實承諾（附政治人物名）
    res = supabase.from_("promises")\
        .select("id,summary,text,status,politician_id,politicians(name)")\
        .in_("status", ["active", "unknown"])\
        .limit(limit).execute()
    promises = res.data or []

    logger.info(f"待核實承諾：{len(promises)} 筆")
    updated = 0

    for p in promises:
        pol_name = (p.get("politicians") or {}).get("name", "")
        promise_text = p.get("summary") or p.get("text") or ""
        if not pol_name or not promise_text:
            continue

        # 取前幾個字當搜尋關鍵字
        kw = promise_text[:20].strip()
        for suffix in ["完成", "落實達成", "跳票食言"]:
            query = f"{pol_name} {kw} {suffix}"
            url   = NEWS_RSS.format(query=requests.utils.quote(query))
            feed  = feedparser.parse(url)

            snippets = []
            for entry in (feed.entries or [])[:4]:
                t = entry.get("title", "")
                s = entry.get("summary", "")
                if pol_name in t + s:
                    snippets.append(f"【{t}】{s[:100]}")

            if snippets:
                break

        if not snippets:
            continue

        news_text = "\n".join(snippets[:3])

        try:
            resp = claude.messages.create(
                model="claude-haiku-4-5",
                max_tokens=200,
                messages=[{"role": "user", "content":
                    VERIFY_PROMPT.format(
                        name=pol_name,
                        promise=promise_text[:150],
                        news=news_text,
                    )
                }]
            )
            raw = re.sub(r"```(?:json)?\s*|\s*```", "",
                         resp.content[0].text.strip())
            result = json.loads(raw)
        except Exception as e:
            logger.debug(f"解析失敗 {pol_name}: {e}")
            continue

        new_status = result.get("status", "unknown")
        confidence = int(result.get("confidence", 0))
        evidence   = result.get("evidence", "")

        # 只有高信心才更新
        if confidence >= 70 and new_status != p["status"]:
            supabase.from_("promises").update({
                "status":           new_status,
                "evidence_title":   evidence[:200],
                "verified_at":      "now()",
                "verification_hint": f"信心度 {confidence}%",
            }).eq("id", p["id"]).execute()

            logger.info(f"  [{pol_name}] {promise_text[:30]}… → {new_status} ({confidence}%)")
            updated += 1

        time.sleep(0.5)

    logger.success(f"承諾核實完成：{updated}/{len(promises)} 筆狀態更新")
    return updated
