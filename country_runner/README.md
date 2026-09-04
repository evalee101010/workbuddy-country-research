# Public Demand Country Runner

这套 Runner 用于逐国收集 Cowork 类产品的公开用户需求与 KOL/KOC 内容信号。它统一证据协议和质量门，但不要求每个国家使用同一批平台。

主报告优先覆盖求职者、办公室工作者、销售/市场、运营/行政/HR、自由职业者/创作者和小企业主。GitHub、开发者论坛和硬核 AI 社区只作为技术补充，不能单独支撑大众需求结论。

## 十分钟启动

环境要求：Python 3.9+、PyYAML。只有最终生成 XLSX 时需要 Node.js 和 `@oai/artifact-tool`；公开匿名研究路径不依赖平台 API 或登录。

```bash
./country-runner init AE --run-id 2026-09-03 --researcher "姓名"
./country-runner discover AE --run-id 2026-09-03
```

然后依次：

1. 在 `research/runs/AE/2026-09-03/02-source-discovery.csv` 补充当地候选渠道；不要把种子平台视为已验证来源。
2. 执行 `queries/` 中 A/B/C 查询，填写 `status`、`results_inspected`、`valid_results` 与备注。
3. 在 `03-channel-fit-pilot.csv` 填写地域、原文、日期、主流任务密度和可重复性等人工检查结果。
4. 运行 Pilot：

```bash
./country-runner pilot AE --run-id 2026-09-03
```

5. 审核者编辑 `04-approved-source-plan.yml`：填写 `approved_by`、`approved_at`、`approval_status: approved`；A/B/C 每条线必须有 Core 或 `documented_gap`。再次运行 `pilot` 完成 Gate A。
6. 把原始发现写入 `evidence/raw-discovery-log.csv`，再把可独立判断的证据单元写入 A/B/C 表。保留原话、译文、URL、日期和地域依据。
7. 首次运行 `validate` 生成 Gate B 审计清单；首次因未签字 BLOCK 是预期行为。

```bash
./country-runner validate AE --run-id 2026-09-03
```

8. 审核者完成 `review/evidence-audit.csv` 中所有 `required_review=Yes` 行，再次运行 `validate`。只有 `validation_pass` 或 `validation_warn` 可构建。
9. 生成 Markdown/XLSX 并冻结：

```bash
./country-runner build AE --run-id 2026-09-03
```

冻结后不得原地修改；更新必须新建 run。

## 首梯队国家配置

| ISO2 | 国家 | 必须留意的本地差异 |
|---|---|---|
| US | 美国 | 英语为主；专业社区、评价站和创作者渠道分层 |
| GB | 英国 | 英国工作语境与全球英语信号分开 |
| DE | 德国 | 德语核心；OMR Reviews 等本地候选需当轮验证 |
| JP | 日本 | 日语核心；ITreview、note 等候选与全球英语补充并行 |
| SG | 新加坡 | 英语核心，多语言/迁移走廊信号分层 |
| ID | 印度尼西亚 | 印尼语核心；KASKUS 等平台必须先验证当前相关活跃度 |
| IN | 印度 | 英语、印地语及区域语言分层；就业与办公任务不可只看技术社区 |
| BR | 巴西 | 葡萄牙语核心；Reclame Aqui 等投诉渠道偏差单列 |
| AE | 阿联酋 | 英语/阿语核心；七个酋长国分别查询，未知酋长国不得写成 Dubai |
| SA | 沙特 | 与 UAE 分开；阿语核心，平台、表达和地理规则独立验证 |

完整执行说明见 [researcher-sop.md](./docs/researcher-sop.md)，审核见 [reviewer-checklist.md](./docs/reviewer-checklist.md)。

## 访问边界

- 匿名公开页面、搜索发现和人工回源是主路径。
- API、登录和付费数据只增强字段；缺失不应阻塞国家包。
- 私域 WhatsApp/Telegram、封闭 Slack/Discord、登录后群组只能作为 `Consent-required` 招募或经同意观察渠道。
- 不绕过登录、访问限制、robots/平台条款或速率限制。

## 常见误区

- 内容语言、国家域名、App storefront、`regionCode` 都不能单独证明作者或用户所在地。
- 频道或 subreddit 名称只是线索；国家结论需要正文、公开资料或其他可审计地域依据。
- 播放、点赞、评论不能直接当需求规模；不同平台指标不相加。
- 未公开价格不能记为免费；链接存在不能推断点击量或转化。
- 海外华人/外籍社群先标迁移走廊或 diaspora，不能自动代表当地居民。
- Developer 样本只进技术附录，除非同一任务也得到非开发者来源支持。

## 第一版限制

- UAE 已完成带“模拟人工签字”的端到端技术验收，但尚未由第二名独立同事按零上下文 SOP 实跑；这一点是交付 WARN。
- 其余九国只有经公开资料预置的候选配置，必须逐国重新做 Local Source Discovery 和 Gate A，不能把配置里的平台当成当前有效事实。
- 第一版不含专用社交平台爬虫、登录/API 集成、地区 Runner 自动化、统计代表性抽样、国家评分或产品策略结论。

## 恢复与排错

- 多个未冻结 run 并存时必须明确传 `--run-id`。
- Runner 不覆盖原始发现；相同内容只给去重提示，最终保留/合并由研究员审核。
- `validation_block` 先看 `review/gaps-and-biases.md`；修正证据或完成审计后可再次运行 `validate`。
- XLSX 构建失败不会冻结 run，Markdown/XLSX 临时文件会被清理。
