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

GAZETTE_INDEX = "https://ppg.ly.gov.tw/ppg/PublicationLayout/publicationList"
DOWNLOAD_DIR = Path("data/gazettes")


def fetch_recent_gazettes(days: int = 7) -> list[dict]:
    """下載最近 N 天的立法院公報 PDF"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"開始下載最近 {days} 天公報")

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(GAZETTE_INDEX, headers=headers, timeout=30, verify=False)
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.error(f"公報首頁取得失敗：{e}")
        return []

    downloaded = []
    links = soup.select("a[href$='.pdf']")[:10]

    for link in links:
        pdf_url = link.get("href", "")
        if not pdf_url.startswith("http"):
            pdf_url = "https://ppg.ly.gov.tw" + pdf_url

        filename = pdf_url.split("/")[-1]
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
            logger.success(f"下載：{filename}")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.error(f"下載失敗：{filename} — {e}")

    return downloaded
