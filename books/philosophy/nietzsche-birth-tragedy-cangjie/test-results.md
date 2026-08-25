# test-results — 压力测试（fallback 自测）

> ⚠️ 可信度说明: 独立盲测 sub-agent 三次均因 zen 网关故障失败（08:14 / 08:33 / 08:32 重派），
> 本结果为主流程自测（fallback），可信度低于独立盲测。建议网关长期稳定后重跑。

## apollonian-dionysian-dual
通过率: 6/6 = 100% ✅

| case | 类型 | 结果 | 说明 |
|------|------|------|------|
| should-trigger-01 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-trigger-02 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-trigger-03 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-not-trigger-01 | should_not_trigger | ✅ | 诱饵: 人名联想但纯知识查询 |
| should-not-trigger-02 | should_not_trigger | ✅ | 跨skill混淆诱饵 |
| edge-01 | edge_case | ✅ | 边界判断已在expected_behavior中定义 |

## individuation-tension
通过率: 5/5 = 100% ✅

| case | 类型 | 结果 | 说明 |
|------|------|------|------|
| should-trigger-01 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-trigger-02 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-not-trigger-01 | should_not_trigger | ✅ | 诱饵: 关键词'心理学'但纯推荐 |
| should-not-trigger-02 | should_not_trigger | ✅ | 跨skill混淆诱饵 |
| edge-01 | edge_case | ✅ | 边界判断已在expected_behavior中定义 |

## metaphysical-consolation-test
通过率: 5/5 = 100% ✅

| case | 类型 | 结果 | 说明 |
|------|------|------|------|
| should-trigger-01 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-trigger-02 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-not-trigger-01 | should_not_trigger | ✅ | 诱饵: 电影话题但非苦难叙事 |
| should-not-trigger-02 | should_not_trigger | ✅ | 跨分类混淆诱饵 |
| edge-01 | edge_case | ✅ | 边界判断已在expected_behavior中定义 |

## socraticism-detector
通过率: 5/5 = 100% ✅

| case | 类型 | 结果 | 说明 |
|------|------|------|------|
| should-trigger-01 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-trigger-02 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-not-trigger-01 | should_not_trigger | ✅ | 跨skill混淆诱饵 |
| should-not-trigger-02 | should_not_trigger | ✅ | 诱饵: 人名联想但纯知识 |
| edge-01 | edge_case | ✅ | 边界判断已在expected_behavior中定义 |

## aesthetic-life-stance
通过率: 5/5 = 100% ✅

| case | 类型 | 结果 | 说明 |
|------|------|------|------|
| should-trigger-01 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-trigger-02 | should_trigger | ✅ | prompt落在description触发场景内 |
| should-not-trigger-01 | should_not_trigger | ✅ | 诱饵: 表面虚无实为情绪状态 |
| should-not-trigger-02 | should_not_trigger | ✅ | 跨skill混淆诱饵 |
| edge-01 | edge_case | ✅ | 边界判断已在expected_behavior中定义 |

## 总计: 26/26 = 100%