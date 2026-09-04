# 海外 Cowork 公开需求信号 Country Runner 设计

> 文档状态：用户已复核确认，可进入实施规划<br>
> 版本：v1.0<br>
> 日期：2026-09-03<br>
> 上游基线：[海外 Cowork 类产品宏观市场研究执行方案](./2026-09-03-overseas-cowork-macro-market-research-design.md)<br>
> 实施边界：本文件只定义公开用户需求信号与 KOL/KOC 内容信号工作流，不包含宏观基本面、政策、综合评分、首发国家选择或我方制胜能力分析

## 一、目标与成功标准

本项目把已经在 UAE 试跑的公开信号研究整理为一套可交给团队逐国执行的 Country Runner。它要让不同研究员在不同国家使用当地适配的平台，仍能产出字段一致、证据可回溯、偏差可披露的国家反馈包。

第一版预配置十个首梯队国家：

- 美国 `USA`
- 英国 `GBR`
- 德国 `DEU`
- 日本 `JPN`
- 新加坡 `SGP`
- 印度尼西亚 `IDN`
- 印度 `IND`
- 巴西 `BRA`
- 阿联酋 `ARE`
- 沙特阿拉伯 `SAU`

成功标准：

1. 同事可用统一入口初始化、试跑、校验并构建任一预配置国家包。
2. 每个国家先发现和验证当地渠道，不要求所有国家使用相同平台。
3. 每个国家包同时呈现三条证据线：竞品实际使用反馈、当地工作需求、KOL/KOC 内容与商业承接；如果某条线没有合格证据，保留空白章节并说明已经执行的查询和缺口，不能省略或以弱证据填充。
4. 每条正式证据可以回到原始原话、原语言、译文、URL、日期和地域归因依据。
5. 普通知识工作者是主报告核心；开发者和技术社区不会主导国家需求结论。
6. 缺少登录权限、API 或付费数据只影响增强字段，不阻塞匿名公开路径。
7. 国家包可以被后续地区、语区和迁移走廊研究复用，并能跨轮去重。

## 二、非目标

第一版不做：

- 宏观经济、就业、AI 成熟度或竞争供给数据采集。
- 隐私、数据跨境、支付和监管政策研究。
- 国家综合评分、首发市场推荐或进入顺序判断。
- Work Buddy 或新产品的优势、定位、产品路线和增长策略判断。
- 登录后封闭社区、私域群或禁止自动访问平台的静默批量抓取。
- 对所有平台开发专用爬虫，或承诺全自动完成研究判断。
- 用公开样本估计总体渗透率、市场份额或精确需求规模。

## 三、核心设计原则

### 3.1 统一证据协议，不统一平台

跨国统一以下内容：

- 字段定义和枚举。
- 原始证据保留方式。
- 国家、次国家、地区和语区归因规则。
- 渠道试跑维度和渠道角色。
- 主流人群覆盖要求。
- 质量门、缺口披露和冻结条件。

跨国不统一以下内容：

- 平台清单。
- 每个平台的样本配额。
- 每个国家的总样本条数。
- 语言数量或次国家样本的等量分布。
- 不同平台点赞、评论、浏览量的绝对比较。

### 3.2 先按目标人群和任务构建证据组合，再选择平台

研究重点是面向非技术或轻技术知识工作者的 Cowork 类产品，不是开发者工具市场。国家包按以下人群分层：

| 层级 | 目标人群 | 在交付中的位置 |
|---|---|---|
| 主流 | 求职者、普通办公室工作者、市场/销售、运营/行政/HR、自由职业者/创作者、小企业主 | 国家主报告核心 |
| 进阶 | 使用 AI 办公、模板、无代码和轻量自动化的业务用户 | 进阶工作流章节 |
| 技术补充 | 开发者、技术创业者、GitHub 和开发者论坛用户 | 技术附录；不得单独支撑主流结论 |

GitHub、开发者论坛和硬核 AI 社区可以补充集成、自动化、隐私、安全和高级工作流，但不计入主流人群最低覆盖。只有当同一需求也出现在非开发者来源，或其工作任务本身不依赖开发者身份时，才可上升为国家主报告主题。

### 3.3 原始发现与研究编码分层

系统保存两个层级：

