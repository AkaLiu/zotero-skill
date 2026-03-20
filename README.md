# Zotero Skill / Zotero 文献助手

Language: [English](#english) | [中文](#chinese)

<a id="english"></a>
## English

### Overview

Zotero Skill is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex](https://openai.com/index/introducing-codex/) skill that connects your local Zotero library to an LLM workflow and turns it into a **local RAG (Retrieval-Augmented Generation)** system:

> Retrieval: search papers, notes, and local PDFs from your Zotero library
> Augmentation: inject metadata and PDF content into the LLM context
> Generation: summarize, compare, analyze, and reason over real papers

All data stays local. Zotero Desktop is the knowledge base, and the LLM is the analysis layer.

Supported platforms: **Claude Code** (Anthropic) and **Codex** (OpenAI).

### Features

- Search papers by keyword / collection / tag
- Expand keywords across Chinese and English automatically
- Search only within abstracts
- Recommend similar papers from your local library or the web
- Integrate with Claude Scholar research workflows
- Inspect metadata such as title, authors, abstract, DOI, and venue
- Show scan-friendly long result cards
- View paper overviews including abstract / attachments / notes / collections / tags
- Read cleaned Zotero notes separately
- Inspect attachments and local file paths
- Read PDFs for deeper analysis
- Summarize papers, explain sections, extract concepts
- Compare multiple papers

### Prerequisites

- [Zotero](https://www.zotero.org/) Desktop must be running and exposing `http://localhost:23119/api/`
- Python 3 is required; helper scripts use only the standard library

### Installation

Clone this repository into your skills directory:

```bash
git clone https://github.com/AkaLiu/zotero-skill.git ~/.agents/skills/zotero
```

### Usage

Mention `zotero` in Claude Code or use the `/zotero` command:

```text
/zotero search "transformer attention"
/zotero summarize the 5 most recently added papers
/zotero compare the methods used in these two papers
```

You can also trigger it in Codex or Claude with natural language:

- "Search English papers with Chinese keywords"
- "Search only abstracts for sparse attention"
- "Find papers similar to this one, first locally then online"
- "Is this paper worth reading?"
- "Show me what was recently added to this Zotero collection"
- "Verify the citations in this related work section"
- "Find research gaps from this group of papers"
- "Turn this Zotero collection into Obsidian literature notes"
- "Help me draft a rebuttal or review response"

### Common Workflows

#### 1. Search papers

```bash
python3 scripts/zotero_api.py search "agentic retrieval" -n 5 --long
python3 scripts/zotero_api.py search "注意力机制" -n 5 --long
python3 scripts/zotero_api.py search "large language model" -n 5 --long
python3 scripts/zotero_api.py search "稀疏注意力" -n 10 -c COLLECTION_KEY --long
```

Notes:

- `--long` prints scan-friendly cards with authors, venue, date, abstract snippets, and tags
- Bilingual keyword expansion is enabled by default via [scripts/bilingual_aliases.json](/Users/liutianyu/.agents/skills/zotero/scripts/bilingual_aliases.json)
- Use `--no-bilingual` to disable bilingual expansion
- Use `--include-notes` if you also want Zotero notes in search results

#### 2. Search only abstracts

```bash
python3 scripts/zotero_api.py abstract-search "sparse attention" -n 5 --long
python3 scripts/zotero_api.py abstract-search "稀疏注意力" -n 5 --long
```

#### 3. Browse collections and recent items

```bash
python3 scripts/zotero_api.py collections
python3 scripts/zotero_api.py collections --tree
python3 scripts/zotero_api.py collection-items COLLECTION_KEY -n 20 --long
python3 scripts/zotero_api.py recent -n 10 --long
```

#### 4. Decide whether a paper is worth reading

```bash
python3 scripts/zotero_api.py overview ITEM_KEY
python3 scripts/zotero_api.py abstract ITEM_KEY
python3 scripts/zotero_api.py notes ITEM_KEY
python3 scripts/zotero_api.py attachments ITEM_KEY
python3 scripts/zotero_api.py pdf ITEM_KEY
```

Suggested order:

1. `overview ITEM_KEY`
2. `abstract ITEM_KEY`
3. `notes ITEM_KEY`
4. `attachments ITEM_KEY`
5. `pdf ITEM_KEY`

#### 5. Find similar papers

```bash
# Similar papers in local Zotero
python3 scripts/zotero_api.py similar ITEM_KEY -n 5 --long

# Similar papers from the web (OpenAlex)
python3 scripts/zotero_api.py web-similar ITEM_KEY -n 5
```

#### 6. Compare papers and do deeper reading

Recommended flow:

1. Use `search` or `abstract-search` to find candidates
2. Use `overview` or `abstract` to confirm targets
3. Use `pdf` to get the local PDF path
4. Ask Claude or Codex to summarize, compare, or explain the paper based on the PDF

### Claude Scholar Integration

The following Claude Scholar skills are already mounted in the same environment:

- `research-ideation`
- `zotero-obsidian-bridge`
- `citation-verification`
- `paper-self-review`
- `review-response`
- `daily-paper-generator`

They can be triggered either by natural language or explicitly by skill name.

---

<a id="chinese"></a>
## 中文

### 简介

Zotero Skill 是一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex](https://openai.com/index/introducing-codex/) Skill，通过 Zotero 本地 API 将个人文献库接入 LLM，形成**本地 RAG（Retrieval-Augmented Generation）**工作流：

> 检索：从 Zotero 本地库中搜索文献、笔记和 PDF 全文
> 增强：将论文元数据与 PDF 内容注入 LLM 上下文
> 生成：基于真实文献内容进行摘要、对比、分析和推理

所有数据均留在本地，不依赖云端向量数据库。Zotero 桌面端就是知识库，LLM 就是分析引擎。

支持平台：**Claude Code** (Anthropic) 和 **Codex** (OpenAI)。

### 功能

- 按关键词 / 集合 / 标签搜索文献
- 自动做中英文关键词扩展检索
- 只按摘要字段搜索
- 从本地库或外网推荐相似论文
- 与 Claude Scholar 研究工作流联动
- 查看标题、作者、摘要、DOI、venue 等元数据
- 输出更适合扫读的长格式结果卡片
- 查看包含摘要 / 附件 / 笔记 / 集合 / 标签的一站式论文概览
- 单独查看清洗后的 Zotero 笔记
- 查看附件及本地文件路径
- 阅读 PDF 并做深度分析
- 做论文概览、逐章解读、概念提取
- 对比多篇论文

### 前置条件

- [Zotero](https://www.zotero.org/) 桌面端正在运行，并提供 `http://localhost:23119/api/`
- 需要 Python 3；辅助脚本只依赖标准库

### 安装

将仓库克隆到 skills 目录：

```bash
git clone https://github.com/AkaLiu/zotero-skill.git ~/.agents/skills/zotero
```

### 使用

在 Claude Code 中提到 `zotero` 或使用 `/zotero` 命令即可触发：

```text
/zotero 搜索 "transformer attention"
/zotero 帮我总结最近添加的 5 篇论文
/zotero 对比这两篇论文的方法差异
```

在 Codex / Claude 中也可以直接用自然语言触发：

- “帮我用中文关键词搜英文论文”
- “只在摘要里搜 sparse attention”
- “找这篇论文的类似文章，先查本地再查网上”
- “这篇论文值不值得读”
- “帮我看这个 collection 最近加了什么”
- “核对这段 related work 的引用”
- “基于这批论文帮我找 research gap”
- “把这个 Zotero collection 变成 Obsidian 论文笔记”
- “帮我写 rebuttal / review response”

### 常见工作流

#### 1. 检索文献

```bash
python3 scripts/zotero_api.py search "agentic retrieval" -n 5 --long
python3 scripts/zotero_api.py search "注意力机制" -n 5 --long
python3 scripts/zotero_api.py search "large language model" -n 5 --long
python3 scripts/zotero_api.py search "稀疏注意力" -n 10 -c COLLECTION_KEY --long
```

说明：

- `--long` 会输出更适合扫读的结果卡片，包含作者、venue、日期、摘要片段和标签
- 默认启用双语扩展，词表在 [scripts/bilingual_aliases.json](/Users/liutianyu/.agents/skills/zotero/scripts/bilingual_aliases.json)
- 如需关闭双语扩展，可加 `--no-bilingual`
- 如需把 `note` 一起搜出来，可加 `--include-notes`

#### 2. 只按摘要搜索

```bash
python3 scripts/zotero_api.py abstract-search "sparse attention" -n 5 --long
python3 scripts/zotero_api.py abstract-search "稀疏注意力" -n 5 --long
```

#### 3. 看 collection 和最近条目

```bash
python3 scripts/zotero_api.py collections
python3 scripts/zotero_api.py collections --tree
python3 scripts/zotero_api.py collection-items COLLECTION_KEY -n 20 --long
python3 scripts/zotero_api.py recent -n 10 --long
```

#### 4. 快速判断一篇论文值不值得读

```bash
python3 scripts/zotero_api.py overview ITEM_KEY
python3 scripts/zotero_api.py abstract ITEM_KEY
python3 scripts/zotero_api.py notes ITEM_KEY
python3 scripts/zotero_api.py attachments ITEM_KEY
python3 scripts/zotero_api.py pdf ITEM_KEY
```

建议顺序：

1. `overview ITEM_KEY`
2. `abstract ITEM_KEY`
3. `notes ITEM_KEY`
4. `attachments ITEM_KEY`
5. `pdf ITEM_KEY`

#### 5. 找类似文章

```bash
# 本地 Zotero 相似文章
python3 scripts/zotero_api.py similar ITEM_KEY -n 5 --long

# 外网相似文章（OpenAlex）
python3 scripts/zotero_api.py web-similar ITEM_KEY -n 5
```

#### 6. 多论文比较和深度阅读

推荐流程：

1. 先用 `search` 或 `abstract-search` 找到候选论文
2. 用 `overview` 或 `abstract` 确认目标
3. 用 `pdf` 获取本地 PDF 路径
4. 让 Claude 或 Codex 基于 PDF 做总结、对比或解释

### Claude Scholar 联动

当前环境已经挂载以下 Claude Scholar skills：

- `research-ideation`
- `zotero-obsidian-bridge`
- `citation-verification`
- `paper-self-review`
- `review-response`
- `daily-paper-generator`

这些能力既可以通过自然语言触发，也可以显式使用技能名调用。
