from playwright.async_api import async_playwright
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from dailyfin.core.connection import SessionLocal
from dailyfin.backend.models import NewsArticle
import asyncio
from sqlalchemy import text


async def fetch_article_content(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            print(f"開始抓取內文{url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(2000)
            if "sorry" in page.url or "驗證" in await page.title():
                print("⚠️ 被 CAPTCHA 擋下")
                return ""
            paragraphs = await page.locator("p").all_inner_texts()
            return "\n".join(paragraphs)
        except Exception as e:
            print(f"❌ 內文抓取錯誤：{e}")
            return ""
        finally:
            await browser.close()

async def save_articles(news_list):
    today = datetime.now().strftime('%Y-%m-%d')
    db = SessionLocal()

    # 篩選出要抓內文的文章
    filtered_articles = [
        article for article in news_list
        if article['source'] != '奇摩新聞' and article['finance'] == '是'
    ]

    # 批次抓取內文
    tasks = [fetch_article_content(article['link']) for article in filtered_articles]
    contents = await asyncio.gather(*tasks)

    try:
        # 查詢今日目前最大 id
        result = db.execute(
            text("SELECT MAX(id) FROM news_list WHERE input_date = :today"),
            {"today": today}
        ).fetchone()
        current_max_id = result[0] if result[0] is not None else 0

        for idx, content in enumerate(contents):
            article = filtered_articles[idx]
            daily_id = current_max_id + idx + 1  # 每筆遞增

            stmt = text("""
                INSERT IGNORE INTO news_list
                (input_date, id, title, link, content, source, date, category, finance, country, aiSummary)
                VALUES
                (:input_date, :id, :title, :link, :content, :source, :date, :category, :finance, :country, :aiSummary)
            """)

            db.execute(stmt, {
                "input_date": today,
                "id": daily_id,
                "title": article['headline'],
                "link": article['link'],
                "content": content,
                "source": article['source'],
                "date": article['news_time'],
                "category": article['category'],
                "finance": article['finance'],
                "country": article['country'],
                "aiSummary": article['Remarks']
            })

            print(f"✅ 新增或跳過（ID:{daily_id}）：{article['headline']}")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ 發生錯誤：{e}")
    finally:
        db.close()
