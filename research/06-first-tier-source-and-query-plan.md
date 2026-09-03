# 首梯队 10 国来源与检索起步方案

> 版本：v1.0  
> 日期：2026-09-03  
> 国家：美国、英国、德国、日本、新加坡、印度尼西亚、印度、巴西、阿联酋、沙特阿拉伯  
> 当前用途：来源可行性与小样本试采集，不是正式规模化抓取方案

## 1. 本轮目标

在正式填宏观数据和批量收集公开反馈前，用一轮可控的小样本回答五个问题：

1. 每类来源能否稳定访问、导出或通过官方 API 获取？
2. 每个国家用什么语言和本地表达，才能找到真实工作需求而非 AI 新闻？
3. 哪些来源能产生“任务—过程—结果”完整反馈？
4. 国家、用户角色、公司规模和付费信号能否可靠判断？
5. 哪些来源、检索词或编码字段需要在扩大样本前修改？

这一步只验证研究方法，不比较国家高低。中东市场已进入首梯队，阿联酋和沙特与其他八国执行同样的试采集标准，同时允许如实记录“公开样本稀疏”。

## 2. 执行顺序

```text
0. 固定产品名、任务词、失败词、付费词和排除词
                         ↓
1. 10国宏观来源可用性检查 ─────┐
                                ├─ 并行
2. 10国公开反馈/需求小样本试采 ─┘
                         ↓
3. 复核国家归因、重复率、有效率和编码一致性
                         ↓
4. 修订来源表、词篮子、配额和字段
                         ↓
5. 再进入正式宏观填数与公开需求采集
```

## 3. 统一检索架构

每个国家均组合五类词，不依赖一个笼统的 “AI agent” 查询：

### 3.1 产品词

- Claude Cowork
- ChatGPT agent
- Manus
- Genspark / Super Agent
- Perplexity Comet / Computer
- Work Buddy
- B 层办公套件产品词，用于验证替代关系

产品别名、旧名称、当地常用音译或无空格写法应写入查询日志。

### 3.2 任务词

围绕非技术或泛知识工作者的真实任务：

- research / information collection
- report / document / presentation / spreadsheet
- email / calendar / meeting follow-up
- data entry / reconciliation / invoice / expense
- browser operations / form filling / application
- customer support / sales operations / ecommerce operations
- file organization / local computer tasks
- cross-app workflow / recurring task

每个国家需要把任务词翻译成本地自然表达，而不是只做机器直译。

### 3.3 体验与失败词

- review / experience / worth it
- failed / stuck / stopped / wrong / unreliable
- slow / latency / queue
- permissions / privacy / security / data residency
- price / credits / limits / subscription / refund
- cancel / churn / switched / alternative

### 3.4 意图词

- how to automate / looking for / recommend
- compare / alternative / replacement
- buy / subscribe / pricing / budget
- use for my team / small business / enterprise

### 3.5 排除词

根据误报率逐步维护：招聘、投资新闻、纯模型基准、AI agent 开发教程、加密货币 agent、游戏 agent、房地产 agent 等。开发者反馈可进入 D 层参照池，但不得混入普通办公用户统计。

## 4. 统一来源优先级

### 4.1 宏观基本面

1. World Bank、ILOSTAT、ITU、Global Findex 等国际官方来源。
2. Eurostat：德国及欧洲市场的企业 AI/云服务可比数据。
3. 各国官方统计：只在国际源缺失或需要细分时补充。
4. OECD、Anthropic、Stanford 等研究：作为 AI 采用交叉验证，不替代主口径。

### 4.2 公开用户反馈与需求

1. 应用商店、扩展商店、官方社区和 GitHub Issues 中描述具体任务的内容。
2. 当地语言 YouTube 实测及其公开讨论。
3. Google Trends 的固定词篮子和关联查询。
4. Reddit、Hacker News 等社区；国家不足时进入 `Global/Unknown`。
5. G2、Capterra、OMR、ITreview、Reclame AQUI 等平台，只做人工或授权小样本。

官网客户证言、厂商案例、新闻转载、SEO 榜单和联盟营销文章只用于发现产品或核对事实，不计入用户反馈。

## 5. 10 国起步方案

