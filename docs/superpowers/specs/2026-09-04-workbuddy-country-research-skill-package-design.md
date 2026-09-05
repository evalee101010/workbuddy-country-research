# WorkBuddy 逐国公开信号研究 Skill 打包设计

日期：2026-09-04  
状态：已完成口头方案确认，待书面确认后实施

## 1. 背景与目标

现有工作区已经具备 `country_runner`、10 个首梯队国家配置、CSV 模板、研究 SOP、自动校验，以及 UAE 和 Saudi 的实跑数据。下一步需要把这些能力封装成可分发的 Codex Skill，让多位同事以“一人一国”的方式并行采集。

每位同事只需指定国家、执行人和研究截止日，Skill 即可引导并执行当地渠道发现、查询矩阵生成、A/B/C 三条证据流采集、去重、结构校验和 ZIP 导出。

本阶段的交付目标是完整、可合并的原始国家数据包，不生成国家洞察、机会排序、市场评分、政策结论或产品策略。

## 2. 已确认的产品决策

- 所有执行同事均使用 Codex/Cowork。
- 基本分工单元为“一位同事独立负责一个国家”，不设计同一国家的多人实时协作。
- 采用自包含的 Codex Skill，而不是依赖共享仓库路径的薄封装。
- 每国只交付标准化原始数据包，不自动生成内部探索性总结。
- 当前用途为内部探索，不要求 Gate B 独立逐条签字。
- 不把 Gate B 状态伪装为通过；未来对外引用或高风险决策时可重新启用严格审核。
- “尽量全”限定为记录查询矩阵内的全部合格唯一命中，不代表平台全站抓取或统计代表性抽样。

## 3. 交付形态

实施完成后提供四项交付物：

1. 可安装的 `workbuddy-country-research` Codex Skill 文件夹。
2. 可直接转发给同事安装的 Skill ZIP。
3. 一页式启动说明。
4. `merge-country-packs` 国家数据包合并工具。

UAE 与 Saudi 作为参考样例保留，但不会成为新国家初始化时的数据种子，也不会复制到其他国家结果。

## 4. Skill 结构

```text
workbuddy-country-research/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── research-protocol.md
│   ├── country-channel-adaptation.md
│   ├── evidence-field-contract.md
│   └── package-handoff-contract.md
├── scripts/
│   ├── workbuddy-country-runner
│   ├── merge-country-packs
│   └── package-country-run
└── assets/
    ├── config/
    │   ├── countries/
    │   └── global/
    ├── schemas/
    └── templates/
```

`SKILL.md` 只包含触发条件、模式选择、核心流程和必须遵守的边界。详细研究协议、当地渠道适配方法、字段定义和交包规范放入按需读取的 references。确定性的初始化、校验、打包与合并逻辑放入 scripts；国家配置、全局 codebook、schema 和空白模板放入 assets。

## 5. 同事使用入口

推荐自然语言入口：

> 使用 WorkBuddy Country Research 跑德国，执行人 Anna，研究截至今天。

Skill 解析并确认三个必填参数：

- 国家名称或 ISO2。
- 执行人名称。
- 研究截止日。

run ID 默认由研究截止日和国家生成，并允许用户显式指定。输出根目录默认为当前工作区下的 `research/runs/<ISO2>/<run-id>/`；不得把运行结果写入 Skill 安装目录。

## 6. 执行流程

### 6.1 初始化

Skill 加载已有国家配置。若国家尚无配置，则先生成配置草案，至少包含：

- 核心语言、探索语言和迁移走廊语言。
- 一级行政区与主要城市。
- 主流非开发者人群。
- 工作任务家族。
- Cowork/相似产品及当地别名。
- 公开访问和国家归因注意事项。

配置是查询起点，不是研究结论。新配置需要执行同事确认国家、语言和行政区信息后才能进入采集。

### 6.2 当地渠道发现

每国均扫描以下来源族，但不会强制使用同一批平台：

1. 全球产品社区和技术社区。
2. 当地 AI、专业和行业社区。
3. 当地主流社交、问答、图文、短视频和职业平台。
4. 当地自由职业、服务交易、投诉、评价、App 商店和 SaaS 目录。
5. 外籍人士、侨民和迁移走廊社区。

GitHub、开发者论坛和硬核 AI 社区最多作为技术补充，不得单独支撑大众需求结论。

