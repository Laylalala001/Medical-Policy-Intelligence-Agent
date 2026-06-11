# -*- coding: utf-8 -*-
import re
import time
import random
import psycopg2
import requests
import sys
import os
import logging

from dotenv import load_dotenv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions

load_dotenv()

logging.basicConfig(
    filename="crawler.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# ========== 全局函数定义 ==========
def normalize_url(href):
    if href.startswith("http"):
        return href
    if href.startswith("../../"):
        href = href.lstrip("../../")
        return "https://www.nmpa.gov.cn/" + href
    elif href.startswith("../"):
        href = href.lstrip("../")
        return "https://www.nmpa.gov.cn/" + href
    elif href.startswith("/"):
        return "https://www.nmpa.gov.cn" + href
    else:
        return "https://www.nmpa.gov.cn/" + href.lstrip("./")

def extract_date(text):
    match = re.search(r"(\d{4}[./-]\d{1,2}[./-]\d{1,2})", text)
    if match:
        date_str = match.group(1)
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
    return None

def extract_doc_num(title, date_text):
    match = re.search(r"(\d{4}年[第\s]*\d+号)", title + " " + date_text)
    return match.group(1) if match else None

def parse_fgwj_list(page):
    """法规文件专用解析"""
    soup = BeautifulSoup(page.html, "lxml")
    items = []
    for li in soup.find_all("li"):
        a = li.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue
        date_span = li.find("span")
        date_text = date_span.get_text(strip=True) if date_span else li.get_text()
        pub_date = extract_date(date_text)
        if pub_date is None:
            continue
        url = normalize_url(href)
        doc_num = extract_doc_num(title, date_text)
        items.append({
            "title": title,
            "url": url,
            "pub_date": pub_date,
            "doc_num": doc_num
        })
    return items

def parse_ypjgyw_list(page):
    """药监动态专用解析"""
    soup = BeautifulSoup(page.html, "lxml")
    items = []
    for li in soup.find_all("li"):
        a_tag = li.find("a")
        span_tag = li.find("span")
        if a_tag and span_tag:
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href")
            if not href or not title:
                continue
            url = normalize_url(href)
            date_text = span_tag.get_text(strip=True)
            pub_date = extract_date(date_text)
            if pub_date:
                items.append({
                    "title": title,
                    "url": url,
                    "pub_date": pub_date,
                    "doc_num": None
                })
    return items

# ========== 配置 ==========
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))

FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")

# 检查环境变量
required_env = [
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "FEISHU_WEBHOOK"
]

for key in required_env:
    if not os.getenv(key):
        raise ValueError(f"环境变量缺失: {key}")

CHANNELS = [
    {
        "name": "法规文件",
        "list_url": "https://www.nmpa.gov.cn/xxgk/fgwj/index.html",
        "parse_func": parse_fgwj_list,
        "enabled": True
    },
    {
        "name": "药监动态",
        "list_url": "https://www.nmpa.gov.cn/yaowen/ypjgyw/index.html",
        "parse_func": parse_ypjgyw_list,
        "enabled": True
    }
]

MIN_DELAY = 2
MAX_DELAY = 5
MAX_RETRIES = 3

# ========== 关键词库 ==========
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
        }, timeout=120)
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
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='nmpa_announcements' AND column_name='channel') THEN
                ALTER TABLE nmpa_announcements ADD COLUMN channel VARCHAR(50);
            END IF;
        END $$;
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_announcement(title, url, pub_date, doc_num, category, channel):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO nmpa_announcements (title, url, publish_date, document_number, category, channel)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (title, url, pub_date, doc_num, category, channel))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"数据库错误: {e}")
        logging.error(f"Database Error: {e}")
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

def is_content_missing(url):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT content, summary FROM nmpa_announcements WHERE url=%s", (url,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return True
    content, summary = row
    if not content or content == "" or not summary or summary.startswith("（正文") or summary.startswith("（摘要生成失败"):
        return True
    return False

def fetch_page_content(page, url):
    for attempt in range(MAX_RETRIES):
        try:
            tab = page.new_tab(url)
            time.sleep(random.uniform(2, 4))
            html = tab.html
            tab.close()
            if html and len(html) > 500:
                return html
        except Exception as e:
            print(f"  抓取失败 {attempt+1}/{MAX_RETRIES}: {e}")
        time.sleep(random.uniform(3, 6))
    return None

def extract_main_text(html):
    soup = BeautifulSoup(html, "lxml")
    selectors = [
        ".text", ".content", "#Content", ".article-content",
        ".TRS_Editor", ".con", "div.news-content", "div.detail-content",
        "article", "main"
    ]
    for selector in selectors:
        content_div = soup.select_one(selector)
        if content_div:
            for tag in content_div(["script", "style"]):
                tag.decompose()
            text = content_div.get_text(separator="\n")
            text = re.sub(r"\n\s*\n", "\n", text)
            if len(text.strip()) > 100:
                return text.strip()
    body = soup.find("body")
    if body:
        for tag in body(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = body.get_text(separator="\n")
        text = re.sub(r"\n\s*\n", "\n", text)
        if len(text.strip()) > 200:
            return text.strip()
    return None

def generate_summary(title, content):
    if not content:
        return "（正文无法获取）"
    truncated = content[:2000]
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
        }, timeout=120)
        if resp.status_code == 200:
            summary = resp.json()["response"].strip()
            if len(summary) > 100 or not summary:
                return title[:40] + "..."
            return summary
        else:
            return f"（摘要生成失败，HTTP状态码: {resp.status_code}）"
    except Exception as e:
        print(f"⚠️ AI 摘要失败: {e}")
        return f"（摘要生成失败: {str(e)[:50]}）"

