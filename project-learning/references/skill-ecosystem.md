# 可引用的技能生态（Skill Ecosystem / refs）

学习项目/知识库时，可按需调用以下**已安装**技能扩展能力。只引用当前任务需要的 1-2 个，不一次性全部加载。

## 技能搜索与发现（找更多技能/知识，扩展知识库）

- `skill-installer`（.system 内置）：列出/安装精选技能，或从任意 GitHub 仓库安装技能
- `skillsmp-find-install`（已装）：从 SkillsMP 市场搜索技能、对比候选、校验上游仓库、安装到 Codex
- `skill-grep`（已装）：多字段技能搜索引擎，联网检索可复用的技能与工作流

## 代码库理解（project-learning 的补充）

- `acquire-codebase-knowledge`（已装）：结构化摸清代码库，产出架构/技术栈/集成等模板文档
- `project-understanding`（已装）：按 token 预算分层给出仓库全局视图，支持按需放大局部
- `codebase-knowledge-builder`（已装）：把仓库研读结果沉淀为结构化知识产物
- `llm-wiki`（已装，Codex 适配版）：Karpathy LLM-Wiki 模式，把项目理解编译成交叉引用的持久知识库

## 文档/知识库理解（document-learning 的补充）

- `llm-wiki`（已装）：read-first 索引、原子页、交叉引用、矛盾标记——知识库维护与查询范式
- `docx` / `pdf` / `pptx` / `xlsx`（已装）：读取非 Markdown 格式文档

## 深度研究方法论（已装）

- `research`：联网查一手资料（官方文档/源码），不靠二手解读
- `domain-modeling`：领域术语与领域模型澄清
- `grill-with-docs`：文档访谈式提问

## 使用方式

- 流程中按需说“参考 <技能名> 的方法论”或直接调用对应技能
- 需要更专业/领域化的知识时，先用技能搜索类技能（skillsmp-find-install / skill-grep）找到对应技能，再继续学习项目
- 长期沉淀用 llm-wiki：把 ONBOARDING_NOTES.md 的结论编译成交叉引用知识库，供后续检索