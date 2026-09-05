# 国家数据包交付与合并契约

## 唯一交付物

每位同事交付一个由脚本生成的 ZIP：

`workbuddy-country-data-<ISO2>-<run-id>.zip`

不要手工改名包内文件、删减零命中查询、只发 Excel、另加结论报告或把多个国家塞入一个包。ZIP 用于内部探索，不代表人工 Gate B 审核完成。

## 导出前检查

1. `02-source-discovery.csv` 与 `03-channel-fit-pilot.csv` 记录所有试过的渠道及失败原因。
2. `04-approved-source-plan.yml` 对每个正式证据来源有角色和理由；A/B/C 均有 Core 或 `documented_gap`。
3. 所有 core-language 查询已经执行，零命中与限制也已记录。
4. raw 中每条 Included 有稳定 URL、最短必要原话、可见发布日期或 Unknown 说明、查询回链和地域依据。
5. A/B/C 每条 Included 回链到 Included raw，并使用本国 ID。
6. 私人电话、邮箱和不必要身份信息已去除。
7. `validate-country-run` 无 BLOCK；WARN 和完整性标签已确认属实。

`package-country-run` 会重新验证并写入质量文件和漏斗文件。不要手改 `package-manifest.json`。

## ZIP 内部结构

包内只有一个根目录，包含 run manifest、国家上下文、source discovery、channel pilot、内部 source plan、collection funnel、raw、A/B/C、三张 query 表、coverage、gaps/biases、structural validation 和 package manifest。

`package-manifest.json` 记录国家、run、研究窗口、版本、行数、覆盖摘要、限制标签、WARN、包内文件大小与 SHA-256。任一文件被改动后哈希都会失效，应从原 run 重新导出新包，不能在 ZIP 内修补。

## 内部校验结果

`internal_validation_pass`：结构和必填字段通过，未发现 WARN。`internal_validation_warn`：没有 BLOCK，但存在应在后续分析中保留的限制。`internal_validation_block`：禁止打包。

这些结果不验证观点真伪、样本代表性或内容版权授权，也不能替代未来面向外部发布或高风险决策的独立证据复核。

## 合并规则

`merge-country-packs` 先验证 ZIP、manifest、版本、哈希和表头，再纵向合并各表并添加 `package_country_iso2` 和 `package_run_id`。同一国家/run 的重复包或跨包 ID 冲突会中止。canonical URL 跨国重复会写入 `cross-country-duplicates.csv`，原始行继续保留。

合并输出包括：

- `tables/`：sources、pilot、raw、A/B/C、queries、coverage；
- `country-pack-index.csv`：国家、run、执行人、窗口、状态与包哈希；
- `cross-country-duplicates.csv`；
- `merge-warnings.md`；
- `merged-manifest.json`；
- 同名合并 ZIP。

Schema/package 版本不一致时停止，不静默转换。需要字段迁移时应先统一 runner 版本并重新导出各国家包。
