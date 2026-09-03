# 海外 Cowork 宏观市场研究数据字典

> 版本：v1.0  
> 基线日期：2026-09-03  
> 适用阶段：宏观基本面与公开用户需求信号研究  
> 上游方案：[海外 Cowork 类产品宏观市场研究执行方案](../docs/superpowers/specs/2026-09-03-overseas-cowork-macro-market-research-design.md)

## 1. 这套数据结构解决什么问题

这套结构用于把四类证据放进可复查、可更新的共同底座：

1. 39 个国家和地区的宏观基本面。
2. AI、数字化与产品供给成熟度。
3. 核心竞品的逐条真实使用反馈。
4. 首梯队国家的公开工作需求信号。

当前不输出首发国家、综合排名或我方制胜能力判断。所有综合评分必须等宏观数据与公开需求小样本完成后再设计，避免先设权重、后找数据。

## 2. 数据文件与主键

| 文件 | 粒度 | 主键/唯一性建议 | 用途 |
|---|---|---|---|
| `02-source-registry.csv` | 一个来源或数据入口一行 | `source_id` | 记录来源的访问方式、可比性、限制和使用边界 |
| `03-country-macro-template.csv` | 一个国家 × 一个指标 × 一个参考期一行 | `country_iso3 + metric_id + reference_year/period` | 宏观基本面、AI成熟度和供给结构 |
| `04-competitor-feedback-template.csv` | 一条可独立判断的使用反馈一行 | `feedback_id` | 任务、结果、失败、信任、成本与留存信号 |
| `05-country-demand-template.csv` | 一条公开需求信号一行 | `signal_id` | 工作痛点、替代方案、意图和付费信号 |

ID 建议：

- `feedback_id`：`FB-{ISO3或GLB}-{YYYYMMDD}-{6位序号}`。
- `signal_id`：`DS-{ISO3或GLB}-{YYYYMMDD}-{6位序号}`。
- `source_id` 与 `metric_id` 一旦发布不改名；定义发生实质变化时创建新 ID。
- 同一原始内容被多个查询命中时，只保留一条主记录，用 `duplicate_group` 关联。

## 3. 共同元数据规则

### 3.1 时间字段

| 字段 | 格式 | 规则 |
|---|---|---|
| `published_at` | ISO 8601；未知日可写 `YYYY-MM` | 原始内容的公开发布时间 |
| `captured_at` / `accessed_at` | `YYYY-MM-DD` | 实际查看、下载或抓取日期 |
| `reference_year` | `YYYY` | 统计值对应年份，不是下载年份 |
| `period_start` / `period_end` | `YYYY-MM-DD` | 搜索、流量或研究窗口；年度统计可留空 |

不得用“最新”代替具体参考期。不同国家错年时要保留原始年份，后续另做同年化或最近可得值规则。

### 3.2 国家归因

`country_or_region` 与 `country_iso3` 表示证据所对应的用户/市场，不是网站服务器、内容语言或查询参数所在国。

`country_confidence` 统一使用：

- `High`：正文、个人资料或交易上下文明确写出国家/地区。
- `Medium`：本地平台、本地商店 storefront、明确城市/币种/监管语境等多项证据一致。
- `Low`：仅由语言、域名、发布时间或 `regionCode` 等单一弱信号推断。
- `Unknown`：没有可靠定位证据，放入 `Global/Unknown`，不得强行分配。

语言不等于国家。英语、阿拉伯语、德语、葡萄牙语等均可能跨国使用；YouTube 的 `regionCode` 与 `relevanceLanguage` 只影响结果可用性/相关性，不证明用户所在地。

### 3.3 来源等级

| 等级 | 说明 | 典型来源 | 可承担的结论 |
|---|---|---|---|
| S1 | 官方统计或产品事实 | World Bank、ILO、ITU、Eurostat、官方帮助/价格页 | 定义明确的宏观事实、产品可用性与价格时点 |
| S2 | 平台行为或官方/学术研究 | Google Trends、YouTube API、OECD研究、GitHub、HN | 采用热度、搜索与公开行为的代理信号 |
| S3 | 评论、社区或商业估算 | G2、OMR、ITreview、Reclame AQUI、Similarweb | 发现问题和形成假设；不宜单独推断总体规模 |
| S4 | 本研究编码或派生 | 反馈库、需求库、知识工作者推导 | 在输入和公式透明时形成研究指标 |

### 3.4 来源访问状态

- `Ready-API`：已有官方 API，访问条件明确。
- `Ready-Download`：可从官方页面下载结构化文件。
- `Ready-Manual-Export`：需在官方界面手动设定条件并导出。
- `Manual-Review`：只计划人工小样本阅读和编码。
- `Conditional`：需凭证、付费授权、单独许可或先审查条款。
- `Candidate-Validate`：仅是候选，必须先做可用性测试。
- `Reference-Only`：用于说明边界，不作为竞品采集入口。
- `Planned`：由本研究后续产生的数据或人工验证。

