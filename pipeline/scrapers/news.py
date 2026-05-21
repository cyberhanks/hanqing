"""
新聞爬蟲：用於承諾核實
使用 Playwright 抓取公開新聞內容
"""
import asyncio
from playwright.async_api import async_playwright

async def scrape_article(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        title = await page.title()
        body = await page.inner_text("article, main, .article-content, .content") \
            if await page.query_selector("article, main, .article-content, .content") \
            else await page.inner_text("body")

        await browser.close()
        return {"url": url, "title": title, "content": body[:5000]}

if __name__ == "__main__":
    result = asyncio.run(scrape_article("https://news.ltn.com.tw/"))
    print(result["title"])
