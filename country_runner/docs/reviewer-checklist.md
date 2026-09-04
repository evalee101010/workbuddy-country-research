# Gate A / Gate B 审核清单

## Gate A：来源计划

- [ ] 候选平台有本轮当地活跃或产出证据，而非只因配置中出现。
- [ ] A/B/C 各有 Core，或明确 `documented_gap` 与替代执行方案。
- [ ] Core 至少通过两组独立查询，并能保存原文、日期、上下文和 High/Medium 地域证据。
- [ ] 核心语言和当地平台已考虑，不是只看全球英文平台。
- [ ] 匿名公开路径可独立执行；API、登录和付费权限只是增强。
- [ ] Auth-optional、Consent-required、Discovery-only、Reject 没有被误标 Core。
- [ ] GitHub/开发者论坛和迁移走廊来源没有被当作国家大众代表。
- [ ] 已填写批准人、时间、备注和 `approval_status: approved`。

## Gate B：证据审计

所有标题证据和报告直接引语 100% 审核；其余 Included 至少按清单中 `required_review=Yes` 的确定性样本审核。高风险、低置信翻译和边界地域记录应提高到全量。

逐行确认：

- [ ] Evidence ID 唯一，并回链唯一或正确共享的 Content ID。
- [ ] raw 表保留最短必要原话、译文、上下文、URL、日期和抓取时间。
- [ ] 译文未增加原文没有的结果、身份、地点或因果。
- [ ] 国家和一级行政区依据可审计；语言、域名、storefront、频道名、subreddit、`regionCode` 没有被单独用作归国证据。
- [ ] Low/Unknown 地域证据未进入国家标题结论。
- [ ] 角色来自内容/公开资料；不知道就 Unknown，没有为覆盖率补猜。
- [ ] Developer/Technical 样本只在技术附录，或有非开发者来源交叉支持。
- [ ] A 有真实任务与结果；B 有痛点/当前做法/期望；C 没把曝光直接写成需求或效果。
- [ ] 不同平台互动未求和；点击、受众所在地、价格和转化未被推断。
- [ ] 重复 URL、转载、多语言镜像和跨轮内容已处理或说明。
- [ ] 单一来源主题、次国家空白、授权增强缺失进入 WARN/限制说明。

签署时填写 `review_status`、`reviewer`、`reviewed_at`、五个 `*_ok` 字段和必要备注。任何一个必检项不能确认时使用 `Reviewed-block` 或 `Reviewed-warn`，不要勉强 PASS。

## 构建前最终抽查

- [ ] manifest 中 Gate A/Gate B 均为 approved，审核者姓名非空。
- [ ] `gaps-and-biases.md` 与主报告限制一致。
- [ ] 随机抽三条标题证据完成 Evidence → Content → 原话 → URL 回链。
- [ ] XLSX 十个工作表齐全；阿语/日语/葡语/中文、换行和 URL 显示正常。
- [ ] `validation_warn` 的 WARN 不妨碍交付，但必须可见。
- [ ] 确认这是可冻结版本；后续修订将创建新 run。