公开可访问不等于允许批量抓取。Reddit、评论平台、商店页和本地论坛均先按登记表的访问方式执行；没有明确授权时，不默认做自动化批量采集。

## 4. 国家宏观表字段

`03-country-macro-template.csv` 已预生成 39 国 × 38 个指标，共 1,482 条待填记录。

| 字段 | 必填 | 说明 |
|---|---:|---|
| `country_iso3` / `country_iso2` | 是 | ISO 国家/地区代码；中国香港使用 `HKG/HK` |
| `country_name_cn` / `country_name_en` | 是 | 固定名称，不随来源改写 |
| `region` | 是 | 本研究五大区域分组 |
| `feedback_tier` | 是 | `T1`、`T2`、`T3`；不代表市场评分 |
| `metric_id` / `metric_name_cn` / `dimension` | 是 | 与本数据字典保持一致 |
| `value` | 填数时必填 | 原始数值；不得把 `N/A`、`<1` 等直接转为 0 |
| `unit` | 是 | 使用指标定义中的标准单位 |
| `reference_year` | 是 | 数值对应年份 |
| `period_start` / `period_end` | 视指标 | 搜索、流量或研究窗口必填 |
| `source_id` / `source_url` | 是 | 指向来源登记表，并保存具体数据页/API请求 |
| `accessed_at` | 是 | 下载/访问日期 |
| `direct_or_proxy` | 是 | 直接、代理、派生代理、平台代理、综合代理等 |
| `estimate_status` | 是 | `Observed`、`Estimated`、`Modelled`、`Forecast`、`Derived`、`Unknown` |
| `quality_grade` | 是 | `A`、`B`、`C`、`D`、`Exclude` |
| `coverage_note` | 视情况 | 缺失、错年、地区覆盖或样本说明 |
| `method_note` | 视情况 | 口径映射、派生公式、版本变化或异常处理 |

质量等级建议：

- `A`：首选来源、定义匹配、参考期满足要求、无明显缺失。
- `B`：可信备用来源，或存在轻微错年但定义一致。
- `C`：代理指标、区域口径映射或年份较旧；只能带限制使用。
- `D`：可疑、不可比或缺少关键元数据；仅保留排查。
- `Exclude`：不进入分析。

## 5. 宏观指标体系

38 个指标的逐项定义、单位、首选来源和质量规则已写入工作簿 `Data Dictionary` 工作表。这里给出分组与关键口径。

### 5.1 市场规模与支付能力

- 总人口、GDP、人均 GDP、人均 GNI。
- 劳动力与就业人口。
- 金融账户拥有率和数字支付使用率。
- 新企业密度。

绝对规模类指标后续评分宜使用 `ln(1+x)` 或分位数，避免美国、印度等超大市场淹没其他差异。支付指标优先使用同一 Global Findex 波次，不把调查年数据伪装成年度数据。

### 5.2 知识工作者

本阶段没有全球统一的“知识工作者”官方统计，因此使用 ISCO 职业大类构造透明代理：

- 核心口径：ISCO-08 大类 1 管理人员 + 2 专业人员 + 3 技术人员及助理专业人员。
- 广义口径：核心口径 + 4 文职支持人员。
- 核心人数：`employment_total × knowledge_worker_core_share / 100`。
- 广义人数：`employment_total × knowledge_worker_broad_share / 100`。

要求三项或四项职业数据来自同一统计系列、同一年龄范围、同一性别汇总、同一年份和同一 ISCO 版本。调查值与 ILO 模型估计不得无标记混用。

### 5.3 数字基础与企业数字化

- 互联网使用率、固定宽带、活跃移动宽带、安全互联网服务器密度。
- 企业购买云服务比例。

Eurostat 企业云服务指标只在其统计覆盖区内具备较高横向可比性；非欧盟国家可使用本国官方同义指标，但必须降级为区域内或单国解释，不能硬拼一个全球排名。

### 5.4 AI 成熟度

- 企业 AI 使用率：优先使用 Eurostat 或本国官方调查。
- 生成式 AI 网站人均访问：只作为网页端采用热度代理。
- Claude 国家使用指数：只描述 Anthropic 平台样本。
- OECD、Stanford 等综合指数：只做敏感性分析，不与其底层指标重复加权。

平台流量和单一模型使用数据不得写成“该国总体 AI 使用率”。

### 5.5 产品供给与竞争结构

- 目标产品能否注册、支付并使用核心功能。
- A 层直接竞品可用数量。
- 个人入门月价、币种、含税状态和配额。
- 使用成本可预测性。