| 国家 | 语言 | 宏观主源 | 公开反馈/需求主源 | 本地来源候选 | 起步查询 |
|---|---|---|---|---|---|
| 美国 | 英语 | WDI、ILOSTAT、ITU、Findex、OECD/Anthropic交叉 | Google Trends、YouTube API、GitHub、HN、Reddit（条件）、商店人工 | G2/Capterra人工或授权 | `AI agent for work`、`AI assistant complete tasks`、`[product] review/failed/worth it` |
| 英国 | 英语 | WDI、ILOSTAT、ITU、Findex、OECD | Google Trends、YouTube、Reddit（条件）、商店人工 | 英国商业社区后续验证 | `AI agent for admin work`、`automate office tasks AI`、`[product] UK review/GDPR concern` |
| 德国 | 德语+英语 | WDI、ILOSTAT、ITU、Eurostat AI/Cloud、Findex | Google Trends、YouTube、OMR Reviews人工、商店人工 | G2德语页、当地论坛待验证 | `KI Agent für die Arbeit`、`KI Assistent Büro Erfahrungen`、`[Produkt] Probleme/Kosten/Datenschutz` |
| 日本 | 日语+英语 | WDI、ILOSTAT、ITU、Findex、日本官方统计补充 | Google Trends、YouTube、ITreview人工、商店人工 | 日本商务/技术论坛待验证 | `AIエージェント 仕事`、`AIアシスタント 業務 自動化`、`[製品] 評判/料金/問題` |
| 新加坡 | 英语为主，华语/马来语探测 | WDI、ILOSTAT、ITU、Findex、OECD | Google Trends、YouTube、Reddit（条件）、商店人工 | 本地科技/创业社区待验证 | `AI agent for work Singapore`、`AI assistant for SME Singapore`、`automate operations AI` |
| 印度尼西亚 | 印尼语+英语 | WDI、ILOSTAT、ITU、Findex、国家统计补充 | Google Trends、YouTube、商店人工 | KASKUS仅做≤20条可行性测试 | `agen AI untuk kerja`、`asisten AI kerja`、`otomatisasi pekerjaan dengan AI`、`[produk] ulasan/harga/masalah` |
| 印度 | 英语+印地语探索 | WDI、ILOSTAT、ITU、Findex、国家统计补充 | Google Trends、YouTube、Reddit（条件）、商店人工 | 印度SaaS/创业社区待验证 | `AI agent for work India`、`office automation AI India`、`[product] pricing India`、`काम के लिए AI एजेंट` |
| 巴西 | 葡萄牙语+英语 | WDI、ILOSTAT、ITU、Findex、国家统计补充 | Google Trends、YouTube、Reclame AQUI人工、商店人工 | 当地SaaS/创业社区待验证 | `agente de IA para trabalho`、`assistente de IA produtividade`、`[produto] avaliação/problemas/preço` |
| 阿联酋 | 英语+阿语，必要时印地语/乌尔都语探测 | WDI、ILOSTAT、ITU、Findex、国家统计补充 | Google Trends、YouTube、Reddit（条件）、商店人工 | UAE/Dubai商业与创业社区待验证 | `AI agent for work UAE`、`AI assistant Dubai SME`、`وكيل ذكاء اصطناعي للعمل`、`[product] privacy UAE` |
| 沙特阿拉伯 | 阿语+英语 | WDI、ILOSTAT、ITU、Findex、国家统计补充 | Google Trends、YouTube、商店人工、Reddit（条件） | 当地技术/创业社区待验证 | `وكيل ذكاء اصطناعي للعمل`、`مساعد ذكاء اصطناعي للأعمال`、`أتمتة العمل بالذكاء الاصطناعي`、`[المنتج] تجربة/سعر` |

完整的国家偏差、归因规则和初始配额也已写入工作簿 `Query Plan` 工作表。

## 6. 首轮小样本配额

配额不是为了形成统计代表性，而是为了判断来源有效性。

### 6.1 竞品反馈

- 美国、英国、德国、日本、印度、巴西：每个 A 层产品 × 每个有覆盖的核心来源，最多先取 20 条可判定反馈。
- 新加坡、印度尼西亚、阿联酋、沙特：每个 A 层产品目标 15 条；公开内容不足时不跨国补齐，记录稀疏本身。
- B 层产品不按全部产品铺开；每国先选 2 个办公生态相关产品，每个最多 20 条，用于理解替代关系。
- C 层先不按国家铺满；每类抽 2 个产品，验证配置、模板、稳定性和成本主题。

### 6.2 国家需求信号

- 每国先选择 8–12 个本地任务词组合。
- 每个词在每个平台最多查看/取得前 50 个结果。
- 目标是每国形成 80–150 条去重后的候选内容；最终有效量可能更低。
- Google Trends 每国至少保留一组统一英文锚定词和一组本地语言词，参数完整记录。

### 6.3 来源上限

任何单一平台不应超过该国有效样本的 40%，以降低平台人群和情绪偏差。若某国公开来源过少，可以突破，但必须标记 `coverage_note`，且不得与覆盖充分国家直接比较总量。

## 7. 来源可行性检查表

每个来源先记录以下结果，再决定是否扩大：

