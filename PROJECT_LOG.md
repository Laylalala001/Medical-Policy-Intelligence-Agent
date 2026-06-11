# Project Development Log

## Project Overview

Medical Regulatory Intelligence Platform (MRIP)

面向医药企业、医疗器械企业及医疗AI企业的监管情报自动化平台。

目标：

通过自动采集、AI分类、AI摘要及飞书推送能力，实现监管情报自动化监测。

---

# Version 1.0

Date: 2026-06

## Initial Problem

在医药行业工作过程中发现：

* NMPA政策更新频繁
* 行业从业者需要频繁访问官网
* 人工检索效率较低
* 信息容易遗漏
* 缺少统一监管情报平台

因此开始开发自动化监管情报系统。

---

## Completed Features

### Data Collection

完成：

* NMPA法规文件采集

支持：

* 自动翻页
* 增量更新
* 去重处理

---

### Data Storage

完成：

* PostgreSQL数据库搭建
* Docker部署

实现：

* 公告结构化存储
* 历史数据留存

---

### AI Processing

完成：

* Ollama部署
* Qwen2-7B接入

实现：

* 自动分类
* 自动摘要

---

### Notification

完成：

* 飞书机器人接入

实现：

* 日报推送
* 周报推送

---

# Version 2.0

Date: 2026-06

## Why Upgrade

法规文件更新频率较低。

对于医药企业而言，仅监测法规文件无法覆盖监管动态变化。

企业同样关注：

* 监管会议
* 工作部署
* 政策解读
* 行业监管方向

因此新增药监动态监测能力。

---

## New Features

新增：

### NMPA药监动态采集

支持：

* 新闻动态监测
* 监管动态跟踪

项目定位升级：

Policy Monitor

↓

Medical Regulatory Intelligence Platform

---

# Current System Architecture

Data Sources

↓

NMPA法规文件

NMPA药监动态

↓

Python Collector

↓

PostgreSQL

↓

AI Classification

↓

AI Summarization

↓

Feishu Notification

↓

Weekly Report

---

# Current Status

Implemented:

✅ NMPA法规文件监测

✅ NMPA药监动态监测

✅ PostgreSQL存储

✅ AI分类

✅ AI摘要

✅ 飞书推送

✅ 周报生成

---

# Roadmap

## Version 3.0

Planned

* CDE审评动态
* CMDE审评动态
* 飞行检查公告
* 不良反应监测

---

## Version 4.0

Planned

* 医疗AI资讯
* 国家医保局政策
* 医疗行业资讯聚合

---

## Version 5.0

Planned

* Power BI Dashboard
* 企业级监管情报看板
* 趋势预测分析
* 企业知识库建设

---

# Personal Learning

通过本项目实践学习：

* Python数据采集
* PostgreSQL数据库
* Docker部署
* 本地大模型部署
* AI文本处理
* 自动化工作流设计
* 医药监管信息体系

项目仍持续迭代中。