def process_announcement(page, item, is_new, channel_name):
    url = item['url']
    if is_new:
        print(f"  ✅ 新增: {item['title'][:40]}... [{item.get('category', '其他')}] from {channel_name}")
    else:
        print(f"  🔄 重新抓取（之前缺失）: {item['title'][:40]}... from {channel_name}")
    
    print(f"  📄 抓取正文: {url[:80]}...")
    html = fetch_page_content(page, url)
    if not html:
        print(f"  ❌ 正文抓取失败")
        update_content_summary(url, "", "（正文抓取失败）")
        return "（正文抓取失败）"
    
    content = extract_main_text(html)
    if not content:
        print(f"  ⚠️ 未提取到正文内容")
        update_content_summary(url, "", "（正文提取失败）")
        return "（正文提取失败）"
    
    summary = generate_summary(item['title'], content)
    print(f"  📝 摘要: {summary[:60]}...")
    update_content_summary(url, content, summary)
    return summary

def send_feishu(title_text, items):
    """
    发送飞书消息
    items: list of (title, url, summary, channel, pub_date)
    """
    if not items:
        return
    content_lines = []
    for idx, (item_title, item_url, item_summary, channel, pub_date) in enumerate(items, 1):
        date_str = pub_date.strftime("%Y-%m-%d") if pub_date else "日期未知"
        line = [
            {"tag": "text", "text": f"{idx}. "},
            {"tag": "text", "text": f"【{channel}】"},
            {"tag": "a", "text": item_title, "href": item_url},
            {"tag": "text", "text": f" ({date_str})\n"},
            {"tag": "text", "text": f"   📝 {item_summary}\n\n"}
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
        logging.error(f"Feishu Error: {e}")

def get_page_with_retry(page, url):
    for attempt in range(MAX_RETRIES):
        try:
            page.get(url)
            for _ in range(20):
                if len(page.html) > 500:
                    break
                time.sleep(0.5)
            time.sleep(random.uniform(2, 4))
            return True
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次访问失败: {e}")
        if attempt < MAX_RETRIES - 1:
            time.sleep(random.uniform(2, 5))
    return False

def filter_recent_items(items, days=7):
    today = datetime.now().date()
    cutoff = today - timedelta(days=days)
    filtered = []
    for item in items:
        pub_date = item.get('pub_date')
        if pub_date is None:
            continue
        if pub_date >= cutoff:
            filtered.append(item)
        else:
            print(f"⏭️ 跳过超过{days}天的公告：{item['title'][:40]}... ({pub_date})")
    return filtered

def main():
    force_refetch = "--force" in sys.argv
    if force_refetch:
        print("⚠️ 强制模式：将重新抓取所有正文缺失的公告（仅限7天内）")
    
    print("🚀 启动 NMPA 公告采集（多频道，正文+AI摘要）")
    logging.info("Crawler Started")
    ensure_columns()

    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    page = ChromiumPage(addr_or_opts=co)

    try:
        all_processed = []
        total_new = 0
        total_refetch = 0

        for channel in CHANNELS:
            if not channel.get("enabled", True):
                continue
            print(f"\n📡 正在采集频道：{channel['name']}")
            if not get_page_with_retry(page, channel['list_url']):
                print(f"  ❌ 无法获取列表页，跳过")
                continue

            items = channel['parse_func'](page)
            print(f"  📄 从列表页提取到 {len(items)} 条公告")
            recent_items = filter_recent_items(items, days=7)
            print(f"  📅 7天内公告：{len(recent_items)} 条")

            new_count = 0
            refetch_count = 0
            channel_processed = []

            for item in recent_items:
                text_for_classify = f"{item['title']} {item['doc_num'] or ''}"
                category = classify_by_text(text_for_classify)
                item['category'] = category

                inserted = insert_announcement(
                    item['title'], item['url'], item['pub_date'],
                    item['doc_num'], category, channel['name']
                )

                if inserted:
                    new_count += 1
                    summary = process_announcement(page, item, is_new=True, channel_name=channel['name'])
                    # 存储 (title, url, summary, channel, pub_date)
                    channel_processed.append((item['title'][:60], item['url'], summary, channel['name'], item['pub_date']))
                    time.sleep(random.uniform(3, 6))
                else:
                    pub_date = item.get('pub_date')
                    if pub_date and (datetime.now().date() - pub_date).days > 7:
                        continue
                    if force_refetch or is_content_missing(item['url']):
                        refetch_count += 1
                        summary = process_announcement(page, item, is_new=False, channel_name=channel['name'])
                        channel_processed.append((item['title'][:60], item['url'], summary, channel['name'], item['pub_date']))
                        time.sleep(random.uniform(3, 6))

            if new_count > 0 or refetch_count > 0:
                print(f"  ✅ {channel['name']} 频道：新增 {new_count} 条，重抓 {refetch_count} 条")
                all_processed.extend(channel_processed)
                total_new += new_count
                total_refetch += refetch_count
            else:
                print(f"  ℹ️ {channel['name']} 频道无更新")

            time.sleep(random.uniform(5, 10))

        if all_processed:
            today = datetime.now().strftime("%Y-%m-%d")
            title_text = f"📢 NMPA 公告更新（{today}）"
            if total_new > 0:
                title_text += f" 新增{total_new}条"
            if total_refetch > 0:
                title_text += f" 重抓{total_refetch}条"
            send_feishu(title_text, all_processed)
        else:
            print("\nℹ️ 所有频道均无新增或7天内无缺失内容")
    finally:
        page.quit()
        print("✅ 浏览器已关闭")

    print("✅ 采集完成")
    logging.info("Crawler Finished")

if __name__ == "__main__":
    main()
