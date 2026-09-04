# 海外 Cowork 公开需求信号 Country Runner 实施计划

> 日期：2026-09-03<br>
> 对应设计：[海外 Cowork 公开需求信号 Country Runner 设计](../specs/2026-09-03-public-demand-country-runner-design.md)<br>
> 实施方式：测试先行、小步提交、先用 UAE 验证，再开放其他九国<br>
> 数据安全：现有 `research/`、`research/pilots/` 和 `outputs/` 文件均视为用户资产；迁移前不修改，迁移时只读导入

## 1. 实施目标

交付一套半自动 Country Runner，使团队可以用以下五条核心命令逐国完成公开需求研究：

```bash
./country-runner init AE
./country-runner discover AE
./country-runner pilot AE
./country-runner validate AE
./country-runner build AE
```

Runner 负责目录、配置、查询包、结构校验、稳定 ID、去重提示、质量门和报告渲染；研究员负责当地渠道判断、公开页面回源、翻译、编码和人工审批。

第一版以 UAE 端到端通过为完成条件，不同时批量采集十国。其他九国交付可运行的种子配置和待本地试跑的渠道候选。

## 2. 技术选择与目录

### 2.1 技术选择

- Python 3.9+：CLI、CSV、状态机、校验、Markdown 渲染。
- PyYAML 6.x：读取 Country Config 和全局规则。
- Codex 工作区提供的 Node.js 与 `@oai/artifact-tool`：生成、检查、渲染并导出 Excel 交付物。
- `unittest`：不增加测试框架依赖。
- 公开采集：人工页面复核、允许的结构化导出和后续可选适配器；第一版不开发通用爬虫。

`requirements.txt` 只固定 PyYAML 的兼容范围。XLSX 构建器使用 `load_workspace_dependencies` 返回的 Node.js 和 `@oai/artifact-tool` 路径；运行时在可写目录创建 `node_modules` 软链接，不修改依赖目录，也不把机器路径提交进仓库。README 说明：CSV/Markdown 流程可在普通 Python 环境运行；XLSX 构建与渲染验证需要 Codex 工作区依赖。

### 2.2 目标目录

```text
country-runner                       # 根目录可执行入口
country_runner/
├── README.md
├── requirements.txt
├── country_runner/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── paths.py
│   ├── config.py
│   ├── manifest.py
│   ├── csvio.py
│   ├── ids.py
│   ├── discovery.py
│   ├── pilot.py
│   ├── validation.py
│   ├── coverage.py
│   ├── report_md.py
│   ├── report_xlsx.py              # 调度 JS 构建器、处理错误与冻结
│   └── migrate_uae.py
├── xlsx/
│   └── build_country_workbook.mjs  # 唯一工作簿创作脚本
├── config/
│   ├── global/
│   │   ├── product-catalog.yml
│   │   ├── channel-catalog.yml
│   │   ├── codebook.yml
│   │   └── quality-rules.yml
│   └── countries/
│       ├── AE.yml
│       ├── SA.yml
│       ├── US.yml
│       ├── GB.yml
│       ├── DE.yml
│       ├── JP.yml
│       ├── SG.yml
│       ├── ID.yml
│       ├── IN.yml
│       └── BR.yml
├── schemas/
│   ├── country-config-fields.yml
│   ├── manifest-fields.yml
│   └── table-fields.yml
├── templates/
│   ├── source-discovery.csv
│   ├── channel-fit-pilot.csv
│   ├── source-plan.yml
│   ├── raw-discovery-log.csv
│   ├── A-competitor-feedback.csv
│   ├── B-local-work-needs.csv
│   ├── C-kol-koc-content.csv
│   ├── evidence-audit.csv
│   ├── coverage-matrix.csv
│   ├── country-context.md
│   └── gaps-and-biases.md
├── docs/
│   ├── researcher-sop.md
│   ├── reviewer-checklist.md
│   ├── field-mapping-legacy-uae.md
│   └── region-runner-contract.md
└── tests/
    ├── __init__.py
    ├── fixtures/
    ├── test_cli.py
    ├── test_config.py
    ├── test_templates.py
    ├── test_manifest.py
    ├── test_discovery.py
    ├── test_pilot.py
    ├── test_ids_and_dedup.py
    ├── test_uae_migration.py
    ├── test_validation.py
    ├── test_reports.py
    └── test_uae_e2e.py

research/runs/                      # 运行时生成；不预填正式研究结论
```

