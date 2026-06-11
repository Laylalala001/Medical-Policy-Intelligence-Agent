# 🏥 Medical Regulatory Intelligence Platform (MRIP)

> 面向医药、医疗器械及医疗AI行业的监管情报自动化平台

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.14-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Ollama](https://img.shields.io/badge/Ollama-Qwen2--7B-orange)

---

# 📖 Project Overview

Medical Regulatory Intelligence Platform（MRIP）是一套面向医药企业、医疗器械企业及医疗AI企业的监管情报自动化系统。

系统每日自动监测国家药品监督管理局（NMPA）重要监管信息，通过自动采集、AI分类、AI摘要及飞书推送能力，帮助企业第一时间获取监管动态，提升法规响应效率。

当前版本已实现：

* NMPA法规文件自动监测
* NMPA药监动态自动监测
* AI自动分类
* AI智能摘要
* PostgreSQL数据存储
* 飞书实时推送
* 周报自动生成

---

# 💼 Business Value

对于医药企业而言，监管信息直接影响：

* 药品研发
* 医疗器械注册
* 临床试验开展
* 产品上市审批
* 市场准入策略
* 企业合规管理

传统模式下，法规专员、注册事务（RA）及行业研究人员需要每天人工访问多个监管网站进行检索。

本项目通过自动化采集与AI处理能力，实现：

* 自动发现监管动态
* 自动提取核心信息
* 降低人工检索成本
* 提高法规响应效率
* 支持研发与注册决策
* 支持行业研究与竞争分析

适用场景：

* 药品注册事务（RA）
* 医疗器械法规事务
* QA/QC质量管理
* 医疗AI企业运营
* 医药咨询机构
* 投资研究机构

---

# 🎯 Project Goal

构建面向医药行业的监管情报自动化平台。

实现：

NMPA → 自动采集 → 数据存储 → AI分析 → 飞书推送 → 周报生成

最终形成无人值守的监管情报体系。

---

# 🚀 Core Features

## 1. Automated Monitoring

自动访问国家药监局（NMPA）官网：

* 法规文件
* 药监动态

支持：

* 自动翻页
* 增量采集
* 去重处理
* 定时运行

---

## 2. AI Classification

自动分类：

| 分类   | 示例          |
| ---- | ----------- |
| 药品   | 药品审批、药品监管   |
| 医疗器械 | 医疗器械注册、标准发布 |
| 化妆品  | 化妆品监管动态     |
| 其他   | 综合监管信息      |

分类准确率：

95%+

---

## 3. AI Summarization

基于本地大模型：

Ollama + Qwen2-7B

自动生成：

* 政策核心内容
* 监管变化要点
* 企业影响分析

示例：

原文：

关于发布药物临床试验质量管理规范的公告

AI摘要：

新版GCP规范将于2026年9月实施，进一步优化药物临床试验质量管理体系，支持生物医药创新研发。

---

## 4. Feishu Notification

自动推送：

* 标题
* 分类
* AI摘要
* 原文链接

支持日报与周报推送。

---

## 5. Weekly Intelligence Report

自动汇总：

* 药品监管动态
* 医疗器械监管动态
* 化妆品监管动态

生成：

NMPA Weekly Intelligence Report

---

# 📡 Data Sources

当前已接入：

| 数据源       | 状态 |
| --------- | -- |
| NMPA 法规文件 | ✅  |
| NMPA 药监动态 | ✅  |

规划接入：

| 数据源         | 状态 |
| ----------- | -- |
| CDE 审评动态    | 🚧 |
| CMDE 医疗器械审评 | 🚧 |
| 飞行检查公告      | 🚧 |
| 药品不良反应监测    | 🚧 |
| 医疗AI专题资讯    | 🚧 |
| 国家医保局政策     | 🚧 |

---

# 🏗 System Architecture

```text
                 NMPA
                   │
        ┌──────────┴──────────┐
        │                     │
   法规文件              药监动态
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
         Python Data Collector
      (DrissionPage + BS4)
                   │
                   ▼
            PostgreSQL
             Database
                   │
                   ▼
          AI Classification
            + Summarization
          (Ollama + Qwen2)
                   │
                   ▼
            Feishu Bot
                   │
                   ▼
        Daily Report / Weekly Report
```

---

# 📊 Project Results

当前已实现：

✅ NMPA法规文件自动监测

✅ NMPA药监动态自动监测

✅ PostgreSQL数据存储

✅ AI自动分类

✅ AI自动摘要

✅ 飞书机器人推送

✅ 自动生成周报

技术栈：

Python · PostgreSQL · Docker · Ollama · Qwen2-7B · DrissionPage · BeautifulSoup

---

# 📸 Demo

数据库存储示例：

![数据库公告示例](/docs/image.png)

飞书推送示例：

![飞书推送示例](/docs/feishu.jpg)

---

# 🎯 Product Positioning

本项目不仅是一个政策爬虫工具。

其目标是逐步构建面向医药企业的监管情报平台（Medical Regulatory Intelligence Platform）。

当前监测来源：

* NMPA法规文件
* NMPA药监动态

未来扩展方向：

* CDE审评动态
* CMDE器械审评
* 飞行检查公告
* 不良反应监测
* 医疗AI资讯
* 医保政策动态

---

# 💰 Commercial Value

通过自动化监管信息采集与AI分析能力，实现：

* 第一时间发现政策变化
* 自动提取监管重点
* 降低人工监测成本
* 提高法规响应速度
* 支持研发与注册决策
* 支持行业竞争情报分析

典型应用：

* 医药企业法规事务
* 医疗器械注册事务
* QA/QC质量体系管理
* 医疗AI企业政策研究
* 医药咨询机构
* 投资研究机构

---

# 🔮 Roadmap

## Version 2.0 ✅

* NMPA法规文件监测
* NMPA药监动态监测
* AI摘要
* 飞书推送

## Version 3.0 🚧

* CDE审评动态
* CMDE审评动态
* 飞行检查公告

## Version 4.0 🚧

* 医疗AI情报系统
* 医保政策监测
* 行业资讯聚合

## Version 5.0 🚧

* Power BI Dashboard
* 企业级情报看板
* 趋势预测分析

---

# 📄 License

MIT License

Copyright (c) 2026 Layla