1. `raw-discovery-log.csv`：以 `content_id` 标识一项底层公开内容，保留当时看到的原文、译文、链接、查询和上下文，只追加、不覆盖。
2. A/B/C 编码表：以 `evidence_id` 标识一个可以独立判断的任务、结果、需求或商业承接单元，并通过 `content_id` 回链原始内容。

一项底层内容可以包含多个确实不同的证据单元，例如一段视频同时描述工作任务和一个付费模板 CTA；这些单元共享 `content_id`，但分别获得 `evidence_id`。同一句话或同一任务不能为了进入多个主题或证据线而重复生成证据。研究员摘要 `evidence_excerpt` 不能替代 `original_text`。同一内容被多个查询、国家轮或地区轮命中时，只保留一个主内容记录，通过重复组和跨轮 ID 关联，不复制成多个独立来源。

ID 规则：优先用平台原生内容 ID 生成稳定 `content_id`；没有原生 ID 时使用 canonical URL 指纹。`evidence_id` 在一个 `content_id` 内按可独立编码单元生成，冻结后不重排。平台原生 ID、URL 或内容合并发生变化时，通过 alias/duplicate 字段关联，不修改已发布 ID。

## 四、总体流程

```text
全局基线
  ├─ Cowork 竞品范围和别名
  ├─ 共同数据字典与代码本
  ├─ 全局候选渠道库
  └─ 公共访问与合规边界
          ↓
Country Config
  ├─ 国家/地区代码与次国家结构
  ├─ 查询语言及语言角色
  ├─ 主流用户角色与工作任务
  ├─ 当地平台种子和发现关键词
  └─ 匿名路径与可选授权路径
          ↓
Local Source Discovery
          ↓
Country Channel Fit Pilot
          ↓
Gate A：人工批准 Source Plan
          ↓
三线正式采集：A 竞品反馈 / B 当地需求 / C KOL-KOC
          ↓
Gate B：证据、地域、受众、翻译、去重和覆盖审核
          ↓
Build & Freeze Country Pack
          ↓
全部国家完成后，再跑地区 / 语区 / 迁移走廊轮
```

## 五、模块边界

### 5.1 Global Baseline

全局基线由以下独立资产组成：

- `product-catalog.yml`：A/B/C/D 层产品、别名、官网和观察任务。
- `channel-catalog.yml`：全球渠道家族、典型平台、访问状态和默认偏差。
- `codebook.yml`：工作任务、角色、成功状态、失败阶段、CTA 和商业承接枚举。
- `quality-rules.yml`：必填字段、质量门、抽查和冻结规则。
- `templates/`：各阶段 CSV、Markdown 和工作簿模板。

全局资产只提供种子和共用定义，不能替代国家渠道发现。

### 5.2 Country Config

每个国家一个配置文件，至少包含：

| 配置组 | 内容 |
|---|---|
| 身份 | ISO2、ISO3、中英文名、时区、货币 |
| 查询语言 | 核心查询语言、发现语言、翻译目标语言、罗马化/混写规则 |
| 地域 | 国家称呼、城市、州/省/酋长国等一级行政区、常见地区别名 |
| 受众 | 主流角色、进阶角色、明确不应主导的技术人群 |
| 任务词库 | 简历、邮件、演示、表格、研究、营销、客服、行政、小企业运营等当地表达 |
| 产品词库 | Cowork 直接竞品、相邻工具、当地常用产品和别名 |
| 渠道种子 | 全球平台、本地候选平台、侨民/迁移走廊候选平台 |
| 访问策略 | 匿名公开路径、可选 API/登录路径、禁止或需同意的访问方式 |
| 研究参数 | 时间窗、每批查询预算、饱和判断批次、抽查比例 |
| 区域映射 | 所属地区、语区和潜在迁移走廊；仅供后续轮次使用 |

配置内的平台只是候选，不因写入配置就自动成为正式来源。

UAE 配置必须同时处理国家和七个酋长国线索，并覆盖英语、阿拉伯语以及对目标工作人群有实际意义的其他语言查询。确认内容属于 UAE 不等于确认其属于 Dubai；具体酋长国没有可靠证据时写为 `Unknown`。

### 5.3 Local Source Discovery

每个国家的 Channel Fit Pilot 前增加一次当地渠道发现扫描，覆盖五类来源：

