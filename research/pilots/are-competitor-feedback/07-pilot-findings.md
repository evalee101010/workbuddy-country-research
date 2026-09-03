# 阿联酋竞品反馈渠道试跑结论

## 一句话结论

公开层面可以跑通“搜索发现 → 原页复核 → 国家证据判断 → 反馈编码”的小样本流程，但没有一个渠道同时满足高产量、高地理可信度、高任务细节和可无条件批量抓取。当前最稳的组合是：**Trustpilot 做高置信国家样本，App Store 做主题发现，Reddit 做低量深描，官方 API/产品页负责访问边界与事实校验。**

## 1. 哪些渠道能顺利取得什么数据

| 渠道 | 本轮结果 | 可取得的主要维度 | 国家归属 | 正式使用建议 |
|---|---|---|---|---|
| Trustpilot | 7 条发现、6 条编码、6 条 High geo | 资料国家、日期、评分、任务、结果、价格/积分、退款/客服、迁移与留存 | 强于其他渠道，但只是平台资料国家 | 第一核心渠道；人工采样，按作者+日期定位并记录选择偏差 |
| Apple App Store UAE | 7 条发现、6 条编码、0 条 High geo | 昵称、日期、评论、任务、失败、credits、替代品和流失 | 弱；storefront 不等于作者所在地 | 主题发现池；Low/Medium 样本不计入国家核心结论 |
| Reddit | 3 条发现、1 条编码、1 条 High geo | 正文地理自述、完整任务链、环境上下文、替代订阅、留存和互动 | 逐条变化；明确自述 Dubai 时很强 | 低量深描；人工发现，批量使用前审查 API 条款 |
| Google Play | 1 条阿语候选、0 条 UAE 编码 | 评论、评分、语言、产品问题、credits | 弱；阿语/界面参数不是国家 | 进入 Global-Arabic 主题池，等待额外地理证据 |
| YouTube | 发现阿语 Cowork 内容，API 未跑 | 视频与评论文本、日期、互动、长篇工作流 | 弱；`regionCode` 只影响检索 | 有 key 后试跑评论命中率，不把检索地区当作者国家 |
| GitHub | API 入口可用，0 条目标反馈 | 版本、复现、错误阶段、技术环境、维护状态 | 极弱 | 只对有官方 repo/issues 的产品启用 |
| Product Hunt | 0 条 UAE 样本 | 发布、早期评论、定位、替代品 | 弱 | 用于全球新品/定位，不做国家反馈主入口 |
| G2/Capterra | 未找到稳定 UAE 入口 | 理论上可取得角色、公司规模、行业、优缺点 | 可能中等 | 二轮验证产品覆盖、国家筛选和授权条件 |

