---
name: zotero
description: >
  Zotero 本地文献库助手。通过 Zotero 本地 API (localhost:23119) 搜索、浏览和深度分析文献。
  触发条件：用户提到 "zotero"、使用 /zotero 命令、或请求分析 Zotero 库中的论文。
  功能包括：(1) 搜索文献 (2) 浏览集合/标签 (3) 查看论文元数据 (4) 阅读并分析 PDF 全文
  (5) 论文摘要/核心概念提取/关键贡献分析 (6) 多篇论文对比
  (7) 中英文双语关键词扩展检索 (8) 仅按摘要搜索 (9) 本地/外网相似文章推荐
  (10) 结合 Claude Scholar 做 research ideation、citation verification、
  review response、paper self review、Zotero 到 Obsidian 的论文知识桥接
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

# 搜索并输出更适合扫读的长卡片
python3 scripts/zotero_api.py search "关键词" -n 5 --long

# 默认启用中英双语关键词扩展检索
python3 scripts/zotero_api.py search "注意力机制" -n 5 --long
python3 scripts/zotero_api.py search "retrieval augmented generation" -n 5 --long

# 只按 abstract 搜索
python3 scripts/zotero_api.py abstract-search "稀疏注意力" -n 5 --long

# 在本地 Zotero 中找相似文章
python3 scripts/zotero_api.py similar ITEM_KEY -n 5 --long

# 去外网找相似文章（OpenAlex）
python3 scripts/zotero_api.py web-similar ITEM_KEY -n 5

# 列出所有集合
python3 scripts/zotero_api.py collections

# 以树形查看集合
python3 scripts/zotero_api.py collections --tree

# 查看某集合下的文献
python3 scripts/zotero_api.py collection-items COLLECTION_KEY -n 20

# 查看文献一站式概览
python3 scripts/zotero_api.py overview ITEM_KEY

# 查看文献详细元数据
python3 scripts/zotero_api.py item ITEM_KEY

# 查看附件/笔记
python3 scripts/zotero_api.py children ITEM_KEY

# 单独查看清洗后的笔记
python3 scripts/zotero_api.py notes ITEM_KEY

# 单独查看附件及本地路径
python3 scripts/zotero_api.py attachments ITEM_KEY

# 单独查看摘要
python3 scripts/zotero_api.py abstract ITEM_KEY

# 获取 PDF 本地路径
python3 scripts/zotero_api.py pdf ITEM_KEY

# 最近修改的文献
python3 scripts/zotero_api.py recent -n 10 --long
```

## 语言唤起约定

当用户用自然语言表达下面这些意图时，应直接触发对应能力，而不是要求用户记命令：

- “帮我用中文关键词搜英文论文”
- “只在摘要里搜这个词”
- “找这篇的类似文章”
- “先在我本地 Zotero 找类似文章，再去网上补充”
- “这篇值不值得读”
- “帮我核对这段 related work 的引用”
- “基于这批论文帮我找 research gap / brainstorm idea”
- “把这个 Zotero collection 变成 Obsidian 里的论文笔记和知识图谱”
- “帮我写 rebuttal / review response”

如果请求同时匹配当前 `zotero` skill 和已安装的 Claude Scholar skills，应联合使用，而不是二选一。

## 已接入的 Claude Scholar Skills

当前环境已经挂载以下 Claude Scholar 技能，可被自然语言触发，也可显式用技能名调用：

- `$research-ideation`：研究选题、gap analysis、literature review、method planning
- `$zotero-obsidian-bridge`：把 Zotero 条目/集合转成 Obsidian 论文笔记、综述和知识图谱
- `$citation-verification`：核对引用真伪、BibTeX/元数据准确性、避免 fake citations
- `$paper-self-review`：按审稿标准审视论文草稿
- `$review-response`：撰写 rebuttal / review response
- `$daily-paper-generator`：按主题生成每日论文跟踪

## 工作流

### 1. 定位文献

根据用户请求定位目标文献：

- **用户给出关键词**：`search "keyword"` 搜索，展示匹配结果让用户确认
- **用户明确说按摘要搜**：`abstract-search "keyword"`，只保留 abstract 命中的文献
- **用户说找相似文章**：优先 `similar ITEM_KEY`；如果用户明确要查外网，再用 `web-similar ITEM_KEY`
- **用户指定集合**：`collections` 列出集合 → `collection-items KEY` 列出内容
- **用户给出标题/作者**：`search` 匹配，如有多条结果，列出供选择
- **用户给出 item key**：直接 `item KEY` 获取

### 2. 快速建立上下文

优先使用更适合人读的命令：

- `overview KEY`：一站式展示标题、作者、venue、摘要、标签、所属集合、附件、笔记摘要
- `abstract KEY`：只看摘要，适合用户先快速判断是否值得深入
- `notes KEY`：只看笔记，适合先利用已有读书笔记和高亮
- `attachments KEY`：确认 PDF/补充材料是否存在，以及本地路径

需要完整原始元数据时再用 `item KEY`。

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

## 更人性化的默认行为

- 当搜索结果较多时，优先使用 `search --long` / `recent --long` / `collection-items --long`，让用户先扫读标题、作者、venue、摘要片段，而不是只看到 key
- 当用户输入中文关键词而文献主要是英文标题时，优先依赖 `search` 默认启用的双语扩展检索；必要时继续扩充 `scripts/bilingual_aliases.json`
- 当用户说“先帮我看看这篇值不值得读”时，优先走 `overview` + `abstract`，不要立刻整篇 PDF 深读
- 当用户说“找类似文章”时，先确认是“本地库里找”还是“去外网补充”；若用户没说，默认先本地后外网
- 当用户已经在 Zotero 里做过笔记时，优先查看 `notes KEY`，把已有人工判断放在前面
- 当用户想“继续读这篇”或“打开正文”时，先 `attachments KEY` / `pdf KEY` 确认本地 PDF 是否存在
- 如果一个 item 有多个附件，要明确告诉用户哪个是 PDF、哪个可能是 supplementary / snapshot / 其他格式

## 双语检索说明

- `search` 默认会读取 `scripts/bilingual_aliases.json`，对命中的中英文同义词做扩展搜索并合并去重
- `abstract-search` 也支持同样的中英扩展，但最终会额外过滤为“只有 abstract 命中”
- 例如搜 `注意力机制` 时，会自动追加 `attention` / `self-attention` 等变体
- 例如搜 `大语言模型` 时，会自动追加 `large language model` / `llm`
- 如需关闭扩展，可显式加 `--no-bilingual`
- 如果某个领域词还没覆盖，直接往 `scripts/bilingual_aliases.json` 追加即可

## 输出语言

与用户使用的语言保持一致。如用户用中文提问，则用中文回答。
