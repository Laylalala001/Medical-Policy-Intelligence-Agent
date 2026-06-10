# -*- coding: utf-8 -*-
import re
import time
import random
import psycopg2
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions

# ========== 配置 ==========
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = "" #your_password_here
DB_HOST = "localhost"
DB_PORT = 5432

LIST_URL = "https://www.nmpa.gov.cn/xxgk/fgwj/index.html"
FEISHU_WEBHOOK = "" #your_webhook_key

MIN_DELAY = 2
MAX_DELAY = 5
MAX_RETRIES = 3
# ==========================

# ========== 加权关键词库（不变）==========
KEYWORDS_WEIGHTED = {
    "医疗器械": {
        "医疗器械": 10, "体外诊断": 8, "医用耗材": 8, "植入": 7, "导管": 6, "支架": 8, "起搏器": 9,
        "隐形眼镜": 9, "角膜接触镜": 9, "美瞳": 9, "X射线": 6, "CT": 6, "MRI": 6, "超声": 5,
        "呼吸机": 8, "麻醉机": 7, "手术器械": 7, "缝合线": 6, "敷料": 5, "人工晶体": 8,
        "假体": 7, "轮椅": 5, "助听器": 6, "医用口罩": 7, "防护服": 7, "检测试剂盒": 8,
        "采血管": 4, "注射器": 4, "输液器": 4, "避孕套": 9, "早孕试纸": 9
    },
    "药品": {
        "药品": 10, "药物": 9, "生物制品": 8, "疫苗": 9, "血清": 7, "抗生素": 7, "中成药": 7,
        "化学药品": 8, "原料药": 6, "辅料": 5, "制剂": 6, "处方": 5, "非处方": 5,
        "临床试验": 9, "仿制药": 8, "创新药": 9, "靶向药": 8, "中药饮片": 6,
        "颗粒剂": 4, "片剂": 4, "胶囊": 4, "注射液": 5, "口服液": 4, "软膏": 4
    },
    "化妆品": {
        "化妆品": 10, "护肤": 6, "彩妆": 7, "香水": 5, "染发": 8, "烫发": 8, "祛斑": 7,
        "防晒": 6, "美白": 7, "保湿": 5, "洁面": 4, "爽肤水": 4, "乳液": 4,
        "面霜": 5, "精华": 6, "眼霜": 5, "口红": 7, "眼影": 6, "粉底": 6,
        "腮红": 5, "指甲油": 6, "洗发": 4, "护发": 4, "沐浴": 4,
        "牙膏": 8, "漱口水": 8, "牙贴": 8
    }
}
SPECIAL_RULES = [
    (re.compile(r"隐形眼镜|角膜接触镜|美瞳", re.I), "医疗器械"),
    (re.compile(r"牙膏|漱口水|牙贴", re.I), "化妆品"),
    (re.compile(r"避孕套|早孕试纸", re.I), "医疗器械"),
]

def ai_classify(text):
    try:
        prompt = f"""仅输出一个类别词（药品/医疗器械/化妆品/其他），不要解释。
标题和内容：{text[:500]}
类别："""
        resp = requests.post("http://localhost:11434/api/generate", json={
            "model": "qwen2:7b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        }, timeout=15)
        if resp.status_code == 200:
            result = resp.json()["response"].strip()
            if result in ["药品", "医疗器械", "化妆品", "其他"]:
                return result
    except Exception as e:
        print(f"⚠️ AI 分类失败: {e}")
    return None

def classify_by_text(text):
    text_lower = text.lower()
    for pattern, cat in SPECIAL_RULES:
        if pattern.search(text_lower):
            return cat
    scores = {"医疗器械": 0, "药品": 0, "化妆品": 0}
    for cat, kw_dict in KEYWORDS_WEIGHTED.items():
        for kw, weight in kw_dict.items():
            count = text_lower.count(kw.lower())
            if count:
                scores[cat] += count * weight
    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]
    if best_score < 5:
        ai_cat = ai_classify(text)
        if ai_cat:
            return ai_cat
    return best_cat if best_score > 0 else "其他"

def get_db_conn():
    return psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def ensure_columns():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='nmpa_announcements' AND column_name='content') THEN
                ALTER TABLE nmpa_announcements ADD COLUMN content TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='nmpa_announcements' AND column_name='summary') THEN
                ALTER TABLE nmpa_announcements ADD COLUMN summary TEXT;
            END IF;
        END $$;
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_announcement(title, url, pub_date, doc_num, category):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO nmpa_announcements (title, url, publish_date, document_number, category)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (title, url, pub_date, doc_num, category))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"数据库错误: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def update_content_summary(url, content, summary):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE nmpa_announcements SET content=%s, summary=%s WHERE url=%s",
                (content, summary, url))
    conn.commit()
    cur.close()
    conn.close()

def fetch_page_content(url):
    for attempt in range(MAX_RETRIES):
        try:
            co = ChromiumOptions()
            co.set_argument('--disable-blink-features=AutomationControlled')
            page = ChromiumPage(addr_or_opts=co)
            page.get(url)
            time.sleep(random.uniform(2, 4))
            html = page.html
            page.close()
            if html and len(html) > 500:
                return html
        except Exception as e:
            print(f"  抓取失败 {attempt+1}/{MAX_RETRIES}: {e}")
        time.sleep(random.uniform(3, 6))
    return None