1. 全球技术和产品社区：如 GitHub Issues/Discussions、Stack Exchange、Hacker News、Product Hunt。
2. 当地 AI、开发者和专业社区：当地语言技术站、AI 论坛、公开活动讨论、行业社区。
3. 当地主流社交与内容平台：短视频、图文、问答、博客、职业社交及当地“小红书类”应用。
4. 当地投诉与评价平台：本地消费者投诉站、App 商店、本地 SaaS 目录和评论站。
5. 侨民与迁移走廊社区：海外华人内容、外籍人士论坛、公开 Telegram/WhatsApp 频道等。

每个候选来源写入 Source Discovery Registry：

```text
source_id
country_iso3
source_name
source_url
source_family
local_role
local_activity_evidence
audience_profile
query_languages
source_native_geo_granularity
candidate_evidence_streams
access_status
public_access
machine_access
auth_or_rights
extractable_fields
freshness_window
main_bias
pilot_status
researcher_note
```

GitHub 默认属于全球技术信号。只有正文、作者公开资料、项目语境或其他可审计证据明确指向某国时，才进入国家正式包，否则保留为 `global_unknown`。

小红书及类似平台是否代表当地需求取决于当地使用人群。海外华人内容通常先标为 `migration_corridor` 或 `diaspora` 信号；若没有额外证据，不能直接代表当地居民。

私域群、登录后封闭社区和禁止自动访问的平台不做静默抓取。它们可以标为 `Consent-required` 招募渠道或 `Auth-optional` 人工观察渠道。

### 5.4 Country Channel Fit Pilot

试跑对候选来源做有限查询和小样本审核，评价：

- 公开或授权可访问性。
- 当地有效内容产出。
- 原文、日期和上下文可保存性。
- 国家或次国家归因能力。
- 主流工作场景的信息密度。
- 公开互动或传播字段可用性。
- 平台、商业和人群偏差。
- 团队能否重复执行。

渠道输出角色：

| 角色 | 定义 |
|---|---|
| `Core` | 可重复产生该国有效证据，访问边界明确，可承担正式采集 |
| `Supplement` | 有效但样本较窄、较少或偏差较强，用于补角色、语言或场景 |
| `Discovery-only` | 适合发现产品、作者和议题，正式编码必须回到可追溯原始来源 |
| `Auth-optional` | 获得登录/API/付费权限时增强，缺失不阻塞国家包 |
| `Consent-required` | 只用于合规招募或经同意的人工观察 |
| `Reject` | 无法回源、地域误导、活跃度过低、访问风险过高或信息密度不足 |

`Core` 必须同时满足：访问方式无阻塞、至少两组独立查询能产生有效发现、国家归因可达 High/Medium、原文和日期可保存。默认试跑检查每个候选渠道前 20 个相关结果；如果平台形态不支持排名结果，使用两个等量时间批次。产出少但独特的渠道可以列为 `Supplement`，不能为了达标加入低质量内容。

Gate A 通过条件：

- A/B/C 每条证据线至少有一个 `Core` 来源，或明确记录“暂无 Core 来源”的缺口和替代执行方案。
- 每个正式来源已记录访问状态、允许用途、受众偏差和地域能力。
- 已考虑当地语言与当地平台，而不只是全球英文平台。
- 已确认匿名公开路径可执行。
- 人工批准 `04-approved-source-plan.yml` 后，正式采集才可继续。

## 六、三条证据线

### 6.1 A：竞品实际使用反馈

有效记录必须包含：具体产品、可识别工作任务、实际结果或摩擦。只有情绪、转发、新闻摘要或官网证言不计入。

专属字段：

```text
product
product_tier
job_to_be_done
trigger
input_or_connected_tools
expected_output
actual_result
success_status
failure_stage
manual_interventions
time_or_latency
setup_difficulty
reliability
control_and_approval
privacy_and_trust
pricing_or_usage_limit
current_alternative
retention_churn_or_switching_signal
sentiment
```

### 6.2 B：当地工作需求和痛点

B 线不要求出现具体产品名，回答用户要完成什么工作、当前如何解决、哪里不够好，以及是否出现购买或迁移意图。

专属字段：

```text
audience_role
technical_level
company_size
work_task
job_to_be_done
current_solution
pain_point
desired_outcome
trigger
tool_or_product
intent_stage
payment_signal
switching_signal
mainstream_fit
sentiment
```

