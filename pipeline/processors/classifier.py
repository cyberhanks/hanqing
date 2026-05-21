"""內容分類器：將原始文字分類為承諾/發言/投票/爭議"""
import json
import anthropic
from pathlib import Path
from loguru import logger
from config import ANTHROPIC_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
CLASSIFY_PROMPT = Path("prompts/classify.txt").read_text(encoding="utf-8")


def classify_text(raw_text: str) -> list[dict]:
    if not raw_text or len(raw_text.strip()) < 20:
        return []
    chunks = split_into_chunks(raw_text, max_chars=3000)
    all_results = []
    for i, chunk in enumerate(chunks):
        logger.debug(f"分類第 {i+1}/{len(chunks)} 段")
        all_results.extend(_classify_chunk(chunk))
    return all_results


def _classify_chunk(text: str) -> list[dict]:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"{CLASSIFY_PROMPT}\n\n---\n\n{text}"}]
        )
        raw = response.content[0].text.strip()
        raw = raw.removeprefix("```json").removesuffix("```").strip()
        results = json.loads(raw)
        return [r for r in results if r.get("confidence", 0) >= 0.6]
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失敗：{e}")
        return []
    except Exception as e:
        logger.error(f"分類失敗：{e}")
        return []


def split_into_chunks(text: str, max_chars: int = 3000) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) > max_chars:
            if current:
                chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text[:max_chars]]