| 检查项 | 记录内容 |
|---|---|
| 访问状态 | 可访问、需登录、需API key、需许可、被限制、不可用 |
| 结构化程度 | API、CSV/XLSX、稳定网页、动态网页、纯人工 |
| 可用字段 | 标题、正文、日期、评论、用户信息、国家、互动量 |
| 国家可判定率 | High/Medium/Low/Unknown 的占比 |
| 任务可判定率 | 能否还原 JTBD、过程和结果 |
| 重复率 | 多查询、多平台转载或同内容重复比例 |
| 有效率 | 符合纳入标准的记录/候选记录 |
| 法律与条款 | 是否允许自动访问、研究或商业使用；是否需要授权 |
| 稳定性 | 翻页、速率、排序、登录态、页面结构是否稳定 |
| 结论 | 扩大、保留人工、仅作发现、暂停 |

Reddit 目前标记为 `Conditional`：应先确认 Data API 条款、用途和速率；不把网页公开视为批量抓取授权。Apple App Store Connect 和 Google Play Developer 的评论 API 面向有权限的自有 App，不是竞品评论接口。

## 8. 国家归因与跨国比较

### 8.1 归因优先顺序

1. 用户或正文明确写出国家/城市。
2. 当地平台、当地商店、当地货币或明确监管语境，多证据一致。
3. 用户主页、频道介绍或公司位置。
4. 查询地区、语言、域名等弱信号。
5. 无证据：`Global/Unknown`。

不能因为德语、日语、葡语或阿语就自动归入德国、日本、巴西或某个中东国家。阿联酋尤其需要区分“内容在迪拜发布”“区域总部账号”和“实际使用者位于阿联酋”。

### 8.2 分母与呈现

正式比较时至少同时报告：

- 原始有效记录数。
- 每个平台/语言的构成。
- 每百条候选中的有效率。
- 可判定国家和角色的比例。
- 按人口或核心知识工作者标准化后的信号数，仅作为辅助。

不把跨平台点赞相加，不把搜索指数、评论数和网页流量混成一个未经校准的“需求总分”。

## 9. 试采集通过标准

一个“国家 × 来源”组合满足以下条件，可进入正式采集：

- 访问方式与条款边界明确。
- 至少取得 20 条候选内容，或能够证明该来源本就稀疏。
- 有效率达到 20%，或对某个关键主题具有不可替代价值。
- 关键字段可稳定提取，不依赖大量主观猜测。
- 重复率可控，能保存原始 URL、日期和查询参数。
- 国家归因能够分级，而不是全部被强制归国。

以下情况暂停或只保留人工发现用途：

- 需要绕过登录、验证码、地区限制或技术保护。
- 使用条款不明确且计划用途可能超出普通浏览。
- 内容大多是营销、新闻或无任务细节的情绪表达。
- 国家归因、发布日期或原文无法稳定保存。
- 同一来源在三轮查询中有效率持续低于 5%。

## 10. 试采集结束后的必做复盘

输出一页方法复盘，不做市场排名，至少回答：

1. 哪些指标在 10 国均有一致来源，哪些需要区域口径？
2. 哪些产品在各国实际上没有公开反馈或不可用？
3. 每国最有效的 5 个任务词和 5 个问题词是什么？
4. 哪些平台产生了最多具体任务，哪些只是情绪或营销？
5. 国家归因的 High/Medium/Low/Unknown 分布如何？
6. 语言、本地平台和产品可用性造成了哪些系统偏差？
7. 数据字典、来源登记表、配额和编码手册需要怎么改？

复盘确认后，才启动两条正式研究线：宏观基本面填数与公开用户需求信号收集。

## 11. 首轮正式入口

- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)
- [ILOSTAT Bulk Download](https://ilostat.ilo.org/data/bulk/)
- [ITU DataHub](https://datahub.itu.int/about/)
- [Global Findex 2025](https://www.worldbank.org/en/publication/globalfindex/download-data)
- [Eurostat 企业 AI 数据集](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table?lang=en)
- [Google Trends 导出说明](https://support.google.com/trends/answer/4365538?hl=en)
- [YouTube Data API `search.list`](https://developers.google.com/youtube/v3/docs/search/list)
- [GitHub REST Search API](https://docs.github.com/en/rest/search/search)
- [Hacker News API](https://github.com/HackerNews/API)
- [Reddit Data API Terms](https://redditinc.com/policies/data-api-terms)
- [OMR Reviews](https://omr.com/en/reviews)
- [ITreview](https://www.itreview.jp/)
- [Reclame AQUI](https://www.reclameaqui.com.br/)

所有入口的状态、偏差和使用限制以 `02-source-registry.csv` 为准；“候选”不等于已批准批量获取。

