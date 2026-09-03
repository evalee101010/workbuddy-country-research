# 阿联酋竞品反馈示意包

> Pilot country：United Arab Emirates（ARE）  
> 采集日期：2026-09-03  
> 目的：验证公开渠道能否取得可追溯的 Cowork 类竞品反馈，以及各渠道实际能覆盖哪些研究字段。  
> 本包不是阿联酋市场规模、满意度或偏好统计。

## 1. 为什么先选阿联酋

阿联酋适合拿来做中东第一轮压力测试：官方语言是阿拉伯语，但英语和其他语言也被广泛使用。官方资料还列出印地语、乌尔都语、马拉雅拉姆语等语言入口，因此不能用“阿语市场”代替“阿联酋市场”。本轮以阿语和英语为核心检索语，印地语与乌尔都语仅测试渠道产出，马拉雅拉姆语列入观察清单。语言依据见 [UAE Government Fact Sheet](https://u.ae/en/about-the-uae/fact-sheet) 与 [UAE investment destination](https://u.ae/en/information-and-services/business/the-uae-an-ideal-investment-destination)。

国家归属与内容语言分栏记录：

- `country_iso3=ARE` 表示要研究的国家单位。
- `query_language` 表示用什么语言检索。
- `content_language` 表示内容本身的语言。
- `geo_evidence` 表示为什么认为这条内容属于阿联酋。
- `country_confidence` 决定这条记录可以支持多强的国家结论。

任何阿语内容、`.ae` 页面、`regionCode=AE`、UAE App Store storefront 或本地社区发帖都不自动等于阿联酋用户。未来 Saudi Arabia、Qatar、Kuwait、Bahrain、Oman 等国家必须分别建立 ISO3、国家锚点与语言组合，不能合并成一个“中东/阿语”样本池。

## 2. 本轮竞品范围

目标发现池包括：

- 直接 Cowork / agent workspace：Claude Cowork、Manus、Genspark。
- 浏览器执行型：Perplexity Comet。
- 相邻对照：ChatGPT、Perplexity 一般产品体验，以及账单/客服等商业系统反馈。

实际进入编码表的产品由证据决定。本轮拿到可编码记录的主要产品是 Genspark、Manus 和 Perplexity Comet；Perplexity 的两条账单/客服记录只作为相邻样本。Claude Cowork 虽发现阿语内容，但没有足够的 UAE 地理证据，因此没有强行纳入。

## 3. 样本漏斗

| 层级 | 数量 | 说明 |
|---|---:|---|
| 公开发现记录 | 20 | 保留纳入、排除、错国、错语种、编辑内容和应转入 05 的需求信号 |
| 可编码记录 | 13 | 能识别产品、任务或商业链路、实际结果/摩擦 |
| High geo | 7 | 来源资料明确显示 AE，或正文明确自述 Dubai/UAE；身份未独立核验 |
| Low/Medium geo 假设 | 6 | 来自 UAE App Store，或叠加未验证的 `dxb/uae` 昵称线索 |
| Core Cowork | 11 | 直接 agent/workspace/browser-agent 任务或关键执行/成本链路 |
| Adjacent | 2 | 账单、退款或客服链路，不与核心任务成功率合并 |

## 4. 文件结构与阅读顺序

1. `07-pilot-findings.md`：先看渠道结论、字段覆盖与正式扩样建议。
2. `02-source-feasibility.csv`：每个渠道的公开可访问性、机器访问条件、权利边界和推荐用途。
3. `03-query-log.csv`：复现检索词、国家锚点、窗口、候选数、编码数与漏检/串国问题。
4. `04-raw-feedback.csv`：20 条发现层记录，保留排除与分流原因。
5. `05-coded-feedback.csv`：13 条结构化反馈，覆盖任务、链路、结果、失败、成本、信任和迁移。
6. `06-dimension-coverage.csv`：各渠道能拿到哪些字段，按 0–3 评分。
7. `01-country-language-scope.csv`：本国语种、关键词与国家锚点。
8. `08-codebook.csv`：国家置信度、Cowork 范围、成功状态与 04/05 分流规则。

同目录外的整合工作簿 `outputs/01a064d5-0ee8-7482-8ace-77518f64e0fa/uae-competitor-feedback-pilot.xlsx` 包含全部表、公式汇总、渠道对比和审计说明。

## 5. 使用边界

- 本轮是渠道小样本，不计算“UAE 用户中有多少人遇到某问题”。
- Trustpilot 的 `AE` 是平台展示的资料国家，不代表本研究独立验证了用户身份。
- Apple UAE storefront 只证明页面入口，不证明评论作者的常住地。试跑中甚至发现正文明确出现 Afghanistan 的评论，说明 storefront 不能作为国家强证据。
- Reddit 仅做搜索引擎发现与人工小样本阅读；没有把“公开可见”理解成可以未授权批量抓取。规模化前按 [Reddit Data API Terms](https://redditinc.com/policies/data-api-terms) 重新评估用途与许可。
- 表中的 `evidence_excerpt` 是研究员短转述，原始 URL 才是复核入口。

## 6. 正式扩样前的门槛

1. 决定是否只把 High geo 计入国家核心样本，Medium 仅作敏感性分析。
2. 两名编码者先对同一批至少 30 条记录独立编码，补充冲突规则。
3. 为每个 `product × channel × query_language` 设置最低检索页数和停止条件，而不是要求同样条数。
4. 先跑完 English/Arabic 的渠道产出，再决定 Hindi/Urdu/Malayalam 是否值得设配额。
5. 任何需要凭证或批量访问的平台，先完成条款、API 和授权评估。

