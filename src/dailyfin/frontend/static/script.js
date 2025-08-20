let newsData = [];

// 各分類的圖示與顏色設定
const categoryConfig = {
  "AI相關":          { icon: "🤖",   color: "#D32F2F" },
  "人事變動":        { icon: "👥",   color: "#1976D2" },
  "客服創新":        { icon: "🎧",   color: "#388E3C" },
  "技術創新":        { icon: "💡",   color: "#0288D1" },
  "政策變動":        { icon: "🏛️",  color: "#512DA8" },
  "永續金融":        { icon: "🌱",   color: "#00796B" },
  "產業合作":        { icon: "🤝",   color: "#FFA000" },
  "股東會與股東權益":  { icon: "📊",   color: "#C2185B" },
  "行情相關":        { icon: "📈",   color: "#E64A19" },
  "電子支付":        { icon: "💳",   color: "#E65100" },
  "其他":            { icon: "🗂️",  color: "#616161" }
};
const defaultConfig = { icon: "📰", color: "#000" };

// 顯示（或更新）頁首日期
function displayCurrentDate() {
  const today = new Date();
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  document.getElementById('article-date').textContent =
    today.toLocaleDateString('zh-TW', options);
}

// 從後端取新聞資料，並渲染
async function fetchNews(date = null) {
  let url = "/api/news";
  if (date) url += `?date_filter=${date}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("資料載入失敗");
    newsData = await response.json();
    renderCategoryFilters();
    renderNewsList();
    if (newsData.length) displayNewsContent(newsData[0]);
    else {
      document.getElementById('article-title').textContent = "無新聞";
      document.getElementById('article-body').innerHTML = "";
    }
  } catch (error) {
    console.error("載入新聞失敗：", error);
    document.getElementById('article-title').textContent = "資料錯誤";
    document.getElementById('article-body').innerHTML =
      "<p>無法載入新聞資料，請稍後再試。</p>";
  }
}

// 動態渲染分類的 checkbox（含「全選」與筆數）
function renderCategoryFilters() {
  const container = document.getElementById('category-filters');
  container.innerHTML = "";

  // 統計各分類總數
  const counts = newsData.reduce((acc, item) => {
    const cat = item.category || '其他';
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});

  // 先加入「全選」checkbox
  const selectAllLabel = document.createElement('label');
  selectAllLabel.innerHTML = `
    <input type="checkbox" id="select-all" checked>
    <span>全選</span>
  `;
  container.appendChild(selectAllLabel);

  // 再加入各分類
  const categories = Object.keys(categoryConfig);
  if (!categories.includes('其他')) categories.push('其他');

  categories.forEach(cat => {
    const cfg = categoryConfig[cat] || defaultConfig;
    const count = counts[cat] || 0;
    const label = document.createElement('label');
    label.innerHTML = `
      <input type="checkbox" class="filter-checkbox" value="${cat}" checked>
      <span style="color: ${cfg.color}">
        ${cfg.icon} ${cat} <small>(${count})</small>
      </span>
    `;
    container.appendChild(label);
  });

  // 事件：點擊「全選」
  const selectAll = document.getElementById('select-all');
  selectAll.addEventListener('change', () => {
    const allCbs = container.querySelectorAll('.filter-checkbox');
    allCbs.forEach(cb => cb.checked = selectAll.checked);
    renderNewsList();
  });

  // 事件：點擊任一分類時，同步更新「全選」狀態
  container.addEventListener('change', e => {
    if (e.target.classList.contains('filter-checkbox')) {
      const allCbs = Array.from(container.querySelectorAll('.filter-checkbox'));
      const allChecked = allCbs.every(cb => cb.checked);
      selectAll.checked = allChecked;
      // 若完全不選，也保持 selectAll unchecked
      renderNewsList();
    }
  });
}

// 根據使用者勾選的分類來篩選、排序並顯示新聞標題
function renderNewsList() {
  const newsList = document.getElementById('news-titles');
  newsList.innerHTML = "";

  // 取出所有已勾選的分類
  const checkedCats = Array.from(
    document.querySelectorAll('.filter-checkbox')
  )
  .filter(cb => cb.checked)
  .map(cb => cb.value);

  // 過濾並排序
  const filtered = newsData
    .filter(item => checkedCats.includes(item.category || '其他'))
    .sort((a, b) =>
      (a.category || '其他').localeCompare(b.category || '其他', 'zh-TW')
    );

  // 建立清單
  filtered.forEach(news => {
    const cfg = categoryConfig[news.category] || defaultConfig;
    const badge = news.category
      ? `<span class="news-category" style="color: ${cfg.color}">
           ${cfg.icon} ${news.category}｜</span>`
      : "";

    const li = document.createElement('li');
    li.className = 'news-item';
    li.dataset.id = news.index;
    li.innerHTML = `
      <div class="news-title">${badge}${news.title}</div>
      <div class="news-source">${news.source} | ${news.date}</div>
    `;
    li.onclick = () => displayNewsContent(news);
    newsList.appendChild(li);
  });
}

// 點標題時顯示完整內文
function displayNewsContent(item) {
  document.getElementById('article-title').textContent = item.title;
  document.getElementById('article-date').textContent = item.date;
  const body = document.getElementById('article-body');
  body.innerHTML = `
    <p class="external-link">
      <a href="${item.link}" target="_blank" rel="noopener noreferrer">
        轉跳至原網站
      </a>
    </p>
    <p>GPT 分類說明 : ${item.aiSummary}</p>
  `;
  if (item.content && item.content.trim()) {
    item.content
      .split(/(?:。|\n)+/)
      .map(s => s.trim())
      .filter(s => s)
      .forEach(seg => {
        const p = document.createElement('p');
        p.textContent = seg;
        body.appendChild(p);
      });
  }
}

// 啟動流程：顯示日期、載入今天新聞、初始化 flatpickr
document.addEventListener('DOMContentLoaded', () => {
  displayCurrentDate();

  const today = new Date();
  const fmt = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;

  fetchNews(fmt);

  flatpickr("#date-select", {
    dateFormat: "Y-m-d",
    defaultDate: fmt,
    locale: "zh_tw",
    onChange: (d, str) => fetchNews(str)
  });
});
