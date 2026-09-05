# 证据字段与写入契约

CSV 表头必须与 `assets/country_runner/templates/` 完全一致，UTF-8 编码。不要增删或重排字段。精确字段枚举以 `assets/country_runner/schemas/table-fields.yml` 和全局 codebook 为准。

## ID 与回链

- `source_id`：`SRC-<ISO3>-<stable-slug>`。
- `query_id`：`Q-<A|B|C>-<ISO2或ISO3>-<stable-id>`。
- `content_id`：`CNT-<ISO2或ISO3>-<run内唯一编号>`。
- `evidence_id`：`EVD-<ISO2或ISO3>-<run内唯一编号>`，跨 A/B/C 不得重复。

一条公开页面/帖子/视频/评论为一个 raw `content_id`。A/B/C 每行是一个可以独立判断的证据单元，必须回链 raw 的 `content_id`。同一内容可进入多个流，但相同句子和相同任务不能为增加主题数重复计数。

## Raw 必填与规则

Included raw 至少记录：`content_id`、`run_id`、`source_id`、`source_name`、`item_url`、`canonical_url`、`published_at`、`date_confidence`、`captured_at`、`query_hit_ids`、`content_language`、`original_text`、`country_iso3`、`geo_evidence`、`country_confidence`、`scope_level`、`inclusion_status` 和 `capture_mode`。

`query_hit_ids` 可用 `|` 合并多个查询。canonical URL 去除跟踪参数但保留稳定内容标识。一个 canonical URL 在同一国家 raw 中只出现一次。原话保持原语言和原意；换行、引号和标点不得因 CSV 写入损坏。非中文内容填写 `original_text_translation_cn`。

作者只记公开别名。`raw_fields_json` 仅保存无法映射但确有价值的公开字段，不得成为塞入私密信息的旁路。

## 所有 A/B/C 的共同必填

Included 证据至少记录：

- `evidence_id`、`content_id`、`run_id`、`evidence_stream`；
- `source_id`、`source_name`、`source_url`、`item_url`；
- `published_at`、`date_confidence`、`captured_at`；
- `query_id`、`query_language`、`content_language`；
- `original_text`、非中文时的中文译文、必要上下文；
- `country_iso3`、`country_or_region`、`geo_evidence`、`country_confidence`、`scope_level`；
- `audience_role`、`technical_level`、`source_audience_bias`；
- `inclusion_status`、`review_status`、`headline_evidence`、`normalized_theme`。

发布日期只写可见或可可靠标准化的日期；不能把抓取日当发布日。相对时间标准化时保留 `published_at_raw` 并降低 `date_confidence`。

## A：竞品反馈

围绕具体任务编码 `product`、`job_to_be_done`、触发、输入/连接工具、预期/实际输出、成功状态、失败阶段、人工干预、耗时、设置难度、可靠性、控制审批、隐私信任、价格/限额、当前替代方案、留存/流失/切换和情绪。看不到的字段留空，不根据产品宣传补齐。

只纳入实际体验或足够具体的使用叙述；纯转发、泛宣传、无使用上下文的口号可以保留 raw，但不得冒充产品反馈。

## B：当地工作需求

编码 `company_size`、`mainstream_fit`、`work_task`、`job_to_be_done`、当前方案、痛点、期望结果、触发、工具/产品、意向阶段、付费信号、切换信号和情绪。B 不要求出现 AI 或竞品名称；重点是可由 Cowork 类产品支持的真实知识工作。

开发、API 或部署任务可以保留，但标 Technical/Developer，不得用其单独支撑大众需求。

## C：KOL/KOC 内容

编码创作者、创作者类型、受众、内容格式、标题/钩子、工作场景、可见互动指标、抓取时点、搜索排名上下文、CTA、承接 URL、Offer 名称/价格/币种、漏斗阶段、商业兴趣和商业偏差。

互动指标逐条原样保存，未知点击量保持空白。不得把播放量当需求人数、把点赞当购买、把粉丝位置当受众位置。就业结果等大主题下可继续拆分技能/二级任务，例如简历、求职资源、1:1 辅导、作品集和面试，但每个二级任务必须有内容级证据。

## 去重与排除

优先使用平台内容 ID，其次 canonical URL，再次标题/作者/日期/文本指纹。镜像、短链和多查询命中合并到一个 raw；保留全部 query IDs。跨国 canonical URL 重复不自动删除，由合并工具标记。

排除或暂不纳入的记录仍应保留发现痕迹与理由：超出研究窗、无国家依据、纯广告、重复、无原话、无法公开访问、只发现机构但无内容等。