`technical_level` 使用：`Non-technical`、`No-code-capable`、`Technical`、`Developer`、`Unknown`。`mainstream_fit` 使用：`Main-report`、`Advanced-workflow`、`Technical-appendix`、`Unclear`。

### 6.3 C：KOL/KOC 内容、传播与商业承接

C 线同时观察什么工作场景获得传播，以及内容如何承接到模板、课程、咨询、服务或产品。公开播放量、点赞、评论和粉丝量是传播代理，不等于需求强度、购买量或产品效果。

专属字段：

```text
creator_name
creator_type
audience_profile
content_format
content_title
content_hook
work_scene
visible_metrics_raw
views_visible
likes_visible
comments_visible
shares_visible
clicks_visible
followers_visible
metric_captured_at
platform_query_context
within_query_rank
within_query_percentile
cta_type
cta_url
offer_type
offer_name
offer_price_original
offer_currency
funnel_stage
commercial_interest
commercial_bias
```

CTA 和承接物至少区分：无 CTA、关注/订阅、免费模板、付费模板、课程、社群、1:1 咨询、代运营/服务、联盟链接、产品注册、其他。只有公开可见的报价才填写价格；不得把未知价格记为免费。

不同平台的互动数不直接相加。只有在同一平台、同一查询和相近时间窗内，才可以计算排名或分位数；原始数值和抓取日期始终保留。`clicks_visible` 只有在平台公开展示真实点击数时才填写，不能用播放、点赞或链接存在推算点击量。

### 6.4 共同证据底座

每条 `Included` 证据至少包含：

```text
content_id
evidence_id
legacy_record_id
run_id
evidence_stream
source_id
source_type
source_name
source_url
item_url
author_alias
published_at
published_at_raw
date_confidence
captured_at
query_id
query_language
content_language
original_text
original_text_translation_cn
context_note
country_iso3
country_or_region
admin1_name
admin1_confidence
city_name
geo_evidence
country_confidence
scope_level
scope_name
discovery_round
source_native_geo_granularity
country_assignment_status
origin_market
destination_market
cross_scope_duplicate_id
audience_role
technical_level
source_audience_bias
duplicate_group
inclusion_status
review_status
researcher_note
```

原文只保存支撑编码所需的最短必要片段和必要上下文，不复制整篇文章、完整评论区或完整视频字幕。`legacy_record_id` 用于保留既有 `feedback_id`、`signal_id` 或 `sample_id`；新数据以 `content_id + evidence_id` 为正式主外键。

`scope_level` 允许：`country`、`subnational`、`region`、`language_zone`、`migration_corridor`、`global_unknown`。语言、域名、平台 storefront 或查询参数不能单独证明用户所在地。

## 七、单国运行目录与命令

### 7.1 目录契约

```text
runs/{ISO2}/{YYYY-MM-DD}/
├── 00-run-manifest.yml
├── 01-country-context.md
├── 02-source-discovery.csv
├── 03-channel-fit-pilot.csv
├── 04-approved-source-plan.yml
├── queries/
│   ├── A-competitor-queries.csv
│   ├── B-local-needs-queries.csv
│   └── C-kol-koc-queries.csv
├── evidence/
│   ├── A-competitor-feedback.csv
│   ├── B-local-work-needs.csv
│   ├── C-kol-koc-content.csv
│   └── raw-discovery-log.csv
├── review/
│   ├── evidence-audit.csv
│   ├── coverage-matrix.csv
│   └── gaps-and-biases.md
├── output/
│   ├── country-feedback-pack.md
│   └── country-feedback-pack.xlsx
└── 99-change-and-freeze-log.md
```

`00-run-manifest.yml` 记录国家配置版本、研究时间窗、执行者、审核者、代码本版本、阶段状态、匿名/授权路径状态、输入文件哈希和冻结时间。运行可以恢复，但冻结后的 evidence 和 output 不原地覆盖；更新必须创建新 run 或新版本。

阶段状态固定为：`initialized`、`discovery_ready`、`source_plan_pending`、`source_plan_approved`、`collection_in_progress`、`validation_pass`、`validation_warn`、`validation_block`、`frozen`。命令只能执行允许的相邻状态转换；人工批准和冻结都要记录操作者与时间。

### 7.2 命令契约

团队入口统一为：

