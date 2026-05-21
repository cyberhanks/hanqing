"""
立法院公報 / 議事文件 PDF 下載器
主要資料來源：data.ly.gov.tw Open Data API
備用來源：ppg.ly.gov.tw 公報網站
"""
import time
import random
import requests
from pathlib import Path
from loguru import logger
from bs4 import BeautifulSoup

DOWNLOAD_DIR = Path("data/gazettes")

# LY Open Data API — dataset id=4 為「委員發言」，含 pdfUrl
LY_OPENDATA_API = "https://data.ly.gov.tw/odw/openDatasetJson.action"

# 備用：直接從公報網站抓
GAZETTE_FALLBACK_URLS = [
    "https://ppg.ly.gov.tw/ppg/",
    "https://ppg.ly.gov.tw/ppg/PublicationLayout/publicationList",
]


def _fetch_via_opendata_api(limit: int = 10) -> list[dict]:
    """從 data.ly.gov.tw API 取得最近議事文件 PDF 連結"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Encoding": "identity",
        "Accept": "application/json",
    }
    # Dataset 4 = 委員發言（含 pdfUrl）；Dataset 6 = 質詢文件
    results = []
    for dataset_id in [4, 6]:
        try:
            r = requests.get(
                LY_OPENDATA_API,
                params={"id": dataset_id, "filterParam": "", "offset": 0, "limit": limit},
                headers=headers,
                timeout=20,
                verify=False,
            )
            r.raise_for_status()
            items = r.json().get("jsonList", [])
            for item in items:
                pdf_url = item.get("pdfUrl") or item.get("docUrl", "")
                if pdf_url and pdf_url.endswith(".pdf"):
                    results.append({
                        "url": pdf_url,
                        "dataset": dataset_id,
                        "term": item.get("term", ""),
                        "session": item.get("selectTerm", ""),
                    })
            logger.info(f"API dataset {dataset_id}: 取得 {len(items)} 筆，{sum(1 for i in items if i.get('pdfUrl'))} 個 PDF")
        except Exception as e:
            logger.warning(f"API dataset {dataset_id} 失敗：{e}")

    return results


def _fetch_via_scraping() -> list[dict]:
    """備用：從公報網站爬取 PDF 連結"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Encoding": "identity",
    }
    for base_url in GAZETTE_FALLBACK_URLS:
        try:
            resp = requests.get(base_url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select("a[href$='.pdf']")
            if links:
                logger.info(f"備用來源 {base_url}：找到 {len(links)} 個 PDF 連結")
                return [{"url": a.get("href", "")} for a in links[:10] if a.get("href")]
        except Exception as e:
            logger.warning(f"備用來源失敗：{base_url} — {e}")
    return []


def fetch_recent_gazettes(days: int = 7) -> list[dict]:
    """
    下載最近 N 天的立法院議事文件 PDF。
    優先使用 data.ly.gov.tw Open Data API，失敗時退回公報網站爬蟲。
    """
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"開始下載最近 {days} 天公報")

    # 1. 嘗試 Open Data API
    pdf_items = _fetch_via_opendata_api(limit=days * 2)

    # 2. 若 API 無結果，嘗試爬蟲
    if not pdf_items:
        logger.warning("Open Data API 無結果，嘗試備用爬蟲")
        pdf_items = _fetch_via_scraping()

    if not pdf_items:
        logger.error("所有來源均無法取得公報 PDF 連結")
        return []

    # 3. 下載 PDF 檔案
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    downloaded = []

    for item in pdf_items[:days * 2]:
        pdf_url = item.get("url", "")
        if not pdf_url:
            continue
        if not pdf_url.startswith("http"):
            pdf_url = "https://ppg.ly.gov.tw" + pdf_url

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
            if not pdf_resp.headers.get("Content-Type", "").startswith("application/pdf"):
                logger.warning(f"非 PDF 回應，跳過：{filename}")
                continue
            save_path.write_bytes(pdf_resp.content)
            size_kb = len(pdf_resp.content) // 1024
            downloaded.append({"filename": filename, "path": str(save_path), "url": pdf_url})
            logger.success(f"下載：{filename} ({size_kb} KB)")
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            logger.error(f"下載失敗：{filename} — {e}")

    logger.info(f"取得 {len(downloaded)} 份公報")
    return downloaded