### 6.3 渠道适配与来源计划

执行同事不等待管理者 Gate A。Skill 对候选来源进行小规模 pilot，并根据以下证据自动建议角色：

- `Core`：可公开/合规访问，至少两组查询有稳定产出，可保存原话、上下文、日期和 High/Medium 地域依据，并包含主流工作任务。
- `Supplement`：产量有限但提供独特人群、地域、语言或内容字段。
- `Discovery-only`：只能发现创作者、机构、话题或线索，不能形成内容级证据。
- `Reject`：访问、地域、原话、时间窗或受众明显不满足要求。

执行同事可以调整建议角色，但必须填写理由。某条证据流没有 Core 时允许继续，前提是写明 `documented_gap`。

### 6.4 查询矩阵

Skill 按“来源 × 语言 × 人群 × 任务 × 产品 × 次国家地区”生成和执行矩阵：

- A：产品名/别名 + 具体工作任务 + 使用结果/问题词，收集 Cowork 和相似产品的真实反馈。
- B：具体工作任务 + 当前办法/痛点/需求词，不要求出现产品名。
- C：工作结果/任务 + 教程、模板、课程、导师、服务等内容和承接词。

每条查询均保存查询文本、语言角色、目标人群、任务家族、地域范围、结果检查数、有效结果数、状态和备注。零命中、重复密集和访问受限查询必须保留。

### 6.5 原始内容与证据编码

`raw-discovery-log.csv` 一条底层公开内容一行。只摘录支持判断的最短必要原话，不复制整篇帖子、完整评论区或完整字幕。

A/B/C 表一行代表一个可独立判断的证据单元，并通过 `content_id` 回链 raw 表。同一内容可以进入多个证据流，但同一句话、同一任务不得为增加主题数量而重复计数。

必须保留：

- 原话、中文译文、内容语言。
- item URL、来源、作者别名、发布日期与抓取日期。
- 国家/地区、一级行政区、地域依据和置信度。
- 人群角色、技术层级和来源偏差。
- 查询 ID、发现轮次、Included/Candidate/Excluded。

不得推断未公开的职业、居住地、价格、点击、收入、受众位置或效果。分类站和招聘内容中的姓名、电话、邮箱不得写入数据包。

### 6.6 停止规则

先执行预先登记的核心查询矩阵，再进行增量查询。只有同时满足以下条件，才可将当前公开检索框标记为暂时完成：

- 核心来源、语言、人群、任务、产品和次国家探针均已执行并记录。
- 连续两个增量批次没有新增合格唯一内容。
- 连续两个增量批次没有新增任务家族、人群或关键反例。

达到时间或查询预算时标记 `budget_limited`；匿名替代已尽但其余来源需要登录、授权或同意时标记 `access_limited`；算法只返回有限排序结果时标记 `ranking_limited`。任何停止标签均不代表统计代表性。

### 6.7 内部数据校验和导出

本阶段不执行 Gate B 人工签字。导出前只运行确定性的结构与证据完整性校验。

硬错误包括：

- 重复或空白的 Content/Evidence/Query ID。
- Evidence 无法回链 raw。
- Included 证据缺失原话、URL、来源或必要地域依据。
- 表头/schema 不一致。
- 文件缺失或 manifest 与实际条数不一致。

WARN 包括：

- 单一来源主题。
- 非精确发布日期。
- 次国家空白。
- KOL/KOC 互动量缺失。
- `ranking_limited`、`access_limited`、`budget_limited`。

硬错误必须修复后才能导出；WARN 写入限制说明但不阻止内部数据包生成。

## 7. 国家数据包结构

```text
research/runs/<ISO2>/<run-id>/
├── 00-run-manifest.yml
├── 01-country-context.md
├── 02-source-discovery.csv
├── 03-channel-fit-pilot.csv
├── 04-source-plan.yml
├── 05-collection-funnel.md
├── evidence/
│   ├── raw-discovery-log.csv
│   ├── A-competitor-feedback.csv
│   ├── B-local-work-needs.csv
│   └── C-kol-koc-content.csv
├── queries/
│   ├── A-competitor-queries.csv
│   ├── B-local-needs-queries.csv
│   └── C-kol-koc-queries.csv
├── quality/
│   ├── coverage-matrix.csv
│   ├── gaps-and-biases.md
│   └── structural-validation.json
└── package-manifest.json
```

