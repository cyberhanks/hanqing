"""Phase 2 主程式：承諾擷取（公報 PDF → AI 分類 → 結構化寫入）"""
import sys
from loguru import logger
from collectors.gazette import fetch_recent_gazettes
from processors.ocr import pdf_to_text
from processors.classifier import classify_text
from processors.extractor import extract_promises
from processors.scorer import calculate_confidence, should_publish
from db.supabase_client import upsert_promise, get_politician_id

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | {level} | {message}")


def run():
    logger.info("Phase 2 開始：承諾擷取")
    gazettes = fetch_recent_gazettes(days=7)
    logger.info(f"取得 {len(gazettes)} 份公報")

    total_promises = 0
    for gazette in gazettes:
        logger.info(f"處理：{gazette['filename']}")
        text = pdf_to_text(gazette["path"])
        if not text:
            continue

        classified = classify_text(text)
        promise_chunks = [c for c in classified if c["type"] == "promise"]
        logger.info(f"找到 {len(promise_chunks)} 個承諾段落")

        for chunk in promise_chunks:
            politician_name = chunk.get("politician", "")
            if not politician_name:
                continue

            promises = extract_promises(
                text=chunk["text"],
                politician_name=politician_name,
                source_url=gazette["url"],
                source_name="立法院公報",
                topic=chunk.get("topic", "其他"),
            )

            for promise in promises:
                score = calculate_confidence(promise, source_type="gazette")
                promise["_confidence"] = score
                if not should_publish(score):
                    logger.warning(f"低信心分數（{score}），進入審核：{politician_name}")

                politician_id = get_politician_id(politician_name)
                if politician_id:
                    upsert_promise(promise, politician_id)
                    total_promises += 1
                else:
                    logger.warning(f"找不到政治人物：{politician_name}")

    logger.success(f"Phase 2 完成，共處理 {total_promises} 個承諾")


if __name__ == "__main__":
    run()