def extract_main_text(html):
    """
    从 NMPA 页面 HTML 中提取正文内容。
    优先使用 .text 容器，备用其他常见选择器。
    """
    soup = BeautifulSoup(html, "lxml")
    selectors = [
        ".text",                 # NMPA 当前页面实际使用的正文容器
        ".content",              # 常见正文容器
        "#Content",              # 旧版常见正文容器
        ".article-content",      # 其他可能容器
        ".TRS_Editor",           # 政府网站常用容器
        ".con"                   # 通用容器
    ]
    for selector in selectors:
        content_div = soup.select_one(selector)
        if content_div:
            for tag in content_div(["script", "style"]):
                tag.decompose()
            text = content_div.get_text(separator="\n")
            text = re.sub(r"\n\s*\n", "\n", text)
            return text.strip()
    return None

def generate_summary(title, content):
    if not content:
        return "（正文无法获取）"
    truncated = content[:1500]
    prompt = f"""你是医药政策分析专家。根据标题和正文，用一句话（40字以内）概括该政策的核心要点或对企业的影响。
标题：{title}
正文片段：
{truncated}
一句话摘要："""
    try:
        resp = requests.post("http://localhost:11434/api/generate", json={
            "model": "qwen2:7b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 80}
        }, timeout=30)
        if resp.status_code == 200:
            summary = resp.json()["response"].strip()
            if len(summary) > 100 or not summary:
                return title[:40] + "..."
            return summary
        else:
            return "（摘要生成失败）"
    except Exception as e:
        print(f"⚠️ AI 摘要失败: {e}")
        return "（摘要生成失败）"

def process_new_announcement(item):
    url = item['url']
    print(f"  📄 抓取正文: {url[:80]}...")
    html = fetch_page_content(url)
    if not html:
        print(f"  ❌ 正文抓取失败")
        # 避免重复尝试：写入失败标记
        update_content_summary(url, "", "（正文抓取失败）")
        return
    content = extract_main_text(html)
    if not content:
        print(f"  ⚠️ 未提取到正文内容")
        update_content_summary(url, "", "（正文提取失败）")
        return
    summary = generate_summary(item['title'], content)
    print(f"  📝 摘要: {summary[:60]}...")
    update_content_summary(url, content, summary)

def send_feishu(title_text, items):
    if not items:
        return
    content_lines = []
    for idx, (item_title, item_url) in enumerate(items, 1):
        line = [
            {"tag": "text", "text": f"{idx}. "},
            {"tag": "a", "text": item_title, "href": item_url},
            {"tag": "text", "text": "\n"}
        ]
        content_lines.append(line)
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title_text,
                    "content": content_lines
                }
            }
        }
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ 飞书推送成功")
        else:
            print(f"❌ 飞书推送失败: {resp.text}")
    except Exception as e:
        print(f"❌ 飞书推送异常: {e}")

def extract_list_items(page):
    soup = BeautifulSoup(page.html, "lxml")
    items = []
    for li in soup.select("ul.list li, .news-list li, .list li"):
        a = li.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue
        if href.startswith("/"):
            url = "https://www.nmpa.gov.cn" + href
        elif href.startswith("../"):
            clean_href = href.lstrip("../")
            url = "https://www.nmpa.gov.cn/" + clean_href
        else:
            url = href
        date_text = li.get_text()
        date_match = re.search(r"(\d{4}[./-]\d{1,2}[./-]\d{1,2})", date_text)
        pub_date = None
        if date_match:
            try:
                pub_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
            except:
                try:
                    pub_date = datetime.strptime(date_match.group(1), "%Y.%m.%d").date()
                except:
                    pass
        doc_match = re.search(r"(\d{4}年[第\s]*\d+号)", title + " " + date_text)
        doc_num = doc_match.group(1) if doc_match else None
        items.append({
            "title": title,
            "url": url,
            "pub_date": pub_date,
            "doc_num": doc_num
        })
    return items

def get_page_with_retry(page, url):
    for attempt in range(MAX_RETRIES):
        try:
            page.get(url)
            page.wait.ele_displayed("ul.list", timeout=10)
            return True
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次访问失败: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(2, 5))
            else:
                return False
    return False

def main():
    print("🚀 启动 NMPA 公告采集（只处理新增，正文+AI摘要）")
    ensure_columns()

    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    page = ChromiumPage(addr_or_opts=co)

    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    if not get_page_with_retry(page, LIST_URL):
        page.close()
        return

    items = extract_list_items(page)
    print(f"📄 从列表页提取到 {len(items)} 条公告")

    new_count = 0
    new_announcements = []
    for item in items:
        text_for_classify = f"{item['title']} {item['doc_num'] or ''}"
        category = classify_by_text(text_for_classify)
        inserted = insert_announcement(
            item['title'], item['url'], item['pub_date'],
            item['doc_num'], category
        )
        if inserted:
            new_count += 1
            new_announcements.append((item['title'][:60], item['url']))
            print(f"  ✅ 新增: {item['title'][:40]}... [{category}]")
            process_new_announcement(item)
            time.sleep(random.uniform(3, 6))

    if new_count > 0:
        today = datetime.now().strftime("%Y-%m-%d")
        title_text = f"📢 NMPA 今日新增 {new_count} 条公告（{today}）"
        send_feishu(title_text, new_announcements)
    else:
        print("ℹ️ 没有新增公告")

    page.close()
    print("✅ 采集完成")

if __name__ == "__main__":
    main()