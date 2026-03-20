# Zotero Skill — 基于本地 Zotero 的 RAG 文献助手

一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex](https://openai.com/index/introducing-codex/) Skill，通过 Zotero 本地 API 将你的个人文献库接入 LLM，形成**本地 RAG（Retrieval-Augmented Generation）**工作流：

> 检索（Retrieval）：从 Zotero 本地库中搜索、定位文献及 PDF 全文
> 增强（Augmentation）：将论文元数据与 PDF 内容注入 LLM 上下文
> 生成（Generation）：基于真实文献内容进行摘要、分析、对比等任务

所有数据均留在本地，不依赖任何云端向量数据库。Zotero 桌面端即是你的知识库，LLM 即是你的分析引擎。

支持平台：**Claude Code** (Anthropic) 和 **Codex** (OpenAI)。

## 功能

- 搜索文献（关键词 / 集合 / 标签）
- 中英文关键词扩展检索
- 只按摘要字段搜索
- 本地 / 外网相似文章推荐
- 与 Claude Scholar 的研究工作流联动
- 查看论文元数据（标题、作者、摘要、DOI 等）
- 更适合扫读的长格式结果卡片
- 一站式论文概览（摘要 / 附件 / 笔记 / 集合 / 标签）
- 单独查看清洗后的 Zotero 笔记
- 查看附件及本地文件路径
- 阅读 PDF 全文并进行深度分析
- 论文概览 / 逐章解读 / 概念提取
- 多篇论文对比

## 前置条件

- [Zotero](https://www.zotero.org/) 桌面端正在运行（提供 `http://localhost:23119/api/`）
- Python 3（辅助脚本仅使用标准库，无第三方依赖）

## 安装

将本仓库克隆到 Claude Code 的 skills 目录：

```bash
git clone https://github.com/AkaLiu/zotero-skill.git ~/.agents/skills/zotero
```

## 使用

在 Claude Code 中提到 "zotero" 或使用 `/zotero` 命令即可触发。例如：

```
/zotero 搜索 "transformer attention"
/zotero 帮我总结最近添加的 5 篇论文
/zotero 对比这两篇论文的方法差异
```

在 Codex / Claude 里也可以直接用自然语言触发，不需要记脚本命令。典型说法：

- “帮我用中文关键词搜英文论文”
- “只在摘要里搜 sparse attention”
- “找这篇论文的类似文章，先查本地再查网上”
- “这篇论文值不值得读”
- “帮我看这个 collection 最近加了什么”
- “核对这段 related work 的引用”
- “基于这批论文帮我找 research gap”
- “把这个 Zotero collection 变成 Obsidian 论文笔记”
- “帮我写 rebuttal / review response”

## 功能怎么用

### 1. 检索文献

适合：

- 普通关键词搜索
- 中文搜英文论文
- 英文搜中文笔记或中文标签
- 限定到某个 collection 内搜索

```bash
python3 scripts/zotero_api.py search "agentic retrieval" -n 5 --long
python3 scripts/zotero_api.py search "注意力机制" -n 5 --long
python3 scripts/zotero_api.py search "large language model" -n 5 --long
python3 scripts/zotero_api.py search "稀疏注意力" -n 10 -c COLLECTION_KEY --long
```

说明：

- `--long` 会输出更适合扫读的结果卡片，包含作者、venue、日期、摘要片段、标签
- 双语扩展默认开启，词表在 [scripts/bilingual_aliases.json](/Users/liutianyu/.agents/skills/zotero/scripts/bilingual_aliases.json)
- 如需关闭双语扩展，可加 `--no-bilingual`
- 默认不返回 `note`，如需把笔记也搜出来可加 `--include-notes`

### 2. 只按摘要搜索

适合：

- 只想找 abstract 里明确出现某个概念的论文
- 避免标题误命中

```bash
python3 scripts/zotero_api.py abstract-search "sparse attention" -n 5 --long
python3 scripts/zotero_api.py abstract-search "稀疏注意力" -n 5 --long
```

说明：

- `abstract-search` 会先召回候选，再过滤成“只有 abstract 命中”的条目
- 同样支持默认的中英双语关键词扩展

### 3. 看 collection 和最近条目

适合：

- 浏览 Zotero 目录结构
- 看某个 collection 里最近更新的论文
- 先扫读一批最近导入的文章

```bash
python3 scripts/zotero_api.py collections
python3 scripts/zotero_api.py collections --tree
python3 scripts/zotero_api.py collection-items COLLECTION_KEY -n 20 --long
python3 scripts/zotero_api.py recent -n 10 --long
```

### 4. 快速判断一篇论文值不值得读

适合：

- 先看摘要、标签、附件、笔记，再决定是否打开 PDF
- 利用你已经写过的 Zotero notes 做快速判断

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

### 5. 找类似文章

适合：

- 围绕一篇种子论文继续扩展阅读
- 先看本地库里有没有相关论文，再去网上补充

```bash
# 本地 Zotero 相似文章
python3 scripts/zotero_api.py similar ITEM_KEY -n 5 --long

# 外网相似文章（OpenAlex）
python3 scripts/zotero_api.py web-similar ITEM_KEY -n 5
```

说明：

- `similar` 基于标题、abstract、tags、作者做本地相似度排序
- `web-similar` 当前用 OpenAlex 公共 API，不需要 MCP
- 如果你想控制 OpenAlex polite pool，可传 `--mailto your@email.com`

### 6. 多论文比较和深度阅读

适合：

- 对比方法差异
- 总结贡献、实验结论、局限性
- 提取关键概念和术语

推荐工作流：

1. 先用 `search` / `abstract-search` 找到候选论文
2. 用 `overview` / `abstract` 确认目标
3. 用 `pdf` 获取本地 PDF
4. 让 Claude / Codex 基于 PDF 做总结、对比、概念解释

脚本层也可以直接使用：

```bash
# 更适合扫读的搜索结果
python3 scripts/zotero_api.py search "agentic retrieval" -n 5 --long

# 中文搜英文论文 / 英文搜中文笔记
python3 scripts/zotero_api.py search "注意力机制" -n 5 --long
python3 scripts/zotero_api.py search "large language model" -n 5 --long

# 只按 abstract 搜索
python3 scripts/zotero_api.py abstract-search "sparse attention" -n 5 --long

# 在本地 Zotero 里找相似文章
python3 scripts/zotero_api.py similar ITEM_KEY -n 5 --long

# 去外网找相似文章（OpenAlex）
python3 scripts/zotero_api.py web-similar ITEM_KEY -n 5

# 一站式查看一篇论文
python3 scripts/zotero_api.py overview ITEM_KEY

# 只看笔记 / 摘要 / 附件
python3 scripts/zotero_api.py notes ITEM_KEY
python3 scripts/zotero_api.py abstract ITEM_KEY
python3 scripts/zotero_api.py attachments ITEM_KEY

# 树形查看集合
python3 scripts/zotero_api.py collections --tree
```

## Claude Scholar 联动

已经为 Codex 挂载一组和 Zotero 工作流直接相关的 Claude Scholar skills：

- `research-ideation`
- `zotero-obsidian-bridge`
- `citation-verification`
- `paper-self-review`
- `review-response`
- `daily-paper-generator`

这些能力已经注册到 `~/.agents/skills`，并通过本机注册脚本同步到 Claude 和 Codex。可以直接通过自然语言触发，也可以显式写技能名，例如：

- `$research-ideation`
- `$zotero-obsidian-bridge`
- `$citation-verification`
- `$paper-self-review`
- `$review-response`
- `$daily-paper-generator`

常见自然语言触发方式：

- “基于我 Zotero 里的这组论文帮我找 research gap”
- “核对这段 related work 的引用是不是准确”
- “把这个 collection 整理成 Obsidian 论文笔记”
- “基于这篇论文帮我写 rebuttal 草稿”

推荐搭配方式：

- `zotero` + `research-ideation`：先搜论文，再做 gap analysis / 研究问题收敛
- `zotero` + `citation-verification`：先定位论文，再核对 related work 引用真伪
- `zotero` + `zotero-obsidian-bridge`：把 collection 变成 Obsidian 中的论文笔记和知识图谱
- `zotero` + `review-response`：围绕某篇论文或 reviewer comment 写 rebuttal
- `zotero` + `paper-self-review`：围绕你的草稿补强相关工作、方法对比和引用完整性

## 备注

- 双语检索默认开启，词表来自 [scripts/bilingual_aliases.json](/Users/liutianyu/.agents/skills/zotero/scripts/bilingual_aliases.json)。如果你的领域里有常用中英术语，可以直接继续往里面追加
- 外网相似文章当前不需要 MCP，直接使用 OpenAlex 公共 API；如果后面你想接更强的学术检索源，再补 MCP 也可以
- 目前 skill 注册目录以 `~/.agents/skills` 为源，`~/.claude/skills` 和 `~/.codex/skills` 只是注册后的软链接入口

## 项目结构

```
├── SKILL.md                  # Skill 定义（Claude Code 入口）
├── agents/openai.yaml        # Agent 配置
├── references/
│   ├── api_reference.md      # API 参考文档
│   └── zotero_api.md         # Zotero API 详细说明
└── scripts/
    └── zotero_api.py         # 辅助脚本（搜索/获取元数据/定位 PDF）
```

## License

MIT
