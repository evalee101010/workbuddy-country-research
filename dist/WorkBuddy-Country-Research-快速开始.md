# WorkBuddy 逐国公开信号研究：快速开始

## 你要交付什么

你独立负责一个国家，只交付一个完整、可合并的原始数据 ZIP。不要写市场结论、国家评分或产品策略。

## 安装

1. 解压 `workbuddy-country-research-skill-v1.zip`。
2. 把其中的 `workbuddy-country-research` 文件夹放到你的 Codex Skills 目录。
3. 重新打开 Codex/Cowork 会话。
4. 在你用于存放研究数据的工作区里启动任务。

## 推荐提示词

> 使用 $workbuddy-country-research 跑德国；执行人 Anna；研究截止日 2026-09-30。先检查当地渠道和语言配置，再完成 A/B/C 公开信号采集、内部结构校验并导出国家数据 ZIP。不要做结论总结。

Skill 会把运行工具准备到当前工作区的 `.workbuddy-country-research/`，把数据写到 `research/runs/<ISO2>/<run-id>/`。不要在 Skill 安装目录里运行或保存研究数据。

## 执行时牢记

- 每个国家重新判断适用渠道；不要照搬 UAE、Saudi 或其他国家的平台组合。
- GitHub、开发者论坛和硬核 AI 社区只作技术补充，不能替代普通职场人、小企业、自由职业者、销售、运营、行政、人事等主流人群。
- 原始记录必须保留最短必要原话、中文译文、URL、日期、查询 ID 和明确地域依据。
- 记录零命中、重复、登录限制和算法排序限制。
- “尽量全”只指已登记查询矩阵内的合格唯一命中，不代表平台全量或统计代表性。
- 私域、登录绕过、个人电话/邮箱和推断数据禁止进入包。

## 交包

完成后让 Skill 运行 `validate-country-run` 和 `package-country-run`。修复全部 BLOCK；WARN 可以保留，但不得删除限制说明。把生成的以下文件交回项目负责人：

`workbuddy-country-data-<ISO2>-<run-id>.zip`

不要手动改 ZIP 内容。若发现错误，修改原 run 后重新导出一个新包。
