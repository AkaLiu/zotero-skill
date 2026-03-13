---
name: zotero
description: >
  Zotero 本地文献库助手。通过 Zotero 本地 API (localhost:23119) 搜索、浏览和深度分析文献。
  触发条件：用户提到 "zotero"、使用 /zotero 命令、或请求分析 Zotero 库中的论文。
  功能包括：(1) 搜索文献 (2) 浏览集合/标签 (3) 查看论文元数据 (4) 阅读并分析 PDF 全文
  (5) 论文摘要/核心概念提取/关键贡献分析 (6) 多篇论文对比
---

# Zotero 文献分析助手

## 前置条件

- Zotero 桌面端必须正在运行（提供 `http://localhost:23119/api/`）
- 辅助脚本：`scripts/zotero_api.py`（无第三方依赖，仅用 Python 标准库）
- API 参考：`references/zotero_api.md`

## 辅助脚本用法

```bash
# 搜索文献
python3 scripts/zotero_api.py search "关键词" -n 10

# 列出所有集合
python3 scripts/zotero_api.py collections

# 查看某集合下的文献
python3 scripts/zotero_api.py collection-items COLLECTION_KEY -n 20

# 查看文献详细元数据
python3 scripts/zotero_api.py item ITEM_KEY

# 查看附件/笔记
python3 scripts/zotero_api.py children ITEM_KEY

# 获取 PDF 本地路径
python3 scripts/zotero_api.py pdf ITEM_KEY

# 最近修改的文献
python3 scripts/zotero_api.py recent -n 10
```

## 工作流

### 1. 定位文献

根据用户请求定位目标文献：

- **用户给出关键词**：`search "keyword"` 搜索，展示匹配结果让用户确认
- **用户指定集合**：`collections` 列出集合 → `collection-items KEY` 列出内容
- **用户给出标题/作者**：`search` 匹配，如有多条结果，列出供选择
- **用户给出 item key**：直接 `item KEY` 获取

### 2. 获取元数据

用 `item KEY` 获取论文基本信息（标题、作者、摘要、DOI 等），先向用户展示确认是目标文献。

### 3. 阅读 PDF

用 `pdf KEY` 获取 PDF 本地路径，然后用 Read 工具读取 PDF 内容。对于较长的论文，分页读取。

### 4. 分析与输出

根据用户需求提供分析，常见模式：

**论文概览**：
- 一句话总结
- 研究动机与问题
- 核心方法/贡献
- 关键实验结果
- 局限性与未来工作

**深度解读**：
- 逐章节详细分析
- 关键公式/算法解释
- 图表解读
- 与相关工作的对比

**概念解释**：
- 提取论文中的专业术语
- 用通俗语言解释核心概念
- 提供直觉性的类比

**多论文对比**：
- 分别获取各论文信息
- 比较方法差异、适用场景、性能指标
- 以表格形式呈现对比

## 输出语言

与用户使用的语言保持一致。如用户用中文提问，则用中文回答。
