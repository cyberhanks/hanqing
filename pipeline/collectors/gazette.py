"""
立法院公報 PDF 下載器
來源：https://ppg.ly.gov.tw/ppg/
"""
import time
import random
import requests
from pathlib import Path
from loguru import logger
from bs4 import BeautifulSoup

# 立法院公報系統 - 多個備用入口（依優先順序）
GAZETTE_URLS = [
    "https://ppg.ly.gov.tw/ppg/PublicationLayout/publicationList",
    "https://ppg.ly.gov.tw/ppg/publications/download/list",
    "https://ppg.ly.gov.tw/ppg/",
    "https://lci.ly.gov.tw/LyLCEW/agenda1/02/pdf/",
]
DOWNLOAD_DIR = Path("data/gazettes")

# CSS selectors to try for PDF links on different page layouts
PDF_SELECTORS = [
    "a[href$='.pdf']",
    "a[href*='/pdf/']",
    "a[href*='PublicationLayout'][href*='pdf']",
    "table a[href]",
]


def fetch_recent_gazettes(days: int = 7) -> list[dict]:
    """下載最近 N 天的立法院公報 PDF，自動嘗試多個備用入口"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"開始下載最近 {days} 天公報")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "identity",
    }

    links_found = []

    for base_url in GAZETTE_URLS:
        logger.info(f"嘗試入口：{base_url}")
        try:
            resp = requests.get(base_url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Try each selector until we find PDF links
            for selector in PDF_SELECTORS:
                found = soup.select(selector)
                pdf_links = [a for a in found if a.get("href", "").endswith(".pdf")
                             or "/pdf/" in a.get("href", "")]
                if pdf_links:
                    logger.info(f"在 {base_url} 找到 {len(pdf_links)} 個 PDF 連結（selector: {selector}）")
                    links_found = pdf_links[:10]
                    break

            if links_found:
                break  # Stop trying fallback URLs once we have links

        except Exception as e:
            logger.warning(f"入口失敗：{base_url} — {e}")
            continue

    if not links_found:
        logger.error("所有入口均無法取得公報 PDF 連結")
        return []

    downloaded = []
    for link in links_found:
        pdf_url = link.get("href", "")
        if not pdf_url:
            continue
        if not pdf_url.startswith("http"):
            # Resolve relative URL
            base = "https://ppg.ly.gov.tw"
            pdf_url = base + ("" if pdf_url.startswith("/") else "/") + pdf_url

        filename = pdf_url.split("/")[-1].split("?")[0]
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        save_path = DOWNLOAD_DIR / filename

        if save_path.exists():
            logger.debug(f"已存在，跳過：{filename}")
            downloaded.append({"filename": filename, "path": str(save_path), "url": pdf_url})
            continue

        try:
            pdf_resp = requests.get(pdf_url, headers=headers, timeout=60, verify=False)
            pdf_resp.raise_for_status()
            save_path.write_bytes(pdf_resp.content)
            downloaded.append({"filename": filename, "path": str(save_path), "url": pdf_url})
            logger.success(f"下載：{filename} ({len(pdf_resp.content)//1024} KB)")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.error(f"下載失敗：{filename} — {e}")

    logger.info(f"取得 {len(downloaded)} 份公報")
    return downloaded