导出文件名：

```text
workbuddy-country-data-<ISO2>-<run-id>.zip
```

该 ZIP 只包含一个国家 run、package manifest 和必要的 schema 版本信息，不包含 Skill 代码、其他国家样例或生成观点。

## 8. Package Manifest 与可合并契约

`package-manifest.json` 至少记录：

- 国家 ISO2/ISO3、run ID、执行人和研究窗口。
- schema、配置、codebook 和 runner 版本。
- A/B/C、raw 和 query 的行数。
- 来源、语言和地域覆盖摘要。
- 完整性标签和已知缺口。
- 包内文件清单、字节数和 SHA-256。

所有 CSV 使用 UTF-8 和固定表头。`content_id`、`evidence_id` 与 `query_id` 必须包含国家代码和 run 内唯一序号。

`merge-country-packs` 的流程为：

1. 校验 ZIP、package manifest、schema 版本和文件哈希。
2. 校验国家/run 主键和表头一致性。
3. 分别合并 raw、A、B、C、queries、sources 和 coverage 表。
4. 检查跨包 ID 冲突。
5. 根据 canonical URL 和平台内容 ID 标记跨国重复，但不自动删除。
6. 输出合并表、国家包索引和合并告警报告。

跨国重复内容可能代表区域内容、迁移走廊或搜索串流，因此必须保留原国别归因和 `cross_scope_duplicate_id`，交由后续分析阶段判断。

## 9. 异常与访问边界

- 无预置国家配置：先生成并确认配置草案。
- 国家无法归因：保留在 raw，标为 `Candidate/Unresolved`，不进入国家 A/B/C。
- 某证据流无合格 Core：以 `documented_gap` 交包，不降低证据门槛。
- 页面需要登录、被 robots 限制或私域可见：记录限制并停止，不绕过访问控制。
- 动态列表不能稳定分页：记录查询深度和 `ranking_limited`，不宣称全站抓取。
- 抓取中断：保留已完成批次和查询状态，重新运行只追加新内容，不覆盖既有 raw。
- Schema 版本不同：合并工具停止并报告，不静默映射字段。
- 文件或哈希损坏：拒绝合并并指明具体文件。

## 10. 验收方案

### 10.1 Skill 验证

- 使用 Skill Creator 的 `quick_validate.py` 检查命名、frontmatter、UI metadata 和未完成占位符。
- 在全新临时目录安装 Skill，验证自然语言触发和资源路径不依赖原工作区。

### 10.2 Runner 回归

- 现有 Runner 全部单元测试继续通过。
- 新增内部探索模式、package manifest、ZIP 与合并工具的测试。
- 验证脚本只写入显式输出目录，不修改 Skill 安装目录。

### 10.3 双国家冒烟测试

用两个隔离测试国家夹具完成：

1. 初始化。
2. 写入来源、查询、raw 和 A/B/C 示例。
3. 运行结构校验。
4. 生成 ZIP。
5. 解压并重新校验哈希和条数。

### 10.4 合并测试

- 合并两个不同国家、相同 schema 的包并核对总行数。
- 检查阿语、中文及其他 Unicode 内容无乱码。
- 构造一个跨国 canonical URL 重复，确认只标记、不自动删除。
- 构造 ID 冲突、schema 不一致和哈希损坏，确认工具明确拒绝。

## 11. 非目标

本次打包不包含：

- 自动生成国家市场洞察、场景优先级或产品建议。
- 国家评分、宏观基本面和政策研究。
- 统计代表性抽样或需求渗透率估算。
- 登录/API/付费渠道集成。
- 私域群抓取。
- 同一国家多人实时合并。
- 对外材料所需的 Gate B 独立证据审计。

## 12. 完成标准

满足以下条件即认为打包完成：

- 同事可在不拥有原始工作区的情况下安装 Skill。
- 一条自然语言请求能初始化任一已配置国家 run。
- 未配置国家可以生成可确认的配置草案。
- 数据采集按国家自适应选择渠道，并保存全部查询状态与最短必要原话。
- 结构校验能区分硬错误和内部可接受 WARN。
- 每国可生成带 manifest 和哈希的标准 ZIP。
- 两个国家 ZIP 可被合并工具无损合并。
- UAE/Saudi 样例不会污染新国家数据。
- 自动测试、Skill 验证和双国家冒烟测试全部通过。