```bash
./country-runner init AE
./country-runner discover AE
./country-runner pilot AE
./country-runner validate AE
./country-runner build AE
```

行为：

- `init`：校验国家配置并创建运行目录、manifest 和空模板。
- `discover`：生成当地渠道发现清单与多语言查询包，合并人工登记结果。
- `pilot`：汇总渠道试跑指标，生成 Source Plan 草案并停在 Gate A。
- `validate`：执行字段、URL、日期、地域、翻译、重复、受众偏差和覆盖检查，输出 Gate B 报告。
- `build`：只有 Gate A 已批准且 Gate B 没有 `BLOCK` 时，生成 Markdown/XLSX 并写入冻结日志。

当一个国家只有一个未冻结 run 时，命令可默认使用它；存在多个未冻结 run 时必须拒绝执行并要求传入 `--run-id`，避免多人并行时写错目录。任何命令失败都不得删除或覆盖已有原始数据。

`validate` 第一次运行生成或更新审计清单；审核者完成抽查并填写签署字段后再次运行，Runner 才能给出最终 `validation_pass` 或 `validation_warn`。未签署或仍有必改项时保持 `validation_block`。

### 7.3 自动化与人工边界

脚本负责：

- 创建目录、模板和查询清单。
- 合并结构化导出或人工录入文件。
- 标准化日期、枚举和 ID。
- 检测缺失、重复、坏链接格式和明显归因冲突。
- 计算渠道产出、覆盖矩阵、平台内互动排序和质量状态。
- 渲染国家反馈包和工作簿。

研究员负责：

- 发现当地平台和当地表达。
- 判断公开访问与使用边界。
- 阅读上下文、保存必要原话并翻译。
- 判断地域证据、受众身份、真实任务和商业偏差。
- 编码 A/B/C 专属字段。
- 在质量不足时记录缺口，而不是补造或放宽证据。

审核者负责：

- 批准 Source Plan。
- 复核所有标题结论引用的证据。
- 按抽查规则复核其余 Included 行。
- 处理编码分歧并批准冻结。

## 八、质量门与停止规则

### 8.1 Gate B 状态

`validate` 对每个检查项输出 `PASS`、`WARN` 或 `BLOCK`。

| 检查面 | PASS | WARN，可交付但必须披露 | BLOCK，不得冻结 |
|---|---|---|---|
| 来源与权限 | 来源角色、访问方式和匿名路径已登记 | API/登录增强字段缺失 | 来源不可追溯或访问边界违规 |
| 原始证据 | Included 行有原话、链接、日期和上下文 | 非标题证据只有月级日期或互动字段不全 | 标题证据缺原话/链接，或译文无法回到原文 |
| 地域归因 | 国家结论由 High/Medium 证据支持 | 一部分只可保留为区域或未知 | 仅凭语言、域名或 storefront 强行归国 |
| 受众偏差 | 主流非开发者角色有覆盖，技术样本独立标识 | 某些角色、行业或次国家区域为空 | 主要国家结论由开发者渠道单独支撑 |
| 三角验证 | 主要主题由不同来源家族或证据线互证 | 单一来源主题标记待验证 | 把播放量、KOL 宣称直接写成需求规模或效果 |
| 人工复核 | 标题证据全量复核，其余按规则抽查 | 一致性问题已记录并限制外推 | 机器提取、翻译或编码未经人工审核进入结论 |

冻结条件：所有检查项无 `BLOCK`；`WARN` 已进入 `gaps-and-biases.md` 和主报告限制说明；审核者在 manifest 签署批准。

主流覆盖的默认 `PASS` 基线是：Country Config 中列出的每个核心角色和任务家族都已经执行查询，且合格证据至少覆盖三个不同的主流角色家族、四个非开发者工作任务家族和两个来源家族。已完成规定查询但有效公开内容不足时记 `WARN`；没有执行主流查询，或用技术样本替代主流覆盖时记 `BLOCK`。国家配置可以提高这一基线，但不能降低。

### 8.2 人工审核比例

- 每个代码本大版本正式扩量前，两名编码者对至少 30 条混合 A/B/C 内容独立编码并解决分歧。
- 每个国家的所有标题结论和直接引语由审核者 100% 复核。
- 其余 `Included` 行至少随机抽查 10%；高风险来源、低置信翻译和边界地域记录提高到全量复核。
- 分歧形成明确例外规则并进入代码本版本记录，不能只改最终结论。