## 3. 开发约束

1. 每项任务先写失败测试，再做最小实现，再运行相关测试和全量测试。
2. 不改写现有 UAE 试跑文件；测试使用复制到临时目录的最小 fixture。
3. 每次提交只暂存计划中明确列出的文件，避免带入现有工作区修改。
4. 所有命令支持 `--project-root`、`--runs-root` 和 `--run-id`，测试不依赖真实工作区路径。
5. 没有 API 凭证、登录态或付费权限时，匿名路径必须完整可运行。
6. 自动化不能生成研究判断；它只校验人类可审计的字段和规则。
7. 冻结数据不可原地改写。任何更新创建新 run 或新版本。
8. 工作簿只能由 `@oai/artifact-tool` 创作；不得回退到 openpyxl、xlsxwriter 或其他替代库。

全量测试命令：

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -v
```

## 4. 实施任务

### Task 1：建立可执行骨架和隔离测试环境

**新建文件**

- `country-runner`
- `country_runner/requirements.txt`
- `country_runner/country_runner/__init__.py`
- `country_runner/country_runner/__main__.py`
- `country_runner/country_runner/cli.py`
- `country_runner/country_runner/paths.py`
- `country_runner/tests/__init__.py`
- `country_runner/tests/test_cli.py`

**测试先行**

1. 写测试：`--help` 显示五条核心命令。
2. 写测试：未知命令返回非零状态和可读错误。
3. 写测试：从任意工作目录运行时仍能解析项目根和配置根。
4. 实现最小 argparse CLI；子命令先返回“尚未实现”的明确状态。
5. 根入口只负责定位 Python 模块，不写业务逻辑；业务模块采用延迟导入，使 `--help` 不依赖 PyYAML/openpyxl 已安装。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_cli.py' -v
./country-runner --help
```

**建议提交**

```text
feat(country-runner): scaffold cli and paths
```

### Task 2：实现 Country Config 与十国种子配置

**新建文件**

- `country_runner/country_runner/config.py`
- `country_runner/schemas/country-config-fields.yml`
- `country_runner/config/countries/{AE,SA,US,GB,DE,JP,SG,ID,IN,BR}.yml`
- `country_runner/tests/test_config.py`

**测试先行**

1. 测试必填组：身份、语言、地域、受众、任务、产品、渠道、访问策略、研究参数、区域映射。
2. 测试 ISO2/ISO3 唯一且十国代码正确。
3. 测试每国至少有匿名公开路径、主流非开发者角色和任务家族。
4. 测试 UAE 存在七个酋长国及国家级 `Unknown` 回退。
5. 测试 SA 与 UAE 分开维护阿拉伯语、本地城市和国家归因锚点。
6. 测试平台种子只标 `Candidate`，不能预设为 `Core`。
7. 实现显式字段校验；未知字段报错，避免拼写错误静默通过。

**种子配置原则**

