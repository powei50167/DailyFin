import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv

from dailyfin.crawler.news_collector import load_search_target
from dailyfin.crawler.news_gpt_generate import connect_gpt
from dailyfin.crawler.news_saver import save_articles


def parse_args():
    parser = argparse.ArgumentParser(
        description="新聞擷取、分類與存檔主程式"
    )
    parser.add_argument(
        "--mode", choices=["classify", "save", "all"], default="all",
        help="執行模式：classify=僅分類; save=僅存檔; all=分類後存檔"
    )
    parser.add_argument(
        "--targets", default="search_targets.xlsx",
        help="搜尋關鍵詞 Excel 檔案路徑"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    load_dotenv()

    try:
        # 1. 擷取新聞並建立 news_dict
        news_dict = load_search_target(args.targets)
        print(f"[INFO] 擷取到 {len(news_dict)} 組關鍵詞新聞候選項")

        tw_news = other_news = []
        # 2. 分類
        if args.mode in ("classify", "all"):
            tw_news, other_news = await connect_gpt(news_dict)
            print(f"[INFO] GPT 分類完成：台灣新聞 {len(tw_news)} 筆，其他 {len(other_news)} 筆")

        # 3. 抓取內文
        if args.mode in ("save", "all"):
            if not tw_news:
                print("[WARN] 無台灣新聞可存檔，跳過存檔階段")
            else:
                await save_articles(tw_news)
                print(f"[INFO] 已成功存檔 {len(tw_news)} 筆新聞內文至資料庫")

    except Exception as e:
        print(f"[ERROR] 主程式執行失敗：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())