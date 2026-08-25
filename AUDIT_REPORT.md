# 全量审计报告（2026-08-25）

## 范围：27个cangjie包 / 118 skills

## 审计方法
1. 结构核查脚本：逐包检查6顶层文件+candidates五路+每skill的frontmatter/B段三子段/test-prompts
2. source_book溯源核查：每skill的frontmatter书名与该包BOOK_OVERVIEW交叉比对
3. 仓库侧复跑：同步后对GitHub工作副本二次扫描

## 发现的问题（按严重度）
### P0 — source_book系统性错位（78处）
- 根因：gen_skill.py生成器的BOOK变量为模块级缓存，跨书调用未刷新→B包skills的source_book写成A包书名
- 波及：15个包（但美丽/十四讲/艾柯/游心/爵士群像/见证/故事大师/二性I II/新丰年等全部中招；韦伯三书/疯癫/萨特/钱穆/悲剧/西西弗因书名短前缀匹配侥幸漏检，实际也错——已一并按BOOK_OVERVIEW重写）
- 修复：78文件按各包BOOK_OVERVIEW重写 ✅

### P1 — version字段缺失（118处）
- gen_skill模板无version行
- 修复：118文件统一补 version: 1.0.0 ✅

### P2 — 顶层文件缺失
- 缺DIGEST×6（疯癫/钱穆/萨特/中国宗教/WSP/新教伦理）：已补最小骨架版并标注待盲审后重写 ✅
- 缺GLOSSARY×1（新教伦理）：已补 ✅

### P3 — 数量<5（17个包）
- 属数量补齐轮范围，暂缓（用户指示先跑盲审+审计）

## 残留风险
- 十四讲包在仓库目录名为fangfalun-shisijiang-cangjie（非标准slug），索引链接需人工核对
- 最小版DIGEST×6质量不达标，列入盲审后重写清单