- 国家配置只放“待试跑候选”，不写未经验证的当地渠道结论。
- 每个国家包含本地语言、英文和必要的混写/罗马化入口。
- 小红书类或侨民平台标记 `migration_corridor`/`diaspora` 候选。
- GitHub 默认 `global_technical`，不默认归国。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_config.py' -v
```

**建议提交**

```text
feat(country-runner): add validated country configs
```

### Task 3：建立全局目录、代码本和表结构模板

**新建文件**

- `country_runner/config/global/product-catalog.yml`
- `country_runner/config/global/channel-catalog.yml`
- `country_runner/config/global/codebook.yml`
- `country_runner/config/global/quality-rules.yml`
- `country_runner/schemas/manifest-fields.yml`
- `country_runner/schemas/table-fields.yml`
- `country_runner/templates/*`
- `country_runner/tests/test_templates.py`

**测试先行**

1. 测试所有 CSV 表头与设计文档一致且没有重复字段。
2. 测试 raw 表包含 `content_id` 和最短必要原文；A/B/C 表包含 `evidence_id` 和 `content_id`。
3. 测试共同字段在三张编码表中类型和枚举一致。
4. 测试 C 表能分别保存 views、likes、comments、shares、真实公开 clicks 和抓取日期。
5. 测试 `technical_level`、`mainstream_fit`、`scope_level`、访问状态和渠道角色枚举。
6. 测试产品目录保留 A/B/C/D 竞品层级；开发者产品仍为能力参照。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_templates.py' -v
```

**建议提交**

```text
feat(country-runner): add catalogs codebook and templates
```

### Task 4：实现 run 初始化、manifest 和状态机

**新建或修改文件**

- `country_runner/country_runner/manifest.py`
- `country_runner/country_runner/cli.py`
- `country_runner/templates/country-context.md`
- `country_runner/templates/gaps-and-biases.md`
- `country_runner/tests/test_manifest.py`

**测试先行**

1. `init AE --run-id 2026-09-03-demo` 创建完整目录和空模板。
2. 已存在目录时拒绝覆盖。
3. manifest 写入配置/代码本版本、执行者、时间窗、路径和输入哈希。
4. 测试所有允许状态及非法跨级转换。
5. 多个未冻结 run 存在且未传 `--run-id` 时拒绝执行。
6. 冻结 run 的任何写操作被阻止。
7. 用临时目录完成实现，测试不得写真实 `research/runs/`。

**状态机**

```text
initialized
→ discovery_ready
→ source_plan_pending
→ source_plan_approved
→ collection_in_progress
→ validation_pass | validation_warn | validation_block
→ frozen
```

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_manifest.py' -v
./country-runner init AE --run-id smoke-test --runs-root /private/tmp/country-runner-smoke
```

**建议提交**

```text
feat(country-runner): initialize runs and enforce state transitions
```

### Task 5：实现本地渠道发现和多语言查询包

**新建或修改文件**

- `country_runner/country_runner/discovery.py`
- `country_runner/country_runner/cli.py`
- `country_runner/templates/source-discovery.csv`
- `country_runner/tests/test_discovery.py`
- `country_runner/tests/fixtures/configs/AE-minimal.yml`

**测试先行**

1. `discover` 组合国家锚点、次国家锚点、任务词、产品词和 A/B/C 查询家族。
2. UAE 查询同时包含国家级与七酋长国级入口，不把 Dubai 代替 UAE。
3. 输出分开标记核心语言、探索语言和迁移走廊语言。
4. GitHub 查询默认 `global_technical`；当地 AI 论坛和社交平台进入 Candidate 列表。
5. 生成的 `02-source-discovery.csv` 保留当地角色、活跃证据、受众、访问状态和偏差字段。
6. 没有 API 凭证时仍生成完整人工查询包。
7. 重复运行不覆盖研究员已填写的来源行，只追加新的稳定候选或给出冲突报告。

**产物**

- `queries/A-competitor-queries.csv`
- `queries/B-local-needs-queries.csv`
- `queries/C-kol-koc-queries.csv`
- `02-source-discovery.csv`
- `01-country-context.md` 中的渠道发现说明

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_discovery.py' -v
```

**建议提交**

```text
feat(country-runner): generate local source discovery queries
```

### Task 6：实现 Channel Fit Pilot 和 Gate A

**新建或修改文件**

- `country_runner/country_runner/pilot.py`
- `country_runner/country_runner/cli.py`
- `country_runner/templates/channel-fit-pilot.csv`
- `country_runner/templates/source-plan.yml`
- `country_runner/tests/test_pilot.py`

**测试先行**

1. Pilot 汇总每个渠道的 inspected、raw found、included、High/Medium geo 和主流任务产出。
2. 渠道具备两组独立查询的有效产出且无访问 BLOCK 时，可以建议 `Core`。
3. 产出稀少但独特时建议 `Supplement`，无回源能力时建议 `Discovery-only` 或 `Reject`。
4. 登录/API 不可用的增强渠道只能为 `Auth-optional`，不能阻塞匿名路径。
5. 私域或封闭社区只能为 `Consent-required`。
6. `pilot` 首次生成 pending Source Plan；再次运行不得覆盖人工审批字段。
7. 只有 `approved_by`、`approved_at`、A/B/C 覆盖和缺口说明完整时，状态转为 `source_plan_approved`。

**Gate A 特例**

若某证据线没有 Core，Source Plan 必须写明：已试渠道、失败原因、替代来源、下一步以及该线在报告中将保持空白或降级。不得用弱来源伪装 Core。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_pilot.py' -v
```

**建议提交**

```text
feat(country-runner): evaluate channel fit and gate source plans
```

### Task 7：实现稳定 ID、原始证据导入和跨表去重

**新建或修改文件**

- `country_runner/country_runner/csvio.py`
- `country_runner/country_runner/ids.py`
- `country_runner/tests/test_ids_and_dedup.py`
- `country_runner/tests/fixtures/evidence/`

**测试先行**

1. 平台内容 ID 优先生成稳定 `content_id`；否则使用 canonical URL 指纹。
2. 同一内容从多个查询命中时合并命中关系，不复制 content。
3. 一项内容可以产生多个独立 `evidence_id`，但相同原话和任务不能在 A/B/C 重复计数。
4. canonical URL 参数、短链和多语言镜像生成重复提示。
5. 冻结前 ID 稳定；新增记录不重排旧 ID。
6. `original_text`、译文、上下文、日期和地理证据不因编码表合并而丢失。
7. CSV 读写保持 UTF-8、阿拉伯语、日语、印地语和换行引号正确。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_ids_and_dedup.py' -v
```

**建议提交**

```text
feat(country-runner): preserve provenance and stable evidence ids
```

### Task 8：实现 UAE 旧数据非破坏性迁移

**新建文件**

- `country_runner/country_runner/migrate_uae.py`
- `country_runner/docs/field-mapping-legacy-uae.md`
- `country_runner/tests/test_uae_migration.py`
- `country_runner/tests/fixtures/uae-legacy/`

**只读输入**

- `research/pilots/are-competitor-feedback/04-raw-feedback.csv`
- `research/pilots/are-competitor-feedback/05-coded-feedback.csv`
- `research/pilots/are-competitor-feedback/16-kol-uae-multichannel-samples.csv`

**测试先行**

1. 复制最小匿名 fixture，证明迁移不修改源文件哈希。
2. 旧 `feedback_id`/`sample_id` 写入 `legacy_record_id`。
3. `original_text` 与 `original_text_translation_cn` 原样保留。
4. 缺失的新字段保持空，不推断点击量、受众角色或价格。
5. `emirate_name` 映射到 `admin1_name`，保留原置信度。
6. A 与 C 记录建立稳定 content/evidence ID；可能重复的 URL 只提示，不自动丢弃。
7. 输出迁移日志、行数对账和未映射字段清单。

**接口**

迁移是内部维护命令，不增加团队必须记忆的第六条命令：

```bash
./country-runner migrate-uae --source research/pilots/are-competitor-feedback --run-id 2026-09-03-uae-e2e
```

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_uae_migration.py' -v
```

**建议提交**

```text
feat(country-runner): migrate legacy UAE evidence safely
```

### Task 9：实现 Gate B、受众偏差和覆盖校验

**新建或修改文件**

- `country_runner/country_runner/validation.py`
- `country_runner/country_runner/coverage.py`
- `country_runner/country_runner/cli.py`
- `country_runner/templates/evidence-audit.csv`
- `country_runner/templates/coverage-matrix.csv`
- `country_runner/tests/test_validation.py`

**测试先行**

1. Included 标题证据缺原话、URL、日期、地域依据或人工审核时返回 `BLOCK`。
2. 仅凭语言、域名、storefront 或 regionCode 归国时返回 `BLOCK`。
3. Low/Unknown 地域内容可保留为 region/global，但不能进入国家标题结论。
4. 缺 API/点击量等可选字段只返回 `INFO` 或 `WARN`。
5. 技术样本独立标识；开发者渠道单独支撑主流结论时返回 `BLOCK`。
6. 主流 PASS 基线：至少三类主流角色、四类非开发者任务、两个来源家族，并完成配置中的全部核心查询尝试。
7. 已执行查询但公开有效样本不足时返回 `WARN`，保留真实空白。
8. 单一来源主题、次国家覆盖不均和未审翻译按规则分级。
9. 所有标题证据和直接引用必须审核；其余 Included 行抽查比例不少于 10%。
10. `validation_warn` 可以进入 build，`validation_block` 不可以。
11. 首次 validate 生成审计清单并在未签署时保持 BLOCK；审核者填写检查结果、姓名和时间后再次 validate 才能进入 PASS/WARN。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_validation.py' -v
```

**建议提交**

```text
feat(country-runner): enforce evidence and audience quality gates
```

### Task 10：实现 Markdown 与 XLSX 构建和冻结

**新建或修改文件**

- `country_runner/country_runner/report_md.py`
- `country_runner/country_runner/report_xlsx.py`
- `country_runner/xlsx/build_country_workbook.mjs`
- `country_runner/country_runner/cli.py`
- `country_runner/tests/test_reports.py`

**测试先行**

1. Markdown 固定生成十一章，空证据线保留执行记录和缺口。
2. 每个标题结论列出 evidence ID，并能回到 content ID、原文和 URL。
3. 报告分开主流、进阶和技术附录，不把 GitHub 主题写成大众需求。
4. KOL 表保留各平台原始互动，不跨平台求和；点击未知保持空值。
5. XLSX 由唯一 `.mjs` 构建器生成，包含 Summary、Source Plan、Raw Discovery、A、B、C、Coverage、Audit、Warnings、Citation Index 工作表。
6. 阿拉伯语、日语、葡萄牙语和中文在 XLSX 中不乱码；长原文自动换行，URL 可点击，冻结表头。
7. Gate A 未批准、Gate B 为 BLOCK、审核者未签字时 build 失败。
8. build 使用临时文件原子替换未冻结派生物；冻结后重复 build 拒绝改写。
9. freeze log 写入输入哈希、输出哈希、构建时间、审核者和 WARN 清单。
10. 构建后用 artifact-tool inspect 检查关键范围和公式错误，并渲染所有工作表做视觉验证；严重裁切、空白页或乱码必须修复。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_reports.py' -v
```

视觉检查 UAE 工作簿：

```bash
./country-runner build AE --run-id 2026-09-03-uae-e2e
```

打开输出确认工作表、文字方向、换行、列宽和链接；发现布局问题后补回归测试。

**建议提交**

```text
feat(country-runner): build auditable country reports
```

### Task 11：完成 UAE 端到端验收

**新建或修改文件**

- `country_runner/tests/test_uae_e2e.py`
- `country_runner/tests/fixtures/uae-e2e/`
- `research/runs/AE/2026-09-03-uae-e2e/`（只在最终人工演示时生成）

**测试场景**

1. 从空临时目录执行 init。
2. 生成 UAE 国家/七酋长国、多语言渠道发现包。
3. 导入匿名化 UAE fixture 并生成 Pilot 草案。
4. 模拟 Gate A 人工审批。
5. 导入 A/B/C 证据，保留 legacy ID 与原话。
6. 首次 validate 生成 Gate B 审计清单并因未签署保持 BLOCK。
7. 验证真实 WARN：非 Dubai 酋长国覆盖不足、部分指标缺失、授权增强未运行。
8. 模拟 Gate B 审核签字并再次 validate，得到 `validation_warn`。
9. 构建 Markdown/XLSX 并冻结。
10. 再次 build 被拒绝；新 run 不受旧 run 影响。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -p 'test_uae_e2e.py' -v
python3 -m unittest discover -s country_runner/tests -t country_runner -v
```

人工核对：抽取报告中的三条标题结论，逐条回链到 evidence、content、原文和 URL。

**建议提交**

```text
test(country-runner): verify UAE end-to-end workflow
```

### Task 12：写团队 SOP、审核手册和地区衔接契约

**新建或修改文件**

- `country_runner/README.md`
- `country_runner/docs/researcher-sop.md`
- `country_runner/docs/reviewer-checklist.md`
- `country_runner/docs/region-runner-contract.md`
- `research/01-data-dictionary.md`（只追加经验证的新字段与迁移说明）

**文档内容**

- 十分钟启动指南和五条核心命令。
- 每个命令的输入、输出、暂停点、错误和恢复方式。
- 国家渠道发现示例，但明确平台只是候选。
- 原话最小摘录、翻译、地理归因、角色判断和公开访问边界。
- Gate A/Gate B 的签署流程。
- 如何把结果导入 Excel/飞书，如何处理 CSV 编码。
- Region Runner 输入输出、跨轮去重、区域定义和不强制归国规则。
- 常见误区：把语言当国家、把 storefront 当居民、把播放量当需求、把开发者当大众、把未知价格当免费。

**验收**

让一名没有参与开发的同事，仅阅读 README 和 SOP，在临时目录中完成 `init → discover → pilot`，记录卡点并修订文档。没有真实同事可用时，由执行者在全新临时目录按“零上下文”清单自测，并将该限制记为 WARN。

**验证**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -v
./country-runner --help
```

**建议提交**

```text
docs(country-runner): add team research and review handbook
```

### Task 13：最终回归、差异审计与交付

**检查项**

1. 运行全部测试。
2. 对照设计文档逐条检查目标、非目标、目录、字段、状态、质量门和报告章节。
3. 检查 `git diff --check`、意外生成文件、临时文件和凭证。
4. 验证提交历史没有包含用户原有未提交修改。
5. 抽查十国配置；任何未试跑的平台保持 Candidate。
6. 确认现有 UAE 源文件哈希没有变化。
7. 在 README 标记第一版限制：只有 UAE 完成端到端，其他九国需逐国执行当地渠道发现和 Gate A。

**最终命令**

```bash
python3 -m unittest discover -s country_runner/tests -t country_runner -v
git diff --check
git status --short
```

**建议提交**

```text
chore(country-runner): finalize first country research package
```

## 5. 计划完成定义

满足以下条件才算第一版完成：

- 五条核心命令可执行且帮助文档清晰。
- 十国配置通过校验，平台均为待验证种子而非假定事实。
- UAE 端到端包通过 Gate A、Gate B、构建与冻结验收。
- A/B/C 都保留原话、译文、URL、日期、地域依据和稳定 ID。
- 主报告不能由开发者样本主导。
- 匿名公开路径不依赖登录/API 权限。
- 现有 UAE 研究资产未被覆盖或改写。
- Markdown/XLSX、SOP、审核手册和地区衔接契约齐全。
- 全量测试通过，所有 WARN 在示例包和 README 中可见。

## 6. 暂缓项

以下事项形成后续独立计划，不进入本次实施：

- 九国正式数据采集与当地渠道结论。
- Region Runner 自动化和跨国综合报告。
- Reddit、LinkedIn、小红书类、TikTok 等平台的专用采集适配器。
- 登录、API key、付费数据源和私域社区集成。
- 统计代表性抽样、市场规模估计和国家评分。
- 产品策略、差异化和我方制胜能力分析。
