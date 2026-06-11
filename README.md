# 📡 AI-Driven Pharmaceutical Policy Intelligence System

> 基于 Python + PostgreSQL + Ollama + 飞书构建的医药政策情报自动化系统

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.14-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Ollama](https://img.shields.io/badge/Ollama-Qwen2--7B-orange)

---

# 📖 项目背景

在医药、医疗器械及医疗AI行业中，政策变化会直接影响：

* 药品注册审批
* 医疗器械上市
* 医保准入
* 企业研发方向
* 行业投资决策

然而行业从业者通常需要每天手动访问国家药监局（NMPA）官网查看公告，效率较低。

因此开发本项目，实现：

> 自动抓取 → 自动分类 → AI摘要 → 飞书推送 → 周报汇总

帮助从业人员第一时间获取关键政策动态。

---

# 🎯 项目目标

实现一个无人值守的政策情报系统：

```text
NMPA官网
    ↓
自动采集
    ↓
PostgreSQL存储
    ↓
AI分类
    ↓
AI摘要
    ↓
飞书推送
    ↓
周报生成
```

每日自动运行。

无需人工干预。

---

# 🚀 核心功能

## 1. 自动采集

自动访问国家药监局官网：

* 法规公告
* 注册审批公告
* 医疗器械公告
* 化妆品公告

支持：

* 翻页抓取
* 新增公告检测
* 去重处理

---

## 2. 智能分类

根据标题和正文内容自动分类：

| 分类   | 示例        |
| ---- | --------- |
| 药品   | 药品审批、药品注册 |
| 医疗器械 | 医疗器械注册、备案 |
| 化妆品  | 化妆品监管公告   |

分类准确率：

> 95%+

---

## 3. AI摘要

调用本地大模型：

```text
Ollama
+
Qwen2-7B
```

自动生成：

* 公告核心内容
* 政策变化要点
* 企业影响分析

示例：

原文：

```text
关于批准XX药品上市申请的公告
```

AI摘要：

```text
NMPA批准XX药品上市，预计将进一步丰富相关治疗领域用药选择。
```

---

## 4. 飞书推送

自动发送至飞书群：

* 标题
* 分类
* AI摘要
* 原文链接

支持点击跳转原公告。

---

## 5. 周报生成

每周自动汇总：

* 药品类公告
* 医疗器械类公告
* 化妆品类公告

生成：

```text
本周政策动态周报
```

自动推送飞书。

---

# 🏗️ 系统架构

```text
               ┌───────────────┐
               │ NMPA 官网     │
               └──────┬────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ Python 爬虫      │
            │ DrissionPage     │
            └──────┬───────────┘
                   │
                   ▼
          ┌───────────────────┐
          │ PostgreSQL        │
          │ 数据存储          │
          └──────┬────────────┘
                 │
                 ▼
          ┌───────────────────┐
          │ Ollama            │
          │ Qwen2-7B          │
          └──────┬────────────┘
                 │
                 ▼
          ┌───────────────────┐
          │ AI分类 & AI摘要   │
          └──────┬────────────┘
                 │
                 ▼
          ┌───────────────────┐
          │ 飞书机器人        │
          └───────────────────┘
```

---

# 🛠️ 技术栈

| 模块     | 技术                     |
| ------ | ---------------------- |
| 编程语言   | Python 3.14            |
| 爬虫框架   | DrissionPage           |
| HTML解析 | BeautifulSoup          |
| 数据库    | PostgreSQL             |
| 数据部署   | Docker                 |
| AI模型   | Ollama + Qwen2-7B      |
| 自动调度   | Windows Task Scheduler |
| 消息推送   | 飞书机器人                  |
| 版本控制   | Git                    |

---

# 📂 项目结构

```text
project/
│
├── nmpa_crawler.py
├── nmpa_weekly_report.py
├── backfill_nmpa_recent.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 📦 安装依赖

```bash
pip install psycopg2-binary requests beautifulsoup4 DrissionPage python-dotenv
```

---

# 🐳 启动 PostgreSQL

```bash
docker run -d \
--name postgres_hotspot \
-e POSTGRES_PASSWORD=YOUR_PASSWORD \
-e POSTGRES_USER=analyst \
-e POSTGRES_DB=hotspot \
-v postgres_data:/var/lib/postgresql/data \
-p 5432:5432 \
postgres:16
```

---

# 🤖 安装 Ollama

安装完成后执行：

```bash
ollama pull qwen2:7b
```

启动模型：

```bash
ollama run qwen2:7b
```

---

# ⚙️ 配置数据库

```python
DB_NAME = "hotspot"
DB_USER = "analyst"
DB_PASSWORD = "YOUR_PASSWORD"
DB_HOST = "localhost"
DB_PORT = 5432
```

---

# ⚙️ 配置飞书机器人

```python
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"
```

获取方式：

飞书群

→ 群设置

→ 群机器人

→ 添加自定义机器人

→ 复制 Webhook

---

# 🚀 运行项目

## 每日采集

```bash
python nmpa_crawler.py
```

---

## 周报生成

```bash
python nmpa_weekly_report.py
```

---

## 历史数据补摘要

```bash
python backfill_nmpa_recent.py
```

## 📸 示例

下面是系统数据库中真实存储的公告数据截图，包含标题、分类、AI摘要和发布日期：飞书推送截图

![数据库公告示例](/docs/image.png)

![飞书推送示例](/docs/feishu.jpg)

---

# 📈 项目价值

本项目可应用于：

* 医药企业政策监测
* 医疗器械行业研究
* 行业咨询机构
* 投资研究
* 医疗AI企业情报系统

可扩展至：

* FDA公告
* 医保局政策
* 药明康德资讯
* 医疗AI新闻
* 行业融资动态

---

# 🔮 后续规划

* [ ] 接入 FDA 数据源
* [ ] 接入国家医保局政策
* [ ] 接入医疗AI行业资讯
* [ ] 增加 Power BI 数据看板
* [ ] 增加热点趋势分析
* [ ] 接入 n8n 自动化工作流

---

# 📄 License

MIT License

Copyright (c) 2026
