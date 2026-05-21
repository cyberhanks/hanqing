"""
PDF 轉文字
優先 PyMuPDF 直接提取，失敗才用 Claude Vision
"""
import base64
from pathlib import Path
from loguru import logger
from config import ANTHROPIC_KEY


def pdf_to_text(pdf_path: str) -> str:
    path = Path(pdf_path)
    logger.info(f"處理 PDF：{path.name}")

    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        if len(text.strip()) > 100:
            logger.debug("直接文字提取成功")
            return text.strip()
    except Exception as e:
        logger.warning(f"直接提取失敗：{e}")

    return pdf_to_text_via_vision(pdf_path)


def pdf_to_text_via_vision(pdf_path: str) -> str:
    import anthropic
    import fitz

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num in range(min(len(doc), 20)):
        page = doc[page_num]
        img_b64 = base64.standard_b64encode(
            page.get_pixmap(dpi=150).tobytes("png")
        ).decode()

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/png", "data": img_b64
                    }},
                    {"type": "text", "text": (
                        "這是台灣立法院公報的掃描頁面。"
                        "請完整擷取所有文字內容，保留段落結構，"
                        "包含發言人姓名、發言內容、表決結果。"
                        "只回傳純文字，不要任何說明。"
                    )}
                ]}]
            )
            all_text.append(f"=== 第 {page_num+1} 頁 ===\n{response.content[0].text}")
        except Exception as e:
            logger.error(f"第 {page_num+1} 頁 Vision 失敗：{e}")

    doc.close()
    return "\n\n".join(all_text)
