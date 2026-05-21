"""承諾擷取器：從分類為「承諾」的文字中擷取結構化資訊"""
import json
import anthropic
from pathlib import Path
from loguru import logger
from config import ANTHROPIC_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
EXTRACT_PROMPT = Path("prompts/extract.txt").read_text(encoding="utf-8")


def extract_promises(
    text: str,
    politician_name: str,
    source_url: str = "",
    source_name: str = "",
    source_date: str = "",
    topic: str = "其他",
) -> list[dict]:
    if not text:
        return []
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": (
                f"{EXTRACT_PROMPT}\n\n"
                f"發言者：{politician_name}\n"
                f"來源：{source_name}（{source_date}）\n\n"
                f"---\n\n{text}"
            )}]
        )
        raw = response.content[0].text.strip()
        raw = raw.removeprefix("```json").removesuffix("```").strip()
        promises_raw = json.loads(raw)

        promises = []
        for p in promises_raw:
            promise = {
                "promise_text":       p.get("promise_text", ""),
                "summary":            p.get("promise_summary", ""),
                "topic":              topic,
                "deadline":           p.get("deadline"),
                "scope":              p.get("scope"),
                "verifiable":         p.get("verifiable", True),
                "verification_hint":  p.get("verification_hint", ""),
                "keywords":           p.get("keywords", []),
                "status":             "active",
                "source_url":         source_url,
                "source_name":        source_name,
                "source_date":        source_date,
                "politician_name":    politician_name,
                "verified_by":        "ai",
            }
            if promise["promise_text"]:
                promises.append(promise)

        logger.success(f"擷取 {len(promises)} 個承諾 from {politician_name}")
        return promises
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失敗：{e}")
        return []
    except Exception as e:
        logger.error(f"承諾擷取失敗：{e}")
        return []
