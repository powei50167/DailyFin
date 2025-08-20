import os
import json
import asyncio
from openai import AsyncOpenAI


SYSTEM_PROMPT_NEWS_FILTER = """
    你是一個專業的《金融新聞篩選與分類模型》。
    任務：僅保留對金融期貨公司具有 **策略意義** 的新聞，並依下列規則填入函式參數：

    ◆ 【必保留】關鍵主題
    ‑ 技術創新、數位化計畫、監管／政策、AI 應用、永續金融、產業合作、電子支付、人事任命等。
    ◆ 【必忽略】非策略或純行銷內容
    ‑ 市場行銷活動、信用卡優惠、實體網點開幕、股價／指數漲跌、日常生活新聞等。

    ✦ 分類準則
    1. **category**：請置於下列枚舉；若無貼合項可用「其他」。
    2. **country**：
    - 「台灣」：內容與台灣市場、監理機關或本地金融機構直接相關。
    - 「國外」：其餘皆列為國外。
    3. **finance**：
    - 「是」：消息對銀行、券商、保險、金控或金融監管有實質影響。
    - 「不是」：其他情境。
    4. **Remarks**：簡述判斷依據（≤ 40字），並點出影響層面（產業／國家）。

    ⚠️ 回答形式：僅透過 function call `classify_news_headline` 回傳 JSON；不要輸出多餘文字。
"""

# GPT function schema 常數
FUNCTIONS = [
    {
        "name": "classify_news_headline",
        "description": "根據規則分類金融相關新聞標題",
        "parameters": {
            "type": "object",
            "properties": {
                "headline": {"type": "string", "description": "原始新聞標題，不可修改"},
                "category": {
                    "type": "string",
                    "enum": [
                        "人事變動","技術創新","產業合作","新功能",
                        "AI相關","永續金融","資料共享","客服創新",
                        "政策變動","行情相關","生活相關","科技相關",
                        "股東會與股東權益","個股、櫃買市場動態",
                        "電子支付","其他"
                    ],
                    "description": "新聞分類"
                },
                "country": {"type": "string", "enum": ["台灣","國外"], "description": "新聞是否與台灣相關"},
                "finance": {"type": "string", "enum": ["是","不是"], "description": "是否影響金融業"},
                "Remarks": {"type": "string", "description": "分類依據說明"},
                "link": {"type": "string", "description": "新聞連結"},
                "source": {"type": "string", "description": "發布平台"},
                "news_time": {"type": "string", "description": "發布時間"}
            },
            "required": [
                "headline","category","country","finance",
                "Remarks","link","source","news_time"
            ]
        }
    }
]

async def connect_gpt(
    news_dict: dict,
    concurrency: int = 5,
    model: str = "gpt-4o-mini"
) -> tuple[list[dict], list[dict]]:
    """
    非同步分類新聞標題；返回台灣與其他分類結果。

    Args:
      news_dict: {key: {title, link, source, news_time}, ...}
      concurrency: 最大併發數
      model: GPT 模型
    Returns:
      (TWNews, OtherNews)
    """
    client = AsyncOpenAI(
        organization=os.getenv("OPENAI_ORG"),
        api_key=os.getenv("OPENAI_KEY")
    )
    sem = asyncio.Semaphore(concurrency)
    TWNews: list[dict] = []
    OtherNews: list[dict] = []

    async def classify_one(key: str, article: dict) -> dict | None:
        async with sem:
            try:
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_NEWS_FILTER},
                    {"role": "user", "content": (
                        f"新聞標題：{article['title']}\n"
                        f"新聞連結：{article['link']}\n"
                        f"新聞來源：{article['source']}\n"
                        f"發布時間：{article['news_time']}"
                    )}
                ]
                resp = await client.chat.completions.create(
                    model=model,
                    temperature=1,
                    messages=messages,
                    functions=FUNCTIONS,
                    function_call={"name": "classify_news_headline"}
                )
                cls: dict = json.loads(
                    resp.choices[0].message.function_call.arguments
                )
                # 記錄原始鍵值以便追蹤
                cls["_key"] = key
                return cls
            except Exception as e:
                print(f"[ERROR] 分類失敗 ({key}): {e}")
                return None

    tasks = [asyncio.create_task(classify_one(k, v)) for k, v in news_dict.items()]
    results = await asyncio.gather(*tasks)

    for cls in results:
        if not cls:
            continue
        if cls.get("country") == "台灣" and cls.get("finance") == "是":
            TWNews.append(cls)
        elif cls.get("country") != "台灣" and cls.get("finance") == "是":
            OtherNews.append(cls)

    with open("tw_news.json", "w", encoding="utf-8") as f:
        json.dump(TWNews, f, ensure_ascii=False, indent=2)

    return TWNews, OtherNews
