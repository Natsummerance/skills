# 对比报告 — 旧流水线 vs cangjie-skill 流水线
## 对象: 《悲剧的诞生》（同一语料 nietzsche_birth.txt）

### 产出规模

| 维度 | 旧流水线（books/philosophy/） | cangjie 流水线（本目录） |
|------|------|------|
| skill 数 | 1（nietzsche-birth-tragedy，5.7KB） | 5（每个 4–6KB） |
| 结构 | When to Use / 核心命题8条 / E / B / 相关 / 审计 | R(原文引用) / I(方法论骨架) / A1(书内案例) / A2★(触发场景+语言信号+相邻区分) / E(完成标准+判停) / B(反场景+失败模式+盲点) + test-prompts.json |
| 触发设计 | description 一句话含触发词 | 每skill独立A2段：3场景+3语言信号+相邻区分；test-prompts 含2类诱饵 |
| 质量门 | 引文溯源（真实性） | 三重验证(V1跨域/V2预测力/V3独特性) + 压力测试 + 审计轨迹(candidates/rejected保留) |

### 关键差异

1. **原子度**: 旧版1个skill承载全书 → 单点触发、description过载。cangjie拆成5个原子，各管一个决策场景，trigger互不抢。
2. **可测试性**: cangjie的test-prompts.json（darwin兼容）让「skill是否会被正确激活」变成可回归验证的问题。旧版无此机制。
3. **反例驱动**: cangjie专设counter-example-extractor——B段「不要在什么情况用」来自书中警告的失败模式（欧里庇得斯理性化、歌剧文化），旧版的边界段是蒸馏者自拟。
4. **批判前置**: cangjie阶段0强制Adler批判（时代局限/立场盲点/未证假设），直接成为B段素材；旧版批判靠蒸馏者自觉。

### 各自优势（诚实评估）

**旧流水线更好处**:
- 单文件自足，加载成本低（一个skill读完即懂全书）
- 「核心命题」式结构对哲学书更贴——尼采的价值恰在命题群而非操作清单

**cangjie更好处**:
- 5个skill分别服务5个真实调用场景（作品分析/文化诊断/悲剧判准/理性化检测/生存姿态），互斥清晰
- 诱饵测试防误触发——部署到agent后稳定性可控
- candidates/rejected审计轨迹可回溯「为什么这个没做成skill」

### 结论

- **哲学原典类**: 建议**混合策略**——cangjie的5个原子skills做agent日常调用的「手」，旧版单skill做「地图」（理解全书的入口）。
- **实操方法论类书**（如穷查理宝典型）: cangjie全面占优，原子化+压力测试价值最大。
- 后续书籍默认走 cangjie 流水线；旧版不再新增但全部保留。

### 遗留
- [ ] zen网关恢复后重跑独立sub-agent盲测（当前为fallback自测26/26）
- [ ] 其余23本已蒸馏书的cangjie重蒸馏排队（按用户指令逐步推进）