官网可访问不等于产品可用。可用性至少需要核对注册、支付、核心 Agent 功能与关键连接器；检查时不得绕过产品的地区限制。

### 5.6 公开需求与反馈派生指标

- 工作型 AI Agent 搜索指数和产品品牌搜索指数。
- 有效公开需求信号数。
- 端到端失败、隐私/授权顾虑、价格/配额顾虑和正向留存信号占比。

Google Trends 的 0–100 是查询批次内的相对值。跨国比较时必须使用统一时间窗、类别、词篮子和锚定词；独立导出的曲线不能直接当成绝对需求量相加。

## 6. 竞品反馈表字段与编码

一条有效反馈必须至少包含：具体产品或工具、可识别的工作任务、实际结果或摩擦。只有情绪、转发、新闻摘要或官网证言不纳入。

核心字段组：

- 来源与定位：`source_type`、`source_name`、`source_url`、时间、国家、置信度和语言。
- 用户上下文：`user_role`、`company_size`、`job_to_be_done`、`trigger`。
- 工作链路：输入/连接器、期望输出、实际结果、成功状态、失败阶段、人工接管。
- 使用体验：耗时、配置难度、可靠性、审批与控制、隐私与信任、价格与配额。
- 替代与留存：当前替代、持续使用、退订或迁移信号。
- 研究质量：证据摘录、纳入状态、重复组和研究备注。

`success_status`：

- `Success`：端到端完成且结果可直接使用。
- `Partial`：完成部分步骤或结果需明显人工修正。
- `Failed`：核心目标未完成、结果不可用或任务中断。
- `Unclear`：原文不足以判断。

摘录只保留支持编码所需的最短片段，并保留原始 URL。不得因为一条反馈命中多个主题而复制成多行。

## 7. 国家公开需求表字段与编码

国家需求库研究的是“用户要完成什么工作以及为什么现有方式不够好”，不是只收集竞品品牌评价。

必须区分：

- `job_to_be_done`：用户希望完成的工作。
- `current_solution`：当前使用的人、软件、模板或手工流程。
- `pain_point`：当前方案的具体摩擦。
- `desired_outcome`：希望改善的速度、质量、成本、控制或协作结果。
- `intent_stage`：从问题认知到购买、使用或迁移的阶段。
- `payment_signal`：预算、询价、订阅、价格敏感或愿付费证据。
- `switching_signal`：明确考虑替换、已替换、退订或回退旧方案。

互动量只保存在 `engagement_metrics`，不能直接代替需求强度；不同平台的点赞、评论和浏览不可直接相加。

## 8. 去重、抽样与编码一致性

### 去重

优先按规范化 URL、平台内容 ID 和文本指纹去重。转载、引用和同一视频的多语言镜像需要归入同一 `duplicate_group`，保留最接近原始来源的一条主记录。

### 抽样

首轮不追求“抓得最多”，而是验证来源能否稳定产出可判定内容。每个国家、产品、来源都要保留查询词、页数、时间窗和筛选过程，以便解释为什么样本量不同。

### 一致性

在正式扩大样本前，两名编码者对同一批至少 30 条内容独立编码；核心主题和成功状态的分歧需要形成例外规则。正式采集后至少抽查 10%。

## 9. 缺失值与异常处理

- 未公布、无法访问、指标不适用和真实的 0 必须区分。
- `value` 留空表示未填或缺失；原因写入 `coverage_note`。
- 源数据显示 `<1`、区间或抑制值时保留原始表示，不擅自填 0。
- 货币统一前保留原币、税和计费周期；转换时另存汇率来源与日期。
- 极端值只在分析副本中做 winsorize 或对数变换，原始表永远保留原值。

## 10. 当前正式来源入口

- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)
- [World Bank Global Findex 2025 下载页](https://www.worldbank.org/en/publication/globalfindex/download-data)
- [World Bank Entrepreneurship Database](https://www.worldbank.org/en/programs/entrepreneurship)
- [ILOSTAT Bulk Download](https://ilostat.ilo.org/data/bulk/)
- [ITU DataHub](https://datahub.itu.int/about/)
- [Eurostat 企业 AI 数据集](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table?lang=en)
- [Eurostat 企业云服务数据集](https://ec.europa.eu/eurostat/databrowser/view/isoc_cicce_use/default/table?lang=en)
- [OECD.AI Trends & Data](https://oecd.ai/en/trends-and-data)
- [Anthropic Economic Index 2026-01](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report)
- [Google Trends CSV 导出说明](https://support.google.com/trends/answer/4365538?hl=en)
- [YouTube Data API `search.list`](https://developers.google.com/youtube/v3/docs/search/list)

来源的可访问性、授权条件与用途边界以 `02-source-registry.csv` 为准。

