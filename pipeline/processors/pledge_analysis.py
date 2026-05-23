"""
選前政見 vs 立法行為 AI 交叉比對
- 取出每位政治人物的選舉政見 (election_pledges)
- 與其提案 (bills)、質詢 (statements)、投票 (votes) 交叉比對
- 用 Claude Sonnet 判斷政見是否有對應的立法行動
- 結果存入 pledge_analyses 表
- 更新 promises 的兌現狀態
"""
import re
import json
import time
from config import supabase, ANTHROPIC_KEY
from loguru import logger
import anthropic

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

ANALYSE_PROMPT = """你是台灣政治分析師，專門分析政治人物是否兌現選前政見。

政治人物：{name}（{party}）

【選前政見】
{pledges}

【實際立法行為】
提案法案：
{bills}

質詢/發言記錄：
{statements}

---
請對每條政見進行交叉分析，判斷是否有具體立法行動呼應。

輸出 JSON 陣列（每條政見一筆）：
[
  {{
    "pledge_index": 0,
    "fulfillment": "fulfilled/partial/broken/unknown",
    "evidence": "具體佐證說明（提及相關法案名稱或質詢內容）",
    "confidence": 0-100
  }}
]

判斷標準：
- fulfilled: 有明確相關法案通過或具體政策成果
- partial: 有提案或質詢但未通過/不完整
- broken: 言論或投票行為與政見明顯相反
- unknown: 找不到相關行動

只輸出 JSON，不加說明。"""


def _get_politicians() -> list[dict]:
    return supabase.from_("politicians").select("id,name,party").execute().data or []


def analyse_pledges(politicians: list[dict] | None = None):
    if politicians is None:
        politicians = _get_politicians()

    total = 0
    for pol in politicians:
        pid  = pol["id"]
        name = pol["name"]
        party = pol.get("party", "")

        # 取政見
        pledges_res = supabase.from_("election_pledges")\
            .select("id,pledge_text,category,election_year")\
            .eq("politician_id", pid).execute()
        pledges = pledges_res.data or []
        if not pledges:
            continue

        # 取提案
        bills_res = supabase.from_("bill_politicians")\
            .select("role,bills(title,status,bill_date)")\
            .eq("politician_id", pid).limit(20).execute()
        bills = bills_res.data or []

        # 取質詢/發言
        stmts_res = supabase.from_("statements")\
            .select("content,statement_type,statement_date")\
            .eq("politician_id", pid).limit(20).execute()
        stmts = stmts_res.data or []

        if not bills and not stmts:
            logger.debug(f"  {name}: 無立法行為資料，跳過")
            continue

        # 格式化
        pledges_text = "\n".join(
            f"{i}. [{p['election_year']}] {p['pledge_text'][:100]}"
            for i, p in enumerate(pledges)
        )
        bills_text = "\n".join(
            f"- [{b.get('role','')}] {(b.get('bills') or {}).get('title','')[:80]}"
            for b in bills if b.get("bills")
        ) or "（無提案記錄）"
        stmts_text = "\n".join(
            f"- {s.get('content','')[:80]}"
            for s in stmts
        ) or "（無質詢記錄）"

        try:
            resp = claude.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1500,
                messages=[{"role": "user", "content":
                    ANALYSE_PROMPT.format(
                        name=name, party=party,
                        pledges=pledges_text,
                        bills=bills_text,
                        statements=stmts_text,
                    )
                }]
            )
            raw = re.sub(r"```(?:json)?\s*|\s*```", "",
                         resp.content[0].text.strip())
            analyses = json.loads(raw)
        except Exception as e:
            logger.warning(f"  {name} AI 分析失敗: {e}")
            continue

        for a in analyses:
            idx = a.get("pledge_index", 0)
            if idx >= len(pledges):
                continue
            pledge = pledges[idx]

            supabase.from_("pledge_analyses").upsert({
                "politician_id": pid,
                "pledge_id":     pledge["id"],
                "fulfillment":   a.get("fulfillment", "unknown"),
                "evidence":      a.get("evidence", "")[:500],
                "confidence":    int(a.get("confidence", 50)),
                "analysis":      f"{pledge['pledge_text'][:100]} → {a.get('fulfillment')}",
            }, on_conflict="politician_id,pledge_id").execute()

            total += 1

        logger.info(f"  {name}: {len(analyses)} 條政見分析完成")
        time.sleep(2)  # Sonnet 較貴，慢一點

    logger.success(f"政見分析完成，共 {total} 筆")
    return total
