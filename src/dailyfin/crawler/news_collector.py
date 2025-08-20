from datetime import datetime, timedelta
from openpyxl import load_workbook
from bs4 import BeautifulSoup
import requests



def append_news(search_target, news_dict):
    now = datetime.now()
    filterday = '2' if now.weekday() == 0 else '1'
    url = f'https://news.google.com/search?q={search_target}%20when%3A{filterday}d&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant'
    response = requests.get(url)
    if response.status_code != 200:
        print(f"{search_target}_HTTP請求失敗：{response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    base_url = 'https://news.google.com'
    time_delta = timedelta(hours=72 if now.weekday() == 0 else 24)

    # 1. 先用 news_dict 裡的 value 建立已存在標題的集合
    existing_titles = {item['title'] for item in news_dict.values()}

    news_id = 0
    for item in soup.find_all('article', class_='IFHyqb'):
        link_tag = item.find('a', class_='WwrzSb')
        if not link_tag:
            continue

        full_link = base_url + link_tag['href'].lstrip('.')
        title_tag = item.find('a', class_='JtKRv')
        title = title_tag.text if title_tag else "No title"

        # 2. 若標題已存在就跳過
        if title in existing_titles:
            continue

        source = item.find("div", class_="vr1PYe").text.strip() if item.find("div", class_="vr1PYe") else "No source"
        time_tag = item.find('time', class_='hvbAAd')
        news_time = time_tag['datetime'] if time_tag else "No time"

        if news_time != "No time":
            utc_time = datetime.strptime(news_time, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)
            if now - utc_time <= time_delta:
                # 3. 加入 news_dict 並同時更新 existing_titles
                news_dict[f'{search_target}_{news_id}'] = {
                    'title': title,
                    'link': full_link,
                    'news_time': utc_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': source
                }
                existing_titles.add(title)
                news_id += 1


def load_search_target(file_path: str) -> dict:
    news_dict = {}
    workbook = load_workbook(file_path)
    sheet = workbook.active
    for row in sheet.iter_rows(min_row=2, values_only=True):
        for search_target in row:
            if search_target:
                append_news(search_target.strip(), news_dict)
    print(f'新聞讀取完成,新聞總量 : {len(news_dict)}')
    return news_dict

