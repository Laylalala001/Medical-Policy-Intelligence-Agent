# -*- coding: utf-8 -*-
import psycopg2
import requests
from datetime import datetime, timedelta

DB_NAME = ""
DB_USER = ""
DB_PASSWORD = "" #your_password_here
DB_HOST = "localhost"
DB_PORT = 5432

FEISHU_WEBHOOK = "" #your_webhook_key

def get_db_conn():
    return psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def send_feishu_post(title, items_by_category):
    if not items_by_category:
        print("没有数据，不发送")
        return
    content_lines = []
    for cat, items in items_by_category.items():
        content_lines.append([{"tag": "text", "text": f"【{cat}】\n"}])
        for idx, (item_title, url, pub_date, summary) in enumerate(items[:10], 1):
            content_lines.append([
                {"tag": "text", "text": f"{idx}. "},
                {"tag": "a", "text": item_title, "href": url},
                {"tag": "text", "text": f"（{pub_date}）\n"}
            ])
            if summary and summary not in ("（正文无法获取）", "（摘要生成失败）"):
                content_lines.append([
                    {"tag": "text", "text": f"   📌 {summary}\n"}
                ])
        content_lines.append([{"tag": "text", "text": "\n"}])
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content_lines
                }
            }
        }
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ 周报已发送到飞书")
        else:
            print(f"❌ 发送失败: {resp.text}")
    except Exception as e:
        print(f"❌ 异常: {e}")

def get_last_week_announcements(days=7):
    """查询最近 days 天的公告（含 summary）"""
    conn = get_db_conn()
    cur = conn.cursor()
    date_limit = (datetime.now() - timedelta(days=days)).date()
    cur.execute("""
        SELECT 
            COALESCE(category, '未分类') as category,
            title,
            url,
            COALESCE(publish_date, created_at::date) as display_date,
            COALESCE(summary, '') as summary
        FROM nmpa_announcements
        WHERE COALESCE(publish_date, created_at::date) >= %s
        ORDER BY category, display_date DESC
    """, (date_limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def group_by_category(rows):
    groups = {}
    for cat, title, url, pub_date, summary in rows:
        groups.setdefault(cat, []).append((title, url, pub_date, summary))
    return groups

def main():
    days = 7
    print(f"📊 正在生成 NMPA 医药政策周报（最近 {days} 天，含AI摘要）...")
    rows = get_last_week_announcements(days=days)
    if not rows:
        print(f"最近 {days} 天没有找到任何公告")
        return
    groups = group_by_category(rows)
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"📢 NMPA 医药政策周报（最近 {days} 天，{today}）"
    send_feishu_post(title, groups)

if __name__ == "__main__":
    main()