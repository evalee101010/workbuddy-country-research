# Region / Language Zone / Migration Corridor 衔接契约

地区轮只在相关国家轮完成后启动。它不是把国家 CSV 合并后按条数排名，而是新增地区原生查询并保留每条证据的真实地域颗粒度。

## 输入

- 已冻结国家 run 的 manifest、raw、A/B/C、coverage、audit 和 citation index。
- Region Config：`region_definition`、included/excluded countries、核心/探索语言、地区别名、迁移走廊方向和时间窗。
- 国家轮的 `cross_scope_duplicate_id`、canonical URL、平台内容 ID 和 duplicate group。

## 地区定义必须分开

`GCC`、`MENA`、`Middle East`、`Arab world`、`Arabic-speaking web` 不是同义词。每个来源记录其采用的定义、覆盖国家和排除国家。语言区不是国籍，市场可访问也不是用户所在地。

## 新增查询

- 地区词：GCC、MENA、Arab world 等。
- 语言区词：Arabic-speaking web、Brazilian Portuguese web 等。
- 迁移走廊：China-to-UAE、India-to-UAE 等，分别保存 `origin_market` 与 `destination_market`。
- 地区 KOL/媒体/社区入口：若原生按大区而非国家组织，保留 `regional_only`，不强制拆国。

## 去重与归因

1. 优先平台内容 ID，其次 canonical URL，再次作者/日期/标题/文本指纹。
2. 导入国家记录时不改变原 `content_id`、`evidence_id`、`run_id`。
3. 同一内容跨国家、地区、语区或走廊命中时共享稳定 `cross_scope_duplicate_id`。
4. 地区内容只有新增国家级证据时才可下放；否则 `country_assignment_status=regional_only`。
5. 转载和多语言镜像提示为同一 duplicate group，但保留最接近原始来源的主记录及别名。

## 输出

- 地区级 raw 与 A/B/C 增量记录，不复制国家行。
- 地区/语区/走廊覆盖矩阵。
- 国家已知信号与地区新增信号的差异表。
- 按角色、任务、语言、渠道和证据线总结的模式，不以原始样本条数给国家排序。
- 地区特有的缺口、平台偏差和定义限制。

Region Runner 复用 Gate B，并额外审核 `region_definition`、included/excluded countries、`country_assignment_status` 与跨轮去重。任何地区轮输出都不能反向覆盖已冻结国家包。
