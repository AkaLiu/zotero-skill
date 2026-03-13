# Zotero Skill — 基于本地 Zotero 的 RAG 文献助手

一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex](https://openai.com/index/introducing-codex/) Skill，通过 Zotero 本地 API 将你的个人文献库接入 LLM，形成**本地 RAG（Retrieval-Augmented Generation）**工作流：

> 检索（Retrieval）：从 Zotero 本地库中搜索、定位文献及 PDF 全文
> 增强（Augmentation）：将论文元数据与 PDF 内容注入 LLM 上下文
> 生成（Generation）：基于真实文献内容进行摘要、分析、对比等任务

所有数据均留在本地，不依赖任何云端向量数据库。Zotero 桌面端即是你的知识库，LLM 即是你的分析引擎。

支持平台：**Claude Code** (Anthropic) 和 **Codex** (OpenAI)。

## 功能

- 搜索文献（关键词 / 集合 / 标签）
- 查看论文元数据（标题、作者、摘要、DOI 等）
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