角色只能由内容、公开作者语境或可审计资料判断，不能仅凭平台推断。无法判断时使用 `Unknown`，不得为了达到覆盖基线补猜角色。

### 8.3 覆盖而非固定样本量

国家包不设置全球统一的总条数门槛。`coverage-matrix.csv` 至少显示：

- A/B/C 三条证据线的来源家族、查询语言和有效产出。
- 主流、进阶和技术补充人群覆盖。
- 主要工作任务和角色覆盖。
- 国家、次国家、地区、语区和迁移走廊粒度。
- 正向、负向、失败、付费、迁移和反例覆盖。
- High/Medium/Low/Unknown 地域证据分布。

如果某项为空，保留为空并解释；不能用技术社区、弱地域内容或低质量评论填满。

### 8.4 停止规则

每条证据线先完成 Gate A 批准的核心来源、核心语言和查询家族，然后分批继续。满足任一条件即可停止：

1. 连续两批没有出现新的主要工作任务、主流角色或会改变当前结论的关键反例。
2. 达到 Country Config 预先设定的时间或查询预算。
3. 剩余候选来源全部为 `Auth-optional`、`Consent-required` 或 `Reject`，且匿名替代路径已穷尽。

停止不等于“数据充分”。报告必须同时写出实际产出、饱和判断、预算约束和未覆盖项。

## 九、错误处理、恢复与可重复性

### 9.1 错误分级

- `INFO`：可选字段缺失、授权增强不可用、平台无公开点击量。
- `WARN`：来源产出低、单一来源主题、次国家覆盖不均、翻译或日期置信度较低。
- `BLOCK`：配置无效、必填原始证据缺失、国家归因冲突、重复 ID、未通过访问边界、Gate 未签署。

### 9.2 恢复规则

- 每个阶段完成后更新 manifest，不依赖终端会话状态。
- 自动生成文件先写到 run 内的临时路径，验证后再替换对应的未冻结派生文件。
- 原始发现日志只追加；修正通过状态字段、替代记录和 change log 表达。
- 同一命令在输入未变化时产生相同派生结果和稳定 ID。
- 外部页面失效时保留 URL、捕获时间、最短必要原文和失效状态，不伪造重新访问结果。

### 9.3 去重

优先使用平台内容 ID 和 canonical URL；其次使用作者、发布日期、标题和文本指纹。转载或多语言镜像放入同一 `duplicate_group`，以最接近原始来源的一条为主记录。

`cross_scope_duplicate_id` 在国家、次国家、地区、语区和迁移走廊轮之间保持稳定，避免同一内容被多轮累加。

## 十、地区、语区与迁移走廊轮

所有首轮国家包完成后，再启动独立 Region Runner。地区轮不是把国家 CSV 简单合并，而是：

1. 导入并锁定已冻结国家包，保留原 `run_id` 和国家粒度。
2. 使用地区、语区或走廊原生关键词新增查询，例如 `GCC`、`MENA`、`Arab world`、`Arabic-speaking web`。
3. 对国家轮和区域轮执行跨轮去重。
4. 保留来源真实粒度；`regional_only` 没有额外国家证据时不得下放。
5. 迁移内容同时保存 `origin_market` 和 `destination_market`。
6. 输出角色、任务、语言、渠道和证据覆盖模式，不按原始条数给国家排名。

`GCC`、`MENA`、`Middle East`、`Arab world` 和 `Arabic-speaking web` 不是同义词。Region Config 必须保存每个来源自己的区域定义。

地区轮复用同一证据底座和 Gate B，另增加 `region_definition`、`included_countries`、`excluded_countries` 和 `country_assignment_status` 审核。

## 十一、国家反馈包结构

`country-feedback-pack.md` 固定包含：

1. 研究范围、运行版本、日期和置信边界。
2. 当地渠道地图与 Source Plan。
3. A：竞品实际使用任务、结果、失败、成本、信任和迁移。
4. B：主流角色的工作任务、现有方案、痛点、期望和付费/切换信号。
5. C：KOL/KOC 高传播场景、内容钩子、公开互动和 CTA/商品承接。
6. 主流、进阶和技术补充人群的差异。
7. 跨证据线互证的主要主题。
8. 反例、矛盾证据和不应外推的发现。
9. 地域、语言、渠道、角色和次国家覆盖矩阵。
10. `WARN`、数据缺口、授权缺口和下一轮建议。
11. 引用索引，可回到原始证据 ID 和 URL。