对应的真实来源例子包括：不看评分、只看任务与结果的 [Genspark Trustpilot UAE 资料样本](https://ca.trustpilot.com/review/genspark.ai?page=3)、包含应用构建和积分锁定的 [Manus Trustpilot 样本](https://es.trustpilot.com/review/manus.im)、明确自述居住 Dubai 并描述 Comet 本地购物研究流程的 [Reddit Comet 帖子](https://www.reddit.com/r/perplexity_ai/comments/1nf6r5e/comet_browser_the_automatic_ai_browser_from/)，以及能稳定看到任务与 credits 主题、却无法证明作者国别的 [Genspark UAE App Store 评论页](https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews) 和 [Manus UAE App Store 评论页](https://apps.apple.com/ae/app/manus-ai-agent-automation/id6740909540?platform=iphone&see-all=reviews)。

## 2. 实际能编码到哪些反馈维度

本轮不是只保存“好评/差评”，而是验证下列字段是否能从公开内容中取得：

- 用户上下文：角色、个人/公司规模、是否创始人或付费订阅者。
- Job to be done：高层演示、PPT、表格、CRM dashboard、应用构建、设计文件打包、透明背景 logo、邮件和本地购物研究。
- 工作链路：输入材料、连接器/数据环境、预期产物、实际产物、失败阶段与人工重试。
- 体验结果：成功、部分成功、失败；是否直接可用、是否需要补救。
- 成本系统：订阅、credits/tokens、失败仍扣费、月度限额、退款和取消后继续扣费。
- 信任与控制：是否能判断扣费、是否有人工客服、系统何时披露能力限制、是否出现未经预期的续费/扣费。
- 替代与留存：改用 ChatGPT、取消 Higgsfield、保留 Gemini、取消大多数其他 AI 订阅、因历史投入而被锁定。
- 本地化：阿语输出错误与价格感知；本轮只形成假设，尚未得到足够 High geo 样本支持。

最稳定的字段是产品、结果/摩擦、价格/credits 和迁移信号；最缺失的是公司规模、真实行业、详细连接器、精确耗时和审批链。G2/Capterra 理论上能补用户画像，但本轮尚未验证稳定入口。

## 3. 高置信样本里出现了什么主题

7 条 High geo 样本里出现了以下可行动信号，但数量太小，不能解释为 UAE 总体占比：

- 正向工作流：短时限高层演示；创始人把演示、表格、CRM 和内容集中到同一 workspace；Comet 用本地天气、电商和促销条件做购物研究。
- 生产失败：Genspark 多次尝试仍无法交付 ZIP 下载和透明背景 logo，失败过程继续消耗 credits。
- 商业系统风险：Manus credits 退款不到账并形成迁移锁定；Perplexity 取消后继续扣费、缺少人工支持。
- 替代和留存都很强：既有取消其他工具、把 Genspark/Comet 纳入日常工作流，也有因成本、可靠性或账单问题考虑离开。

这些主题的价值是告诉下一轮要重点问什么、继续抓什么，不是告诉我们问题在 UAE 有多普遍。

## 4. 为什么 04/05 正式模板不能只是一张简单表

试跑证明需要把两层数据分开：

1. **Raw discovery 层**：保留被排除、错国、错语种、编辑文章以及应转入 05 的需求信号，否则无法审计检索偏差。
2. **Coded evidence 层**：只有通过国家证据与内容门槛的记录，才展开任务、链路、结果、成本、信任和迁移字段。

因此此前的 `04-competitor-feedback-template.csv` 更像“最终编码表骨架”，不是完整采集流程；正式执行应配套国家—语言表、来源可行性表、query log、raw feedback、coded feedback、coverage matrix 和 codebook。

`05-country-demand-template.csv` 同样需要独立 raw 层。本轮抓到的 UAE SME “AI search visibility / GEO”讨论就是典型例子：它有明确的工作需求，但不是某个竞品的使用反馈，应从 04 分流到 05，而不是丢掉或强塞进竞品表。

## 5. 自动化可行性与权利边界

- YouTube 可通过官方 `search.list` 和 `commentThreads.list` 获取结构化视频/评论数据，但需要 API key；检索参数不提供可靠的作者国家。[YouTube search.list](https://developers.google.com/youtube/v3/docs/search/list) / [commentThreads.list](https://developers.google.com/youtube/v3/docs/commentThreads/list)
- GitHub Search API 可结构化搜索公开 issues，但对本轮闭源竞品覆盖弱，且用户国家通常不存在。[GitHub REST Search](https://docs.github.com/en/rest/search/search)
- Product Hunt 提供 GraphQL API，但需要 API key/OAuth，国家归因仍弱。[Product Hunt API](https://www.producthunt.com/v2/docs)
- Apple App Store Connect 的 customer reviews 接口和 Google Play Developer Reviews API 面向经授权的自有应用，不可当作竞争对手评论导出接口。[Apple customer reviews](https://developer.apple.com/documentation/appstoreconnectapi/customer-reviews) / [Google Play reviews.list](https://developers.google.com/android-publisher/api-ref/rest/v3/reviews/list)
- Reddit 公开页面可以人工发现，但商业或规模化使用要按当前 [Data API Terms](https://redditinc.com/policies/data-api-terms) 审查，不能把“可读”直接理解为“可批量爬取”。

## 6. 建议的下一轮

不立即扩到整个中东。先用同一套结构把 UAE 扩到 30–50 条 High geo 候选，并做双人编码校准；如果 Trustpilot 的真实任务密度在新增页面明显下降，再追加 G2/Capterra 本地筛选验证和 YouTube API 小样本。阿语与英语分别保留查询漏斗，Hindi/Urdu 只有在能稳定命中 UAE 公开工作反馈时才设正式配额。

完成 UAE 方法校准后，再复制到 Saudi Arabia。两国只共享字段与编码规则，不共享关键词、语言配额或国家归属判断。

