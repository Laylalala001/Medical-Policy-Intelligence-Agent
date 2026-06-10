# -*- coding: utf-8 -*-
import re
import time
import random
import psycopg2
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions

# ========== 配置 ==========
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = 5432

DAYS_BACK = 7
MIN_DELAY = 3
MAX_DELAY = 6
MAX_RETRIES = 2
# ==========================

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
    print("✅ 已确保 content 和 summary 字段存在")

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
    # NMPA 正文容器选择器（按优先级排序）
    selectors = [
        ".text",                 # 当前页面实际使用的正文容器
        ".content",              # 常见正文容器
        "#Content",              # 旧版常见正文容器
        ".article-content",      # 其他可能容器
        ".TRS_Editor",           # 政府网站常用容器
        ".con"                   # 通用容器
    ]
    for selector in selectors:
        content_div = soup.select_one(selector)
        if content_div:
            # 移除脚本和样式
            for tag in content_div(["script", "style"]):
                tag.decompose()
            # 获取纯文本，保留段落结构
            text = content_div.get_text(separator="\n")
            # 清理多余空白行
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

def update_content_summary(url, content, summary):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE nmpa_announcements SET content=%s, summary=%s WHERE url=%s",
                (content, summary, url))
    conn.commit()
    cur.close()
    conn.close()

def get_recent_empty_summary():
    conn = get_db_conn()
    cur = conn.cursor()
    date_limit = (datetime.now() - timedelta(days=DAYS_BACK)).date()
    cur.execute("""
        SELECT id, title, url, publish_date
        FROM nmpa_announcements
        WHERE (summary IS NULL OR summary = '')
          AND COALESCE(publish_date, created_at::date) >= %s
        ORDER BY COALESCE(publish_date, created_at::date) DESC
    """, (date_limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def main():
    print(f"🔧 开始为最近 {DAYS_BACK} 天内的历史公告补充正文和摘要...")
    ensure_columns()
    rows = get_recent_empty_summary()
    if not rows:
        print("✅ 没有需要补充的公告（最近7天内都已生成摘要）")
        return
    total = len(rows)
    print(f"📋 发现 {total} 条待处理公告")
    for idx, (eid, title, url, pub_date) in enumerate(rows, 1):
        print(f"\n[{idx}/{total}] {title[:50]}...")
        print(f"   URL: {url}")
        print(f"   发布日期: {pub_date}")
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        print(f"   ⏳ 等待 {delay:.1f} 秒...")
        time.sleep(delay)
        html = fetch_page_content(url)
        if not html:
            print(f"   ❌ 正文抓取失败，跳过")
            continue
        content = extract_main_text(html)
        if not content:
            print(f"   ⚠️ 未提取到正文内容，跳过")
            # 可选：保存空白内容避免重复尝试
            update_content_summary(url, "", "（正文提取失败）")
            continue
        summary = generate_summary(title, content)
        print(f"   📝 摘要: {summary[:80]}...")
        update_content_summary(url, content, summary)
        print(f"   ✅ 已更新")
    print("\n🎉 补充完成！现在可以运行周报脚本查看带摘要的最近7天公告了。")

if __name__ == "__main__":
    main()