标题不得写成精确市场规模判断。没有代表性抽样时，使用“公开信号中出现”“在本次来源组合中反复出现”等边界清晰的表达。

## 十二、与现有资产的兼容与迁移

现有文件不原地废弃：

- `research/01-data-dictionary.md` 继续作为全项目共同口径，后续补充 Runner 新字段。
- `research/04-competitor-feedback-template.csv` 映射到 A 线。
- `research/05-country-demand-template.csv` 映射到 B 线。
- UAE `04-raw-feedback.csv` 中已有的 `original_text` 和 `original_text_translation_cn` 原样保留。
- UAE `16-kol-uae-multichannel-samples.csv` 映射到 C 线；缺失的新字段保持空值并在迁移日志说明，不反推或补造。
- 现有 UAE 试跑结果导入新 run 时创建迁移 manifest 和字段映射，不覆盖旧文件。

Country Runner 第一版新增 C 线正式模板、Source Discovery Registry、Country Config、质量规则和渲染结构。现有宏观研究模板与 Runner 解耦。

## 十三、第一版实施范围

第一版实现：

- 模块化目录和统一命令入口。
- 十国 Country Config 初始版本。
- 全局产品、渠道和代码本种子。
- Source Discovery、Channel Fit Pilot、A/B/C、审核和覆盖模板。
- 查询包生成、CSV 结构校验、ID/日期/枚举标准化、去重提示、质量门、Markdown/XLSX 渲染。
- UAE 旧试跑数据的非破坏性迁移验证。
- 匿名公开路径的完整演示。

第一版不实现大规模自动爬虫。平台采集通过公开搜索、人工页面复核、允许的结构化导出和可选 API 适配器完成。后续只有在访问权、价值和维护成本明确时，才单独为高价值渠道增加适配器。

## 十四、验收与测试

### 14.1 配置测试

- 十个国家配置都能通过 schema 校验。
- ISO、语言、次国家和区域映射无冲突。
- 每国存在匿名公开路径、主流角色和非开发者任务词库。

### 14.2 命令测试

- `init` 能创建完整目录且不会覆盖已有 run。
- `discover` 和 `pilot` 能在没有 API 凭证时运行。
- Gate A 未批准时，正式 build 被阻止。
- 存在 Gate B `BLOCK` 时，build 被阻止。
- 输入不变时重复 validate/build 结果稳定。

### 14.3 数据测试

- 缺原话、URL、日期、地域证据或审核状态的 Included 行被正确阻止或降级。
- 语言不等于国家；storefront 不等于居民国家。
- 同一 URL、多语言镜像和跨轮内容能被提示去重。
- 开发者来源不能单独生成主流国家结论。
- KOL 互动数据不会跨平台直接相加。

### 14.4 端到端验收

使用 UAE 完成一次非破坏性端到端运行：

1. 读取 UAE 配置并生成 run。
2. 导入现有试跑和 KOL/KOC 样本。
3. 补齐 Source Discovery 与 Source Plan。
4. 执行质量门并显示真实 WARN/缺口。
5. 生成 Markdown 和 XLSX 国家包。
6. 每个标题结论能通过 ID 回到原始原话和 URL。
7. 冻结后重复 build 不改写已冻结输出。

UAE 验收通过后，再复制到其他九国；不在第一轮同时批量正式采集十国。

## 十五、最终交付物

完成第一版实现后，团队将得到：

1. Country Runner 使用说明和五条核心命令。
2. 十国可编辑 Country Config。
3. 全局产品、渠道、代码本和质量规则。
4. 各阶段 CSV/Markdown/XLSX 模板。
5. UAE 端到端示例包。
6. 匿名路径和可选授权路径说明。
7. 数据字典、字段映射、审核手册和常见错误处理。
8. 后续 Region Runner 的输入输出契约；具体自动化在国家流程稳定后单独实施。

这套交付的目标不是替代研究员判断，而是把判断发生的位置、证据要求、错误边界和交付格式固定下来，使团队能够按国家逐一执行并持续修订。
