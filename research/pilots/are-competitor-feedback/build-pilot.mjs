import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const capturedAt = "2026-09-03";
const pilotDir = path.resolve("research/pilots/are-competitor-feedback");
const outputDir = path.resolve("outputs/01a064d5-0ee8-7482-8ace-77518f64e0fa");
const renderDir = "/private/tmp/uae-competitor-feedback-pilot-renders";

const languageScope = [
  {
    country_iso3: "ARE",
    country_name_cn: "阿联酋",
    country_name_en: "United Arab Emirates",
    market_unit: "国家级；必要时再拆 Dubai / Abu Dhabi 等酋长国",
    query_language: "阿拉伯语",
    language_code: "ar",
    priority: "Core",
    rationale: "官方语言；必须覆盖阿语评价、问题词和本地化质量信号",
    seed_terms: "تجربة؛ مراجعة؛ مشاكل؛ بديل؛ اشتراك؛ رصيد؛ وكيل ذكاء اصطناعي؛ مساحة عمل",
    country_anchors: "الإمارات؛ دبي؛ أبوظبي؛ درهم؛ AED",
    geo_rule: "阿语本身不证明 ARE；至少再要正文/资料/城市/币种等地理证据",
    status: "Run",
    source_url: "https://u.ae/en/about-the-uae/fact-sheet",
  },
  {
    country_iso3: "ARE",
    country_name_cn: "阿联酋",
    country_name_en: "United Arab Emirates",
    market_unit: "国家级；必要时再拆 Dubai / Abu Dhabi 等酋长国",
    query_language: "英语",
    language_code: "en",
    priority: "Core",
    rationale: "阿联酋官方信息指出英语被广泛使用；公开工作反馈中英语样本密度更高",
    seed_terms: "review; experience; problem; alternative; subscription; credits; AI agent; workspace",
    country_anchors: "UAE; United Arab Emirates; Dubai; Abu Dhabi; AED; dirham",
    geo_rule: "英语本身不证明 ARE；UAE storefront 或检索参数也不能单独证明用户所在地",
    status: "Run",
    source_url: "https://u.ae/en/information-and-services/business/the-uae-an-ideal-investment-destination",
  },
  {
    country_iso3: "ARE",
    country_name_cn: "阿联酋",
    country_name_en: "United Arab Emirates",
    market_unit: "国家级；必要时再拆 Dubai / Abu Dhabi 等酋长国",
    query_language: "印地语",
    language_code: "hi",
    priority: "Exploratory",
    rationale: "用于测试非阿语/英语本地居民与工作人群信号，不作为首轮配额语言",
    seed_terms: "समीक्षा; अनुभव; समस्या; विकल्प; सदस्यता; क्रेडिट; एआई एजेंट",
    country_anchors: "UAE; दुबई; अबू धाबी; AED",
    geo_rule: "只有语言命中时归 Global/Unknown；首轮只记录渠道是否产出",
    status: "Probe",
    source_url: "https://u.ae/en/about-the-uae/fact-sheet",
  },
  {
    country_iso3: "ARE",
    country_name_cn: "阿联酋",
    country_name_en: "United Arab Emirates",
    market_unit: "国家级；必要时再拆 Dubai / Abu Dhabi 等酋长国",
    query_language: "乌尔都语",
    language_code: "ur",
    priority: "Exploratory",
    rationale: "阿联酋官方信息列为广泛使用语言之一；先验证公开渠道产出",
    seed_terms: "جائزہ؛ تجربہ؛ مسئلہ؛ متبادل؛ سبسکرپشن؛ کریڈٹ؛ اے آئی ایجنٹ",
    country_anchors: "UAE; دبئی; ابوظہبی; AED",
    geo_rule: "只有语言命中时归 Global/Unknown；首轮只记录渠道是否产出",
    status: "Probe",
    source_url: "https://u.ae/en/about-the-uae/fact-sheet",
  },
  {
    country_iso3: "ARE",
    country_name_cn: "阿联酋",
    country_name_en: "United Arab Emirates",
    market_unit: "国家级；必要时再拆 Dubai / Abu Dhabi 等酋长国",
    query_language: "马拉雅拉姆语",
    language_code: "ml",
    priority: "Watchlist",
    rationale: "阿联酋官方信息列为广泛使用语言之一；待核心语种跑通后再加",
    seed_terms: "അവലോകനം; അനുഭവം; പ്രശ്നം; സബ്സ്ക്രിപ്ഷൻ; ക്രെഡിറ്റ്; AI ഏജന്റ്",
    country_anchors: "UAE; ദുബായ്; അബുദാബി; AED",
    geo_rule: "不进入本轮样本配额；仅保留后续扩展入口",
    status: "Hold",
    source_url: "https://u.ae/en/about-the-uae/fact-sheet",
  },
];

const sourceFeasibility = [
  {
    channel: "Trustpilot",
    access_status: "Manual-Review",
    public_access: "公开页面可读；页面位置会随新增评价变化",
    machine_access: "本轮不做自动化批量抓取",
    auth_or_rights: "无需登录即可人工查看；规模化前需复核条款/许可",
    dimensions_observed: "资料国家、日期、评分、任务、结果、价格/积分、客服、迁移/留存",
    geo_strength: "Strong when profile country is shown",
    main_bias: "主动评价与售后/投诉偏差；品牌页不代表总体用户",
    pilot_recommendation: "首轮核心渠道；人工采样+编码，保存作者/日期定位",
    pilot_test_outcome: "顺利；获得 6 条可编码 ARE 样本",
    source_url: "https://www.trustpilot.com/",
  },
  {
    channel: "Apple App Store",
    access_status: "Manual-Review",
    public_access: "ARE storefront 评论页可直接访问",
    machine_access: "公开页可解析，但竞争对手评论无官方批量导出接口",
    auth_or_rights: "公开查看；规模化前需复核条款/许可",
    dimensions_observed: "昵称、日期、评论、评分显示、产品任务、价格/积分、替代品",
    geo_strength: "Weak: storefront is not reviewer residence",
    main_bias: "移动端/商店样本；storefront 地理误判风险高",
    pilot_recommendation: "作为主题发现池；仅 storefront 的记录标 Low，不单独做国家结论",
    pilot_test_outcome: "顺利拿量；6 条可编码假设样本，另发现 1 条地理反例",
    source_url: "https://apps.apple.com/ae/",
  },
  {
    channel: "Reddit",
    access_status: "Conditional",
    public_access: "公开帖子可经搜索引擎发现并人工阅读",
    machine_access: "不做未授权批量抓取；官方 Data API 使用受条款约束",
    auth_or_rights: "商业/扩展研究需按 Reddit Data API 条款单独评估",
    dimensions_observed: "正文自述地理、任务上下文、工作链路、替代品、留存、互动",
    geo_strength: "Variable; strong only with explicit self-location",
    main_bias: "社区选择偏差；命中率低；子版块不等于常住地",
    pilot_recommendation: "保留低量高信息密度的人工发现；每条单独做地理证据审查",
    pilot_test_outcome: "低产出但高价值；1 条明确 Dubai 的 Comet 深度样本",
    source_url: "https://redditinc.com/policies/data-api-terms",
  },
  {
    channel: "Google Play",
    access_status: "Manual-Review",
    public_access: "公开评论页可读并可指定界面语言",
    machine_access: "官方 Reviews API 面向经授权的自有应用，不是竞品评论导出",
    auth_or_rights: "公开查看；官方 API 需发布者授权",
    dimensions_observed: "评论、日期、评分、语言、产品问题；用户国家通常缺失",
    geo_strength: "Weak",
    main_bias: "界面语言/商店参数不等于用户国家",
    pilot_recommendation: "作为多语言主题发现池；无额外地理证据不进入 ARE 核心样本",
    pilot_test_outcome: "可访问；阿语评论有用，但本轮无法归因到 ARE",
    source_url: "https://developers.google.com/android-publisher/api-ref/rest/v3/reviews/list",
  },
  {
    channel: "YouTube",
    access_status: "Conditional",
    public_access: "视频页/搜索结果可人工发现",
    machine_access: "Data API 可检索视频与评论线程",
    auth_or_rights: "需要 API key；配额与条款限制",
    dimensions_observed: "视频日期/频道/互动、评论文本、语言；作者国家通常缺失",
    geo_strength: "Weak",
    main_bias: "regionCode/relevanceLanguage 只影响检索，不证明评论者所在地",
    pilot_recommendation: "拿到 key 后测评论产出；当前只用于发现，不归因国家",
    pilot_test_outcome: "发现阿语 Cowork 内容，但无 UAE 证据；API 未执行",
    source_url: "https://developers.google.com/youtube/v3/docs/commentThreads/list",
  },
  {
    channel: "GitHub",
    access_status: "Ready-API",
    public_access: "公开 issues/discussions 可搜索",
    machine_access: "REST Search API；未认证配额较低",
    auth_or_rights: "公开数据；仍需遵守 API 与仓库许可",
    dimensions_observed: "版本、复现步骤、错误阶段、技术环境、维护状态",
    geo_strength: "Very weak",
    main_bias: "技术用户偏差；本轮闭源竞品缺少官方问题面",
    pilot_recommendation: "仅对有公开 repo/extension 的竞品启用",
    pilot_test_outcome: "接口可用，但本轮目标产品未产出 ARE 反馈",
    source_url: "https://docs.github.com/en/rest/search/search",
  },
  {
    channel: "Product Hunt",
    access_status: "Conditional",
    public_access: "产品页可人工阅读",
    machine_access: "GraphQL API",
    auth_or_rights: "需要 API key/OAuth token",
    dimensions_observed: "发布、评论、早期用户反应、替代品；国家信息弱",
    geo_strength: "Weak",
    main_bias: "早期采用者/发布活动偏差；难做国家归因",
    pilot_recommendation: "用于全球新品/定位，不作为国家反馈主渠道",
    pilot_test_outcome: "本轮未获得可归因 ARE 样本",
    source_url: "https://www.producthunt.com/v2/docs",
  },
  {
    channel: "G2/Capterra",
    access_status: "Candidate-Validate",
    public_access: "部分公开页可人工查看",
    machine_access: "未确认适合本项目的公开竞品评论导出",
    auth_or_rights: "批量使用/再分发需单独审查平台条款或授权",
    dimensions_observed: "角色、公司规模、行业、优缺点、评分（若页面提供）",
    geo_strength: "Medium at best",
    main_bias: "B2B 评论激励/审核机制与产品覆盖差异",
    pilot_recommendation: "二轮验证；先确认目标竞品覆盖和 ARE 筛选能力",
    pilot_test_outcome: "搜索未发现稳定的 ARE 样本入口",
    source_url: "https://www.g2.com/",
  },
  {
    channel: "Search engine index",
    access_status: "Ready-Discovery",
    public_access: "可检索公开索引结果",
    machine_access: "只作为发现层，不把搜索摘要当原始反馈",
    auth_or_rights: "按搜索服务条款使用",
    dimensions_observed: "候选 URL、标题、日期片段、国家/语言关键词",
    geo_strength: "None by itself",
    main_bias: "排名/索引偏差；摘要可能过期或截断",
    pilot_recommendation: "用于跨平台找入口；必须回到原始页面编码",
    pilot_test_outcome: "顺利支持多渠道发现，也暴露大量错国/错语种结果",
    source_url: "https://www.google.com/",
  },
  {
    channel: "Publisher review APIs",
    access_status: "Reference-Only",
    public_access: "不提供竞品评论公开导出",
    machine_access: "Apple/Google 官方接口面向开发者自有应用",
    auth_or_rights: "需要对应发布者账户与应用权限",
    dimensions_observed: "自有应用评分/评论/回复工作流",
    geo_strength: "N/A for competitor research",
    main_bias: "权限边界决定无法用于竞品",
    pilot_recommendation: "不纳入竞品采集；未来只用于我方产品反馈",
    pilot_test_outcome: "不适用",
    source_url: "https://developer.apple.com/documentation/appstoreconnectapi/customer-reviews",
  },
  {
    channel: "Chrome Web Store",
    access_status: "Reference-Only",
    public_access: "扩展详情/评论可人工查看（若竞品有扩展）",
    machine_access: "官方 API 主要是发布者管理，不是竞品评论导出",
    auth_or_rights: "发布 API 需要所有者授权",
    dimensions_observed: "扩展版本、评分、评论、浏览器工作流",
    geo_strength: "Weak",
    main_bias: "只覆盖浏览器扩展用户；目标产品覆盖不一",
    pilot_recommendation: "有扩展的竞品再单独测；不作为通用入口",
    pilot_test_outcome: "本轮未产出 ARE 样本",
    source_url: "https://developer.chrome.com/docs/webstore/using-api",
  },
  {
    channel: "Editorial/SEO",
    access_status: "Discovery-Only",
    public_access: "公开文章可读",
    machine_access: "不作为用户反馈抓取",
    auth_or_rights: "按网页版权/引用规范使用",
    dimensions_observed: "本地关键词、产品定位、可能的用例线索",
    geo_strength: "Article market, not user location",
    main_bias: "SEO/联盟/编辑观点；不能冒充用户证据",
    pilot_recommendation: "只提取检索词和待验证假设",
    pilot_test_outcome: "发现 UAE 定向文章，因非用户反馈排除",
    source_url: "https://menaelite.com/manus-ai-agent-review-uae-2026/",
  },
];

const queryLog = [
  {query_id:"Q-ARE-001",channel:"Trustpilot",product:"Genspark",query_language:"en",exact_query:'site:trustpilot.com/review/genspark.ai "AE" Genspark',country_anchor:"AE profile tag",time_window:"2025-09-01 to 2026-09-03",pages_checked:"pages 3, 4, 7, 9",candidates_seen:4,coded_count:4,outcome:"Yield",leakage:"Page order changes over time",note:"按作者名+日期复核；任务、积分和迁移字段丰富"},
  {query_id:"Q-ARE-002",channel:"Trustpilot",product:"Manus",query_language:"en/es",exact_query:'site:trustpilot.com/review/manus.im "David Erreyes"',country_anchor:"AE profile tag",time_window:"2025-09-01 to 2026-09-03",pages_checked:"brand page",candidates_seen:1,coded_count:1,outcome:"Yield",leakage:"西语站点界面不代表评论语种/国家",note:"获取到应用构建、积分退款和锁定效应"},
  {query_id:"Q-ARE-003",channel:"Trustpilot",product:"Perplexity",query_language:"en",exact_query:'site:trustpilot.com/review/www.perplexity.ai "AE" subscription charged',country_anchor:"AE profile tag",time_window:"2025-09-01 to 2026-09-03",pages_checked:"page 3",candidates_seen:1,coded_count:1,outcome:"Adjacent yield",leakage:"属于产品账单而非 Comet 工作任务",note:"保留为商业系统/售后边界样本"},
  {query_id:"Q-ARE-004",channel:"Trustpilot",product:"ChatGPT",query_language:"en",exact_query:'site:trustpilot.com/review/chatgpt.com "AE" simple task',country_anchor:"AE profile tag",time_window:"2025-09-01 to 2026-09-03",pages_checked:"page 5",candidates_seen:1,coded_count:0,outcome:"Exclude",leakage:"任务太模糊且非 Cowork",note:"证明有国家标签也仍需任务门槛"},
  {query_id:"Q-ARE-005",channel:"Apple App Store",product:"Genspark",query_language:"en/ar",exact_query:"apps.apple.com/ae Genspark see-all=reviews",country_anchor:"ARE storefront",time_window:"page current at capture",pages_checked:"1 storefront page",candidates_seen:8,coded_count:4,outcome:"Hypothesis yield",leakage:"storefront 不证明作者在 UAE",note:"价格/积分、阿语质量、停用和替代信号明显"},
  {query_id:"Q-ARE-006",channel:"Apple App Store",product:"Manus",query_language:"en",exact_query:"apps.apple.com/ae Manus see-all=reviews",country_anchor:"ARE storefront",time_window:"page current at capture",pages_checked:"1 storefront page",candidates_seen:9,coded_count:2,outcome:"Hypothesis yield",leakage:"storefront 不证明作者在 UAE",note:"积分消耗、错误、扣费和客服字段丰富"},
  {query_id:"Q-ARE-007",channel:"Apple App Store",product:"ChatGPT",query_language:"en",exact_query:"apps.apple.com/ae ChatGPT see-all=reviews",country_anchor:"ARE storefront",time_window:"page current at capture",pages_checked:"1 storefront page",candidates_seen:6,coded_count:0,outcome:"Geo counterexample",leakage:"正文明确提到 Afghanistan",note:"UAE storefront 只能给 Low geo confidence"},
  {query_id:"Q-ARE-008",channel:"Reddit",product:"Perplexity Comet",query_language:"en",exact_query:'site:reddit.com/r/perplexity_ai "I live in Dubai" Comet',country_anchor:"正文自述 Dubai",time_window:"2025-09-01 to 2026-09-03",pages_checked:"1 thread",candidates_seen:1,coded_count:1,outcome:"High-value yield",leakage:"无",note:"工作链路、环境上下文、替代和留存都可编码"},
  {query_id:"Q-ARE-009",channel:"Reddit",product:"Perplexity / Claude",query_language:"en",exact_query:"site:reddit.com/r/dubai Perplexity Claude discount",country_anchor:"r/dubai",time_window:"all time",pages_checked:"1 thread",candidates_seen:1,coded_count:0,outcome:"Route to demand / out of window",leakage:"子版块不是常住地；早于主窗口",note:"可作为价格需求，不进入本轮竞品反馈"},
  {query_id:"Q-ARE-010",channel:"Reddit",product:"General AI",query_language:"en",exact_query:"site:reddit.com/r/UAE AI search visibility SME",country_anchor:"r/UAE + 正文 UAE SME",time_window:"2025-09-01 to 2026-09-03",pages_checked:"1 thread",candidates_seen:1,coded_count:0,outcome:"Route to 05 demand",leakage:"不是竞品使用反馈",note:"保留为公开用户需求信号入口"},
  {query_id:"Q-ARE-011",channel:"Search engine index",product:"Genspark / Manus",query_language:"ar",exact_query:"الإمارات تجربة Genspark Manus مشاكل اشتراك رصيد",country_anchor:"الإمارات",time_window:"2025-09-01 to 2026-09-03",pages_checked:"first results page",candidates_seen:null,coded_count:0,outcome:"Low precision",leakage:"Saudi/Egypt/Iraq/global Arabic results",note:"阿语必须和国家证据二次交叉，不能直接归 UAE"},
  {query_id:"Q-ARE-012",channel:"YouTube",product:"Claude Cowork",query_language:"ar",exact_query:"دبي Claude Cowork تجربة مراجعة",country_anchor:"دبي",time_window:"2025-09-01 to 2026-09-03",pages_checked:"search results",candidates_seen:1,coded_count:0,outcome:"Discovery only",leakage:"视频为泛阿语内容，无 UAE 用户证据",note:"作者/评论者国家弱；需 API key 后再测评论"},
  {query_id:"Q-ARE-013",channel:"Search engine index",product:"Genspark",query_language:"hi",exact_query:"UAE Genspark review Hindi दुबई",country_anchor:"UAE / दुबई",time_window:"2025-09-01 to 2026-09-03",pages_checked:"first results page",candidates_seen:0,coded_count:0,outcome:"No yield",leakage:"无",note:"保留为探索语种，不设首轮配额"},
  {query_id:"Q-ARE-014",channel:"Search engine index",product:"Manus",query_language:"ur",exact_query:"UAE Manus AI review Urdu دبئی",country_anchor:"UAE / دبئی",time_window:"2025-09-01 to 2026-09-03",pages_checked:"first results page",candidates_seen:0,coded_count:0,outcome:"No yield",leakage:"无",note:"保留为探索语种，不设首轮配额"},
  {query_id:"Q-ARE-015",channel:"Google Play",product:"Genspark",query_language:"ar",exact_query:"play.google.com Genspark hl=ar reviews",country_anchor:"none",time_window:"page current at capture",pages_checked:"1 product page",candidates_seen:1,coded_count:0,outcome:"Global-Arabic only",leakage:"阿语界面/评论无 UAE 地理证据",note:"保留到 Global-Arabic 主题池，不进入 ARE"},
  {query_id:"Q-ARE-016",channel:"YouTube",product:"Multiple",query_language:"en/ar",exact_query:"YouTube Data API search.list + commentThreads.list",country_anchor:"regionCode=AE (discovery only)",time_window:"planned",pages_checked:"not run",candidates_seen:null,coded_count:0,outcome:"Blocked by key",leakage:"regionCode 不等于作者国家",note:"需要 API key；先小样本测试评论命中率"},
  {query_id:"Q-ARE-017",channel:"Product Hunt",product:"Genspark / Manus",query_language:"en",exact_query:"Genspark UAE Product Hunt comments",country_anchor:"UAE keyword",time_window:"all time",pages_checked:"search results",candidates_seen:0,coded_count:0,outcome:"No country yield",leakage:"早期采用者评论普遍无国家",note:"适合全球定位/竞品发现，不适合本轮国家归因"},
  {query_id:"Q-ARE-018",channel:"GitHub",product:"Genspark / Manus / Comet",query_language:"en",exact_query:"Genspark Manus Comet UAE issue",country_anchor:"UAE keyword",time_window:"all time",pages_checked:"search results",candidates_seen:0,coded_count:0,outcome:"No target surface",leakage:"同名项目与非官方仓库",note:"闭源产品缺少稳定官方 issue 面"},
  {query_id:"Q-ARE-019",channel:"G2/Capterra",product:"Genspark / Manus",query_language:"en",exact_query:"Genspark Manus UAE review G2 Capterra",country_anchor:"UAE keyword",time_window:"all time",pages_checked:"search results",candidates_seen:0,coded_count:0,outcome:"No stable yield",leakage:"产品覆盖不足/国家筛选不明显",note:"二轮再做授权和页面能力验证"},
  {query_id:"Q-ARE-020",channel:"Editorial/SEO",product:"Manus",query_language:"en",exact_query:"Manus AI agent review UAE 2026",country_anchor:"UAE in title",time_window:"2026",pages_checked:"1 article",candidates_seen:1,coded_count:0,outcome:"Exclude as feedback",leakage:"编辑/SEO 内容不是用户反馈",note:"只用于发现本地词和待验证假设"},
];

const rawFeedback = [
  {feedback_id:"FB-ARE-20260602-000001",product:"Manus",product_scope:"Direct agent/workspace",source_channel:"Trustpilot",source_name:"Trustpilot Manus",source_url:"https://es.trustpilot.com/review/manus.im",source_item_hint:"David Erreyes · AE · 2 Jun 2026",author_alias:"David Erreyes",published_at:"2026-06-02",published_at_raw:"2 Jun 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en/es",content_language:"es",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:1,author_context:"正在用 Manus 构建应用；已投入时间和金钱",task_summary:"持续构建一个已较成熟的应用",outcome_summary:"产品能力有价值，但退款积分未到账并形成迁移锁定",friction_summary:"多次积分退款不到账；继续使用需升级更贵计划",pricing_signal:"已花费超过 US$200 credits；计划升级价格上升",switching_signal:"不愿从其他工具重做，因会损失更多时间和金钱",sentiment:"Negative",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] 应用已做得较深，但积分与退款问题造成锁定",inclusion_status:"Included-Core",exclusion_reason:"",duplicate_group:"",researcher_note:"国家来自平台资料标识，未独立验证身份"},
  {feedback_id:"FB-ARE-20260815-000002",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Trustpilot",source_name:"Trustpilot Genspark",source_url:"https://ca.trustpilot.com/review/genspark.ai?page=3",source_item_hint:"Anish Velupillai · AE · 15 Aug 2026",author_alias:"Anish Velupillai",published_at:"2026-08-15",published_at_raw:"15 Aug 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:5,author_context:"需要向高层交付演示材料的知识工作者",task_summary:"短时间内准备 top-management presentations",outcome_summary:"模板、洞察和内容修改支持让演示制作更容易、压力更低",friction_summary:"未提及明确失败",pricing_signal:"",switching_signal:"正向持续使用信号",sentiment:"Positive",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] Super Agent 帮助在短时限内完成高层演示",inclusion_status:"Included-Core",exclusion_reason:"",duplicate_group:"",researcher_note:"任务和结果明确；角色仍为推断性标签"},
  {feedback_id:"FB-ARE-20260707-000003",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Trustpilot",source_name:"Trustpilot Genspark",source_url:"https://uk.trustpilot.com/review/genspark.ai?page=7",source_item_hint:"nasima ahmed · AE · 7 Jul 2026",author_alias:"nasima ahmed",published_at:"2026-07-07",published_at_raw:"7 Jul 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:5,author_context:"startup founder / solo entrepreneur",task_summary:"制作演示、电子表格、CRM dashboard 与内容，支持日常经营",outcome_summary:"多个工作流集中到同一 workspace，并成为日常工具",friction_summary:"未提及明确失败",pricing_signal:"付费订阅在用",switching_signal:"取消 Higgsfield，因为 Genspark 覆盖创意工作",sentiment:"Positive",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] 创始人用它统一演示、表格、CRM 与内容工作",inclusion_status:"Included-Core",exclusion_reason:"",duplicate_group:"",researcher_note:"高信息密度正向留存样本"},
  {feedback_id:"FB-ARE-20260419-000004",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Trustpilot",source_name:"Trustpilot Genspark",source_url:"https://uk.trustpilot.com/review/genspark.ai?page=9",source_item_hint:"Simon Balol · AE · 19 Apr 2026",author_alias:"Simon Balol",published_at:"2026-04-19",published_at_raw:"19 Apr 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:1,author_context:"设计/生产工作用户",task_summary:"生成包含设计文件的 ZIP 下载，并输出透明背景 logo",outcome_summary:"ZIP 多次失败且无法生成链接；logo 背景不透明",friction_summary:"反复尝试仍失败，同时持续消耗 credits",pricing_signal:"失败尝试仍扣 credits，造成时间和金钱损失",switching_signal:"不推荐用于严肃设计/生产工作",sentiment:"Negative",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] ZIP 与透明 logo 任务失败，过程中持续扣积分",inclusion_status:"Included-Core",exclusion_reason:"",duplicate_group:"",researcher_note:"可明确编码失败阶段、结果和成本"},
  {feedback_id:"FB-ARE-20260804-000005",product:"Genspark",product_scope:"Support / commercial system",source_channel:"Trustpilot",source_name:"Trustpilot Genspark",source_url:"https://www.trustpilot.com/review/genspark.ai?page=4",source_item_hint:"Sebastian Fuchs · AE · 4 Aug 2026",author_alias:"Sebastian Fuchs",published_at:"2026-08-04",published_at_raw:"4 Aug 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:4,author_context:"未说明",task_summary:"处理 credits 争议/投诉",outcome_summary:"客服调查并适当退款；整体认为平台灵活",friction_summary:"曾发生 credits 争议",pricing_signal:"credits 争议获得退款",switching_signal:"正向继续使用",sentiment:"Positive",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] credits 争议得到调查与退款",inclusion_status:"Included-Adjacent",exclusion_reason:"",duplicate_group:"",researcher_note:"能评价售后但缺少具体 Cowork 工作任务"},
  {feedback_id:"FB-ARE-20260722-000006",product:"Perplexity",product_scope:"Support / commercial system",source_channel:"Trustpilot",source_name:"Trustpilot Perplexity",source_url:"https://www.trustpilot.com/review/www.perplexity.ai?page=3",source_item_hint:"Muhammad Waqas · AE · 22 Jul 2026",author_alias:"Muhammad Waqas",published_at:"2026-07-22",published_at_raw:"22 Jul 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:1,author_context:"付费订阅用户",task_summary:"取消订阅并请求停止扣费/退款",outcome_summary:"取消后连续数月仍扣费；只有自动邮件，未获得人工解决",friction_summary:"无法联系人工客服；承诺 48 小时回访但未兑现",pricing_signal:"取消后仍被收取 5–7 月费用",switching_signal:"明确取消订阅",sentiment:"Negative",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] 取消后仍连续扣费，且无法获得人工支持",inclusion_status:"Included-Adjacent",exclusion_reason:"",duplicate_group:"",researcher_note:"不是 Comet/Cowork 任务反馈，只进入商业系统边界"},
  {feedback_id:"FB-ARE-20260809-000007",product:"ChatGPT",product_scope:"General AI",source_channel:"Trustpilot",source_name:"Trustpilot ChatGPT",source_url:"https://www.trustpilot.com/review/chatgpt.com?page=5",source_item_hint:"AbuYaseen Hodjageldyev · AE · 9 Aug 2026",author_alias:"AbuYaseen Hodjageldyev",published_at:"2026-08-09",published_at_raw:"9 Aug 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Trustpilot profile displays AE",country_confidence:"High",rating:1,author_context:"付费用户",task_summary:"仅称 simple task，未说明工作内容",outcome_summary:"认为浪费时间",friction_summary:"任务细节不足，无法判断失败阶段",pricing_signal:"付费用户",switching_signal:"",sentiment:"Negative",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] 付费后简单任务仍浪费时间",inclusion_status:"Excluded",exclusion_reason:"任务不可识别；非 Cowork 特性",duplicate_group:"",researcher_note:"用于说明国家明确也不等于内容合格"},
  {feedback_id:"FB-ARE-20250912-000008",product:"Perplexity Comet",product_scope:"Direct browser agent",source_channel:"Reddit",source_name:"r/perplexity_ai",source_url:"https://www.reddit.com/r/perplexity_ai/comments/1nf6r5e/comet_browser_the_automatic_ai_browser_from/",source_item_hint:"Thread dated 12 Sep 2025",author_alias:"not retained",published_at:"2025-09-12",published_at_raw:"12 Sep 2025",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"Dubai, United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"Body explicitly states residence in Dubai",country_confidence:"High",rating:null,author_context:"Dubai resident; active AI subscription user",task_summary:"自动处理日常/手工网页任务、邮件与空调选购研究",outcome_summary:"结合房间大小、Dubai 天气、电商与促销信息做决策支持",friction_summary:"未提及本次任务失败",pricing_signal:"用一个订阅替代多个 AI 订阅",switching_signal:"取消几乎所有其他 AI 订阅，仅保留 Gemini",sentiment:"Positive",capture_mode:"Manual indexed discovery + paraphrase",evidence_excerpt:"[转述] Dubai 用户用 Comet 自动化邮件与本地购物研究",inclusion_status:"Included-Core",exclusion_reason:"",duplicate_group:"",researcher_note:"本轮最完整的地理+任务+替代链路样本"},
  {feedback_id:"FB-ARE-20250322-000009",product:"Perplexity / Claude",product_scope:"Pricing demand",source_channel:"Reddit",source_name:"r/dubai",source_url:"https://www.reddit.com/r/dubai/comments/1jhg4sk",source_item_hint:"Thread dated 22 Mar 2025",author_alias:"not retained",published_at:"2025-03-22",published_at_raw:"22 Mar 2025",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"Dubai community",country_iso3_candidate:"ARE",geo_evidence:"Posted in r/dubai; no explicit residence retained",country_confidence:"Medium",rating:null,author_context:"价格敏感的潜在订阅者",task_summary:"寻找 Perplexity/Claude 折扣",outcome_summary:"询问本地可用优惠",friction_summary:"订阅价格",pricing_signal:"显式折扣需求",switching_signal:"比较多个产品",sentiment:"Neutral",capture_mode:"Manual indexed discovery + paraphrase",evidence_excerpt:"[转述] 询问 Dubai 可用的 Perplexity/Claude 优惠",inclusion_status:"Excluded",exclusion_reason:"早于主窗口；更适合 05 国家需求",duplicate_group:"",researcher_note:"后续可转移到 demand signal 表"},
  {feedback_id:"FB-ARE-20260404-000010",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Apple App Store",source_name:"UAE App Store Genspark",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",source_item_hint:"Mzmz2006 · I paid a lot for small tasks · 4 Apr",author_alias:"Mzmz2006",published_at:"",published_at_raw:"4 Apr (year not shown)",date_confidence:"Year unknown",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"UAE storefront only",country_iso3_candidate:"ARE",geo_evidence:"Page storefront=AE; no author location",country_confidence:"Low",rating:null,author_context:"annual subscriber",task_summary:"生成图片、PPT、音乐并使用 AI designer/slides",outcome_summary:"AI designer/slides 有价值，但月度 credits 很快限制可用性",friction_summary:"误以为年订阅覆盖使用；大多数产出仍需 credits",pricing_signal:"已付年费；月度 credits 限制且难预期",switching_signal:"失望但未说明是否离开",sentiment:"Negative",capture_mode:"Manual storefront review + paraphrase",evidence_excerpt:"[转述] 年订阅后才发现图片、PPT、音乐仍受积分限制",inclusion_status:"Included-Core-LowGeo",exclusion_reason:"",duplicate_group:"",researcher_note:"只可用于 UAE 假设池，不能单独代表 UAE 用户"},
  {feedback_id:"FB-ARE-20260220-000011",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Apple App Store",source_name:"UAE App Store Genspark",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",source_item_hint:"Michelle2025dxb · Not intuitive · 20 Feb",author_alias:"Michelle2025dxb",published_at:"",published_at_raw:"20 Feb (year not shown)",date_confidence:"Year unknown",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"Possible Dubai",country_iso3_candidate:"ARE",geo_evidence:"AE storefront + unverified 'dxb' in alias",country_confidence:"Medium",rating:null,author_context:"needs a general AI assistant",task_summary:"用作日常 AI assistant 并提出单次问题",outcome_summary:"认为难用且每个问题都会消耗 tokens",friction_summary:"交互不直观；单位任务 credits 消耗感强",pricing_signal:"tokens/credits 消耗",switching_signal:"明确更倾向 ChatGPT",sentiment:"Negative",capture_mode:"Manual storefront review + paraphrase",evidence_excerpt:"[转述] 难上手、每次提问都耗 token，倾向改用 ChatGPT",inclusion_status:"Included-Core-MediumGeo",exclusion_reason:"",duplicate_group:"",researcher_note:"用户名不是可靠身份证据，仍不可升级为 High"},
  {feedback_id:"FB-ARE-20260417-000012",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Apple App Store",source_name:"UAE App Store Genspark",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",source_item_hint:"Chahaita · Sudden stopped working · 17 Apr",author_alias:"Chahaita",published_at:"",published_at_raw:"17 Apr (year not shown)",date_confidence:"Year unknown",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"UAE storefront only",country_iso3_candidate:"ARE",geo_evidence:"Page storefront=AE; no author location",country_confidence:"Low",rating:null,author_context:"recent purchaser",task_summary:"购买后继续使用 AI workspace",outcome_summary:"购买不足一个月即无法使用",friction_summary:"付费后服务中断",pricing_signal:"已购买且权益期内不可用",switching_signal:"明确不再使用",sentiment:"Negative",capture_mode:"Manual storefront review + paraphrase",evidence_excerpt:"[转述] 购买不到一个月即无法使用，并决定停用",inclusion_status:"Included-Core-LowGeo",exclusion_reason:"",duplicate_group:"",researcher_note:"任务细节一般，但付费—可用性—流失链路清楚"},
  {feedback_id:"FB-ARE-20260416-000013",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Apple App Store",source_name:"UAE App Store Genspark",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",source_item_hint:"Matrixuae · Arabic language mistakes · 16 Apr",author_alias:"Matrixuae",published_at:"",published_at_raw:"16 Apr (year not shown)",date_confidence:"Year unknown",captured_at:capturedAt,query_language:"en/ar",content_language:"en",geo_claim:"Possible UAE",country_iso3_candidate:"ARE",geo_evidence:"AE storefront + unverified 'uae' in alias",country_confidence:"Medium",rating:null,author_context:"Arabic-language user",task_summary:"使用阿语输出",outcome_summary:"认为阿语错误多",friction_summary:"本地语言质量不足",pricing_signal:"同时认为价格高",switching_signal:"",sentiment:"Negative",capture_mode:"Manual storefront review + paraphrase",evidence_excerpt:"[转述] 阿语错误较多，同时认为价格偏高",inclusion_status:"Included-Core-MediumGeo",exclusion_reason:"",duplicate_group:"",researcher_note:"本地化主题重要，但地理仍未独立验证"},
  {feedback_id:"FB-ARE-20250516-000014",product:"Manus",product_scope:"Direct agent/workspace",source_channel:"Apple App Store",source_name:"UAE App Store Manus",source_url:"https://apps.apple.com/ae/app/manus-ai-agent-automation/id6740909540?platform=iphone&see-all=reviews",source_item_hint:"TheTruthArabian · Terrible Experience · 16 May 2025",author_alias:"TheTruthArabian",published_at:"2025-05-16",published_at_raw:"16/05/2025",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"UAE storefront only",country_iso3_candidate:"ARE",geo_evidence:"Page storefront=AE; alias is not location proof",country_confidence:"Low",rating:null,author_context:"paid app user",task_summary:"付费后尝试调用 Manus 服务",outcome_summary:"每次访问报错，但 credits 仍被扣除",friction_summary:"错误、未交付、客服无回复、疑似重复扣费尝试",pricing_signal:"失败仍扣 credits；银行出现再次扣费通知",switching_signal:"明确不推荐",sentiment:"Negative",capture_mode:"Manual storefront review + paraphrase",evidence_excerpt:"[转述] 服务反复报错仍扣积分，客服也未响应",inclusion_status:"Included-Core-LowGeo",exclusion_reason:"",duplicate_group:"",researcher_note:"内容很强，但 UAE 归属仅 Low"},
  {feedback_id:"FB-ARE-20260419-000015",product:"Manus",product_scope:"Direct agent/workspace",source_channel:"Apple App Store",source_name:"UAE App Store Manus",source_url:"https://apps.apple.com/ae/app/manus-ai-agent-automation/id6740909540?platform=iphone&see-all=reviews",source_item_hint:"Mazen2012 · Credits Drain · 19 Apr",author_alias:"Mazen2012",published_at:"",published_at_raw:"19 Apr (year not shown)",date_confidence:"Year unknown",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"UAE storefront only",country_iso3_candidate:"ARE",geo_evidence:"Page storefront=AE; no author location",country_confidence:"Low",rating:null,author_context:"Lite plan user",task_summary:"执行一个简单任务",outcome_summary:"简单任务消耗 510 credits，价值不足以支持订阅",friction_summary:"使用成本不可预测且与任务价值不匹配",pricing_signal:"510 credits for one simple task；明确不愿订阅",switching_signal:"认为有更好的替代品并预计用户会离开",sentiment:"Negative",capture_mode:"Manual storefront review + paraphrase",evidence_excerpt:"[转述] 一个简单任务消耗 510 credits，认为不值得订阅",inclusion_status:"Included-Core-LowGeo",exclusion_reason:"",duplicate_group:"",researcher_note:"价格主题清晰；任务具体内容未知"},
  {feedback_id:"FB-ARE-20260000-000016",product:"ChatGPT",product_scope:"General AI",source_channel:"Apple App Store",source_name:"UAE App Store ChatGPT",source_url:"https://apps.apple.com/ae/app/chatgpt/id6448311069?platform=iphone&see-all=reviews",source_item_hint:"Review text explicitly references leaving Afghanistan",author_alias:"not retained",published_at:"",published_at_raw:"not retained",date_confidence:"Unknown",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"Afghanistan",country_iso3_candidate:"AFG",geo_evidence:"Review body explicitly identifies Afghanistan context despite AE storefront",country_confidence:"High",rating:null,author_context:"Afghanistan context",task_summary:"general ChatGPT use",outcome_summary:"not coded",friction_summary:"not coded",pricing_signal:"",switching_signal:"",sentiment:"Unknown",capture_mode:"Manual storefront geo-audit",evidence_excerpt:"[转述] 正文明确出现 Afghanistan，与 UAE storefront 冲突",inclusion_status:"Excluded",exclusion_reason:"Wrong country; geo counterexample",duplicate_group:"",researcher_note:"直接证明 storefront 不能等同 reviewer country"},
  {feedback_id:"FB-GLB-20260000-000017",product:"Claude Cowork",product_scope:"Direct cowork feature",source_channel:"YouTube",source_name:"YouTube public search",source_url:"https://www.youtube.com/results?search_query=%D9%82%D8%B6%D9%8A%D8%AA+%D8%B4%D9%87%D8%B1%D9%8A%D9%86+Claude+Cowork",source_item_hint:"Arabic video: قضيت شهرين مع Claude Cowork",author_alias:"channel not retained",published_at:"",published_at_raw:"not retained",date_confidence:"Unknown",captured_at:capturedAt,query_language:"ar",content_language:"ar",geo_claim:"Arabic-speaking only",country_iso3_candidate:"",geo_evidence:"Language only; no UAE marker",country_confidence:"Unknown",rating:null,author_context:"video creator",task_summary:"Claude Cowork long-form experience video",outcome_summary:"not coded",friction_summary:"not coded",pricing_signal:"",switching_signal:"",sentiment:"Unknown",capture_mode:"Search discovery only",evidence_excerpt:"[转述] 阿语 Cowork 体验内容，但无法归属 UAE",inclusion_status:"Excluded",exclusion_reason:"No UAE geo evidence",duplicate_group:"",researcher_note:"可进入 Global-Arabic 候选池"},
  {feedback_id:"FB-GLB-20260000-000018",product:"Genspark",product_scope:"Direct agent/workspace",source_channel:"Google Play",source_name:"Google Play Arabic storefront",source_url:"https://play.google.com/store/apps/details?hl=ar&id=ai.mainfunc.genspark",source_item_hint:"Arabic review about credits and image generation",author_alias:"not retained",published_at:"",published_at_raw:"not retained",date_confidence:"Unknown",captured_at:capturedAt,query_language:"ar",content_language:"ar",geo_claim:"Arabic-speaking only",country_iso3_candidate:"",geo_evidence:"Arabic interface/review only; no UAE marker",country_confidence:"Unknown",rating:null,author_context:"mobile user",task_summary:"图片生成",outcome_summary:"对 credits 成本不满",friction_summary:"credits 价格/消耗",pricing_signal:"high credit cost",switching_signal:"",sentiment:"Negative",capture_mode:"Manual public-page review + paraphrase",evidence_excerpt:"[转述] 阿语评论提到积分成本与图片生成问题",inclusion_status:"Excluded",exclusion_reason:"No UAE geo evidence",duplicate_group:"",researcher_note:"进入 Global-Arabic 主题池，不进入 ARE"},
  {feedback_id:"DS-ARE-20260520-000019",product:"General AI search visibility",product_scope:"Country demand",source_channel:"Reddit",source_name:"r/UAE",source_url:"https://www.reddit.com/r/UAE/comments/1tie48b/has_anyone_here_tested_geo_ai_search_visibility/",source_item_hint:"UAE SME asks about GEO/AI search visibility",author_alias:"not retained",published_at:"2026-05-20",published_at_raw:"20 May 2026",date_confidence:"Exact",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"United Arab Emirates",country_iso3_candidate:"ARE",geo_evidence:"UAE SME context in body + r/UAE",country_confidence:"High",rating:null,author_context:"UAE SME",task_summary:"提升 AI search visibility / GEO",outcome_summary:"寻求工具或经验",friction_summary:"现有可见性/方法不确定",pricing_signal:"",switching_signal:"",sentiment:"Neutral",capture_mode:"Manual indexed discovery + paraphrase",evidence_excerpt:"[转述] UAE SME 寻求 AI 搜索可见性方案",inclusion_status:"Excluded",exclusion_reason:"Belongs to 05 country-demand dataset",duplicate_group:"",researcher_note:"这是 04 与 05 分流的示例"},
  {feedback_id:"FB-ARE-20260000-000020",product:"Manus",product_scope:"Editorial review",source_channel:"Editorial/SEO",source_name:"MenaElite",source_url:"https://menaelite.com/manus-ai-agent-review-uae-2026/",source_item_hint:"Manus AI Agent Review UAE 2026",author_alias:"editorial",published_at:"2026",published_at_raw:"2026",date_confidence:"Year only",captured_at:capturedAt,query_language:"en",content_language:"en",geo_claim:"UAE-targeted article",country_iso3_candidate:"ARE",geo_evidence:"UAE in article targeting, not a user location",country_confidence:"Unknown",rating:null,author_context:"publisher/editor",task_summary:"product review article",outcome_summary:"not coded",friction_summary:"not coded",pricing_signal:"",switching_signal:"",sentiment:"Unknown",capture_mode:"Search discovery only",evidence_excerpt:"[转述] 面向 UAE 的评测文章，但不是用户原始反馈",inclusion_status:"Excluded",exclusion_reason:"Editorial/SEO, not user-generated feedback",duplicate_group:"",researcher_note:"只用于发现当地词与候选假设"},
];

const originalEvidence = {
  "FB-ARE-20260602-000001": { original_text: "Llevo gastando más de 200 dólares en créditos", original_text_translation_cn: "我已经在积分上花了超过 200 美元。" },
  "FB-ARE-20260815-000002": { original_text: "prepare presentations for top management on a very short time frame", original_text_translation_cn: "在很短时间内为高层准备演示材料。" },
  "FB-ARE-20260707-000003": { original_text: "building presentations, creating spreadsheets, managing CRM dashboards", original_text_translation_cn: "制作演示、创建表格并管理 CRM 仪表盘。" },
  "FB-ARE-20260419-000004": { original_text: "generate a simple ZIP file containing my designs", original_text_translation_cn: "生成一个包含我的设计文件的简单 ZIP。" },
  "FB-ARE-20260804-000005": { original_text: "investigate and refund appropriately", original_text_translation_cn: "进行调查并适当退款。" },
  "FB-ARE-20260722-000006": { original_text: "I canceled my subscription in May 2026 and they still charged me", original_text_translation_cn: "我在 2026 年 5 月取消订阅，但他们仍继续扣费。" },
  "FB-ARE-20250912-000008": { original_text: "I live in Dubai", original_text_translation_cn: "我住在迪拜。" },
  "FB-ARE-20260404-000010": { original_text: "one year subscription", original_text_translation_cn: "一年期订阅。" },
  "FB-ARE-20260220-000011": { original_text: "very difficult to use", original_text_translation_cn: "非常难用。" },
  "FB-ARE-20260417-000012": { original_text: "unable to use it", original_text_translation_cn: "无法继续使用。" },
  "FB-ARE-20260416-000013": { original_text: "Arabic language mistakes", original_text_translation_cn: "阿拉伯语错误。" },
  "FB-ARE-20250516-000014": { original_text: "it kept throwing errors", original_text_translation_cn: "它一直报错。" },
  "FB-ARE-20260419-000015": { original_text: "A very simple task burned 510 credits", original_text_translation_cn: "一个非常简单的任务消耗了 510 积分。" },
  "FB-ARE-20260000-000016": { original_text: "Afghanistan", original_text_translation_cn: "阿富汗。" },
  "FB-GLB-20260000-000017": { original_text: "قضيت شهرين مع Claude Cowork", original_text_translation_cn: "我使用 Claude Cowork 两个月。" },
  "DS-ARE-20260520-000019": { original_text: "Has anyone here tested GEO / AI search visibility?", original_text_translation_cn: "这里有人测试过 GEO / AI 搜索可见性吗？" },
  "FB-ARE-20260000-000020": { original_text: "Manus AI Agent Review UAE 2026", original_text_translation_cn: "2026 年 UAE Manus AI Agent 评测。" },
};

for (const row of rawFeedback) {
  row.original_text = originalEvidence[row.feedback_id]?.original_text ?? "";
  row.original_text_translation_cn = originalEvidence[row.feedback_id]?.original_text_translation_cn ?? "";
}

const codedFeedback = [
  {feedback_id:"FB-ARE-20260602-000001",product:"Manus",product_tier:"A1 Direct",source_type:"Review platform",source_name:"Trustpilot",source_url:"https://es.trustpilot.com/review/manus.im",published_at:"2026-06-02",captured_at:capturedAt,country_or_region:"United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Profile displays AE; not independently verified",query_language:"en/es",content_language:"es",user_role:"App builder / entrepreneur (inferred)",company_size:"Unknown",job_to_be_done:"Build and continue developing an application",trigger:"Existing project already advanced",input_or_connected_tools:"Existing Manus project; credits",expected_output:"Continue building without losing prior work",actual_result:"Project progressed, but refunds did not restore credits and plan costs escalated",success_status:"Partial",failure_stage:"Billing / credit recovery",manual_interventions:"Repeated refund claims",time_or_latency:"Switching would require rebuilding",setup_difficulty:"Unknown",reliability:"Product capability positive; commercial system unreliable",control_and_approval:"Credit ledger/refund status lacks control",privacy_and_trust:"Trust damaged by unresolved credits",pricing_or_usage_limit:">US$200 spent; higher plan needed",current_alternative:"Other options, unnamed",retention_churn_or_switching_signal:"Locked in by prior time/money despite dissatisfaction",sentiment:"Negative",evidence_excerpt:"[转述] 应用已做得较深，但积分与退款问题造成锁定",inclusion_status:"Included",scope_class:"Core",date_confidence:"Exact",source_bias_note:"Self-selected review; support/billing complaint bias",researcher_note:"Strong lock-in and cost-predictability signal"},
  {feedback_id:"FB-ARE-20260815-000002",product:"Genspark",product_tier:"A1 Direct",source_type:"Review platform",source_name:"Trustpilot",source_url:"https://ca.trustpilot.com/review/genspark.ai?page=3",published_at:"2026-08-15",captured_at:capturedAt,country_or_region:"United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Profile displays AE; not independently verified",query_language:"en",content_language:"en",user_role:"Knowledge worker preparing management materials",company_size:"Unknown",job_to_be_done:"Prepare top-management presentations under short deadlines",trigger:"Very short delivery window",input_or_connected_tools:"Templates; Super Agent; content modifications",expected_output:"Management-ready presentation with relevant insights",actual_result:"Presentation work became easier and less stressful",success_status:"Success",failure_stage:"",manual_interventions:"User still directs templates/content",time_or_latency:"Short timeframe; qualitative time saving",setup_difficulty:"Low/unclear",reliability:"Positive in stated workflow",control_and_approval:"User can modify content",privacy_and_trust:"Not mentioned",pricing_or_usage_limit:"Not mentioned",current_alternative:"Manual presentation preparation",retention_churn_or_switching_signal:"Positive continued-use signal",sentiment:"Positive",evidence_excerpt:"[转述] Super Agent 帮助在短时限内完成高层演示",inclusion_status:"Included",scope_class:"Core",date_confidence:"Exact",source_bias_note:"Self-selected positive review",researcher_note:"Strong JTBD and outcome coverage"},
  {feedback_id:"FB-ARE-20260707-000003",product:"Genspark",product_tier:"A1 Direct",source_type:"Review platform",source_name:"Trustpilot",source_url:"https://uk.trustpilot.com/review/genspark.ai?page=7",published_at:"2026-07-07",captured_at:capturedAt,country_or_region:"United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Profile displays AE; not independently verified",query_language:"en",content_language:"en",user_role:"Startup founder / solopreneur",company_size:"Solo",job_to_be_done:"Run presentations, spreadsheets, CRM dashboards and content in one workspace",trigger:"Founder must wear multiple hats",input_or_connected_tools:"Presentations; spreadsheets; CRM dashboards; content tools",expected_output:"Consolidated daily operating workspace",actual_result:"Became part of daily workflow and covered creative work too",success_status:"Success",failure_stage:"",manual_interventions:"User orchestrates multiple tasks",time_or_latency:"Works faster/smarter (qualitative)",setup_difficulty:"Unknown",reliability:"Positive over sustained use",control_and_approval:"Not mentioned",privacy_and_trust:"Not mentioned",pricing_or_usage_limit:"Paid subscription",current_alternative:"Higgsfield and separate tools",retention_churn_or_switching_signal:"Cancelled Higgsfield; Genspark retained",sentiment:"Positive",evidence_excerpt:"[转述] 创始人用它统一演示、表格、CRM 与内容工作",inclusion_status:"Included",scope_class:"Core",date_confidence:"Exact",source_bias_note:"Self-selected positive review",researcher_note:"Best role/company-size/workflow sample in pilot"},
  {feedback_id:"FB-ARE-20260419-000004",product:"Genspark",product_tier:"A1 Direct",source_type:"Review platform",source_name:"Trustpilot",source_url:"https://uk.trustpilot.com/review/genspark.ai?page=9",published_at:"2026-04-19",captured_at:capturedAt,country_or_region:"United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Profile displays AE; not independently verified",query_language:"en",content_language:"en",user_role:"Design/production user",company_size:"Unknown",job_to_be_done:"Package designs in a ZIP and create a transparent-background logo",trigger:"Need downloadable production assets",input_or_connected_tools:"Design files; image/logo generation",expected_output:"Working ZIP link and transparent PNG/logo",actual_result:"No ZIP link after retries; logo background was not transparent",success_status:"Failed",failure_stage:"Artifact generation / export",manual_interventions:"Multiple retries and verification",time_or_latency:"Time wasted across retries",setup_difficulty:"Prompting was not enough to fix output",reliability:"Low for serious production use",control_and_approval:"System admitted limitation only after attempts",privacy_and_trust:"Trust reduced by late disclosure",pricing_or_usage_limit:"Credits consumed despite failure",current_alternative:"Dedicated design/file tools (implicit)",retention_churn_or_switching_signal:"Would not recommend",sentiment:"Negative",evidence_excerpt:"[转述] ZIP 与透明 logo 任务失败，过程中持续扣积分",inclusion_status:"Included",scope_class:"Core",date_confidence:"Exact",source_bias_note:"Self-selected negative review",researcher_note:"Best failure-stage example"},
  {feedback_id:"FB-ARE-20260804-000005",product:"Genspark",product_tier:"A1 Direct",source_type:"Review platform",source_name:"Trustpilot",source_url:"https://www.trustpilot.com/review/genspark.ai?page=4",published_at:"2026-08-04",captured_at:capturedAt,country_or_region:"United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Profile displays AE; not independently verified",query_language:"en",content_language:"en",user_role:"Unknown",company_size:"Unknown",job_to_be_done:"Resolve a credits dispute",trigger:"Credit complaint",input_or_connected_tools:"Support channel; credit ledger",expected_output:"Investigation and fair refund",actual_result:"Complaint investigated and refunded appropriately",success_status:"Success",failure_stage:"Commercial/support system",manual_interventions:"Contact support",time_or_latency:"Not stated",setup_difficulty:"Not stated",reliability:"Support outcome positive",control_and_approval:"Dispute handled case-by-case",privacy_and_trust:"Trust improved by resolution",pricing_or_usage_limit:"Credits disputed then refunded",current_alternative:"Unknown",retention_churn_or_switching_signal:"Continues to enjoy product",sentiment:"Positive",evidence_excerpt:"[转述] credits 争议得到调查与退款",inclusion_status:"Included",scope_class:"Adjacent",date_confidence:"Exact",source_bias_note:"Task use vague; service-resolution signal only",researcher_note:"Useful for support system, not core JTBD"},
  {feedback_id:"FB-ARE-20260722-000006",product:"Perplexity",product_tier:"A2 Adjacent",source_type:"Review platform",source_name:"Trustpilot",source_url:"https://www.trustpilot.com/review/www.perplexity.ai?page=3",published_at:"2026-07-22",captured_at:capturedAt,country_or_region:"United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Profile displays AE; not independently verified",query_language:"en",content_language:"en",user_role:"Paid subscriber",company_size:"Unknown",job_to_be_done:"Cancel subscription and stop/resolve charges",trigger:"Cancellation in May 2026",input_or_connected_tools:"Email support; billing account",expected_output:"No further charge and a refund",actual_result:"Charged in subsequent months; no human follow-up",success_status:"Failed",failure_stage:"Billing / human support",manual_interventions:"Repeated support emails",time_or_latency:"Repeated 48-hour promises; still unresolved after days",setup_difficulty:"No phone escalation",reliability:"Low for cancellation flow",control_and_approval:"Cancellation did not stop charges",privacy_and_trust:"Trust severely damaged",pricing_or_usage_limit:"Multiple post-cancellation monthly charges",current_alternative:"Unknown",retention_churn_or_switching_signal:"Cancelled subscription",sentiment:"Negative",evidence_excerpt:"[转述] 取消后仍连续扣费，且无法获得人工支持",inclusion_status:"Included",scope_class:"Adjacent",date_confidence:"Exact",source_bias_note:"Billing complaint; not Comet/Cowork task",researcher_note:"Keep separate from core feature conclusions"},
  {feedback_id:"FB-ARE-20250912-000008",product:"Perplexity Comet",product_tier:"A1 Direct",source_type:"Community",source_name:"Reddit",source_url:"https://www.reddit.com/r/perplexity_ai/comments/1nf6r5e/comet_browser_the_automatic_ai_browser_from/",published_at:"2025-09-12",captured_at:capturedAt,country_or_region:"Dubai, United Arab Emirates",country_iso3:"ARE",country_confidence:"High",geo_evidence:"Body explicitly states residence in Dubai",query_language:"en",content_language:"en",user_role:"AI power user / consumer researcher",company_size:"Individual",job_to_be_done:"Automate daily browser work, email and local shopping research",trigger:"Repeated manual online tasks",input_or_connected_tools:"Email; room size; Dubai weather; e-commerce sites; sale dates",expected_output:"Shortlist best air-conditioner deal and automate routine actions",actual_result:"Comet combined personal/local constraints and supported the decision",success_status:"Success",failure_stage:"",manual_interventions:"User supplies context and validates purchase",time_or_latency:"Qualitative reduction in manual work",setup_difficulty:"Not stated",reliability:"Positive in described workflows",control_and_approval:"User remains decision maker",privacy_and_trust:"Email access implied; concern not stated",pricing_or_usage_limit:"One subscription replaced several",current_alternative:"Other AI subscriptions; Gemini retained",retention_churn_or_switching_signal:"Cancelled almost all other AI subscriptions",sentiment:"Positive",evidence_excerpt:"[转述] Dubai 用户用 Comet 自动化邮件与本地购物研究",inclusion_status:"Included",scope_class:"Core",date_confidence:"Exact",source_bias_note:"Community self-selection; single rich case",researcher_note:"Best end-to-end local-context sample"},
  {feedback_id:"FB-ARE-20260000-000010",product:"Genspark",product_tier:"A1 Direct",source_type:"App-store review",source_name:"Apple App Store",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",published_at:"",captured_at:capturedAt,country_or_region:"UAE hypothesis pool",country_iso3:"ARE",country_confidence:"Low",geo_evidence:"AE storefront only",query_language:"en",content_language:"en",user_role:"Annual subscriber",company_size:"Unknown",job_to_be_done:"Create images, PPT, music and designed assets",trigger:"Purchased annual subscription",input_or_connected_tools:"AI Designer; AI Slides; chat; monthly credits",expected_output:"Use paid creative features throughout subscription",actual_result:"Creative tools useful but quickly constrained by monthly credits",success_status:"Partial",failure_stage:"Usage quota / expectation setting",manual_interventions:"Must wait/buy more credits or fall back to chat",time_or_latency:"Monthly reset dependency",setup_difficulty:"Plan limits were not understood at purchase",reliability:"Feature capability positive; access constrained",control_and_approval:"Low visibility into plan limits",privacy_and_trust:"Not mentioned",pricing_or_usage_limit:"Annual payment plus monthly credit cap",current_alternative:"Chat-only mode",retention_churn_or_switching_signal:"Disappointed; churn unclear",sentiment:"Negative",evidence_excerpt:"[转述] 年订阅后才发现图片、PPT、音乐仍受积分限制",inclusion_status:"Hypothesis only",scope_class:"Core",date_confidence:"Year unknown",source_bias_note:"AE storefront does not prove reviewer country",researcher_note:"Do not use in UAE prevalence calculations without stronger geo"},
  {feedback_id:"FB-ARE-20260000-000011",product:"Genspark",product_tier:"A1 Direct",source_type:"App-store review",source_name:"Apple App Store",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",published_at:"",captured_at:capturedAt,country_or_region:"Possible Dubai",country_iso3:"ARE",country_confidence:"Medium",geo_evidence:"AE storefront + 'dxb' in alias; unverified",query_language:"en",content_language:"en",user_role:"General AI assistant user",company_size:"Individual",job_to_be_done:"Use a general AI assistant for single questions",trigger:"Trying Genspark as assistant",input_or_connected_tools:"Mobile app; prompts; tokens",expected_output:"Easy, predictable assistant interaction",actual_result:"Difficult to use and tokens consumed for each question",success_status:"Failed",failure_stage:"Interaction / cost",manual_interventions:"User considers switching tool",time_or_latency:"Not stated",setup_difficulty:"High",reliability:"Perceived low value",control_and_approval:"Token spend lacks predictability",privacy_and_trust:"Not mentioned",pricing_or_usage_limit:"Every question consumes tokens",current_alternative:"ChatGPT",retention_churn_or_switching_signal:"Explicit preference for ChatGPT",sentiment:"Negative",evidence_excerpt:"[转述] 难上手、每次提问都耗 token，倾向改用 ChatGPT",inclusion_status:"Hypothesis only",scope_class:"Core",date_confidence:"Year unknown",source_bias_note:"Alias is weak geo evidence",researcher_note:"Useful onboarding+price theme; medium is still non-core geo"},
  {feedback_id:"FB-ARE-20260000-000012",product:"Genspark",product_tier:"A1 Direct",source_type:"App-store review",source_name:"Apple App Store",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",published_at:"",captured_at:capturedAt,country_or_region:"UAE hypothesis pool",country_iso3:"ARE",country_confidence:"Low",geo_evidence:"AE storefront only",query_language:"en",content_language:"en",user_role:"Recent purchaser",company_size:"Unknown",job_to_be_done:"Continue using purchased AI workspace",trigger:"Within first month of purchase",input_or_connected_tools:"Paid mobile app",expected_output:"Service remains usable during paid period",actual_result:"App stopped working before one month elapsed",success_status:"Failed",failure_stage:"Access / service availability",manual_interventions:"None described",time_or_latency:"Failure within first month",setup_difficulty:"Not mentioned",reliability:"Low",control_and_approval:"Unable to restore access",privacy_and_trust:"Feels fraudulent to reviewer",pricing_or_usage_limit:"Paid period not delivered",current_alternative:"Stop using",retention_churn_or_switching_signal:"Explicit churn",sentiment:"Negative",evidence_excerpt:"[转述] 购买不到一个月即无法使用，并决定停用",inclusion_status:"Hypothesis only",scope_class:"Core",date_confidence:"Year unknown",source_bias_note:"AE storefront does not prove reviewer country",researcher_note:"Strong paid-access churn theme"},
  {feedback_id:"FB-ARE-20260000-000013",product:"Genspark",product_tier:"A1 Direct",source_type:"App-store review",source_name:"Apple App Store",source_url:"https://apps.apple.com/ae/app/genspark-ai-workspace/id6739554054?platform=iphone&see-all=reviews",published_at:"",captured_at:capturedAt,country_or_region:"Possible UAE",country_iso3:"ARE",country_confidence:"Medium",geo_evidence:"AE storefront + 'uae' in alias; unverified",query_language:"en/ar",content_language:"en",user_role:"Arabic-language user",company_size:"Unknown",job_to_be_done:"Produce accurate Arabic-language output",trigger:"Arabic use",input_or_connected_tools:"Arabic prompts/output",expected_output:"Correct Arabic output at acceptable price",actual_result:"Many Arabic-language mistakes",success_status:"Failed",failure_stage:"Localization / output quality",manual_interventions:"Likely correction, not stated",time_or_latency:"Not stated",setup_difficulty:"Not stated",reliability:"Low for Arabic output",control_and_approval:"Not mentioned",privacy_and_trust:"Not mentioned",pricing_or_usage_limit:"Price perceived high",current_alternative:"Unknown",retention_churn_or_switching_signal:"Not stated",sentiment:"Negative",evidence_excerpt:"[转述] 阿语错误较多，同时认为价格偏高",inclusion_status:"Hypothesis only",scope_class:"Core",date_confidence:"Year unknown",source_bias_note:"Alias and storefront are weak/medium geo evidence",researcher_note:"Important localization hypothesis requiring stronger UAE validation"},
  {feedback_id:"FB-ARE-20250516-000014",product:"Manus",product_tier:"A1 Direct",source_type:"App-store review",source_name:"Apple App Store",source_url:"https://apps.apple.com/ae/app/manus-ai-agent-automation/id6740909540?platform=iphone&see-all=reviews",published_at:"2025-05-16",captured_at:capturedAt,country_or_region:"UAE hypothesis pool",country_iso3:"ARE",country_confidence:"Low",geo_evidence:"AE storefront only",query_language:"en",content_language:"en",user_role:"Paid app user",company_size:"Unknown",job_to_be_done:"Run paid Manus tasks",trigger:"Paid use",input_or_connected_tools:"App; credits; email/in-app support",expected_output:"Task completion or no charge when errors occur",actual_result:"Errors prevented delivery while credits were deducted",success_status:"Failed",failure_stage:"Execution + billing + support",manual_interventions:"Repeated emails and in-app messages",time_or_latency:"Repeated attempts; no support response",setup_difficulty:"Not stated",reliability:"Low",control_and_approval:"Repeated payment attempts alleged without approval",privacy_and_trust:"Severe trust concern",pricing_or_usage_limit:"Credits charged on failures",current_alternative:"Unknown",retention_churn_or_switching_signal:"Explicit non-recommendation",sentiment:"Negative",evidence_excerpt:"[转述] 服务反复报错仍扣积分，客服也未响应",inclusion_status:"Hypothesis only",scope_class:"Core",date_confidence:"Exact",source_bias_note:"AE storefront does not prove reviewer country",researcher_note:"Rich failure chain but low geo confidence"},
  {feedback_id:"FB-ARE-20260000-000015",product:"Manus",product_tier:"A1 Direct",source_type:"App-store review",source_name:"Apple App Store",source_url:"https://apps.apple.com/ae/app/manus-ai-agent-automation/id6740909540?platform=iphone&see-all=reviews",published_at:"",captured_at:capturedAt,country_or_region:"UAE hypothesis pool",country_iso3:"ARE",country_confidence:"Low",geo_evidence:"AE storefront only",query_language:"en",content_language:"en",user_role:"Lite plan user",company_size:"Individual",job_to_be_done:"Complete a simple task",trigger:"Testing Lite plan",input_or_connected_tools:"Lite plan; 510 credits",expected_output:"Simple task at proportionate cost",actual_result:"Task consumed 510 credits; value did not justify subscription",success_status:"Partial",failure_stage:"Cost predictability",manual_interventions:"Compare with alternatives",time_or_latency:"Not stated",setup_difficulty:"Not stated",reliability:"Capability acceptable, economics not",control_and_approval:"Credit cost not predictable",privacy_and_trust:"Pricing model reduces trust",pricing_or_usage_limit:"510 credits for one simple task",current_alternative:"Unspecified better alternatives",retention_churn_or_switching_signal:"Would not subscribe; expects users to leave",sentiment:"Negative",evidence_excerpt:"[转述] 一个简单任务消耗 510 credits，认为不值得订阅",inclusion_status:"Hypothesis only",scope_class:"Core",date_confidence:"Year unknown",source_bias_note:"AE storefront does not prove reviewer country",researcher_note:"High-value pricing hypothesis; low UAE confidence"},
];

const dimensionCoverage = [
  {channel:"Trustpilot",sample_basis:"6 coded ARE rows",volume:2,date:3,rating:3,language:3,user_country:3,user_role:2,company_size:1,jtbd:2,workflow_steps:2,connected_tools:1,expected_output:2,actual_result:3,failure_stage:2,manual_intervention:2,time_latency:2,pricing_limits:3,support:3,privacy_trust:2,switching_retention:3,engagement:0,summary:"最适合国家标签+商业摩擦+迁移；任务深度不稳定"},
  {channel:"Apple App Store",sample_basis:"6 coded hypothesis rows",volume:3,date:2,rating:3,language:3,user_country:1,user_role:0,company_size:0,jtbd:2,workflow_steps:1,connected_tools:1,expected_output:2,actual_result:3,failure_stage:2,manual_intervention:1,time_latency:1,pricing_limits:3,support:2,privacy_trust:2,switching_retention:3,engagement:0,summary:"容易拿量和主题；国家归属最危险，必须降置信度"},
  {channel:"Reddit",sample_basis:"1 coded + 2 routed/excluded",volume:1,date:3,rating:0,language:3,user_country:2,user_role:1,company_size:1,jtbd:3,workflow_steps:3,connected_tools:3,expected_output:3,actual_result:3,failure_stage:2,manual_intervention:2,time_latency:2,pricing_limits:2,support:1,privacy_trust:2,switching_retention:3,engagement:3,summary:"命中率低但上下文最完整；需逐条确认地理并遵守 API 条款"},
  {channel:"Google Play",sample_basis:"1 excluded Arabic row",volume:3,date:3,rating:3,language:3,user_country:1,user_role:0,company_size:0,jtbd:2,workflow_steps:1,connected_tools:1,expected_output:1,actual_result:2,failure_stage:2,manual_intervention:1,time_latency:1,pricing_limits:3,support:2,privacy_trust:1,switching_retention:2,engagement:1,summary:"多语言主题发现可用；缺少可靠国家字段"},
  {channel:"YouTube",sample_basis:"discovery only; API not run",volume:3,date:3,rating:1,language:3,user_country:1,user_role:1,company_size:0,jtbd:2,workflow_steps:2,connected_tools:2,expected_output:2,actual_result:2,failure_stage:1,manual_intervention:1,time_latency:2,pricing_limits:1,support:1,privacy_trust:1,switching_retention:2,engagement:3,summary:"适合长评和评论规模；作者/评论者国家弱，需 API key"},
  {channel:"GitHub",sample_basis:"API surface tested; 0 target rows",volume:2,date:3,rating:0,language:3,user_country:0,user_role:0,company_size:0,jtbd:2,workflow_steps:3,connected_tools:3,expected_output:3,actual_result:3,failure_stage:3,manual_intervention:3,time_latency:2,pricing_limits:0,support:2,privacy_trust:2,switching_retention:1,engagement:3,summary:"技术故障最强，但本轮闭源竞品缺少官方 issues，地理也弱"},
  {channel:"Product Hunt",sample_basis:"0 ARE rows",volume:2,date:3,rating:1,language:3,user_country:1,user_role:2,company_size:1,jtbd:2,workflow_steps:1,connected_tools:1,expected_output:2,actual_result:2,failure_stage:1,manual_intervention:1,time_latency:1,pricing_limits:2,support:1,privacy_trust:1,switching_retention:2,engagement:3,summary:"适合新品/定位，国家归因与长期使用证据弱"},
  {channel:"G2/Capterra",sample_basis:"0 ARE rows; candidate",volume:2,date:3,rating:3,language:3,user_country:2,user_role:3,company_size:3,jtbd:3,workflow_steps:2,connected_tools:2,expected_output:2,actual_result:3,failure_stage:2,manual_intervention:2,time_latency:2,pricing_limits:2,support:2,privacy_trust:2,switching_retention:2,engagement:1,summary:"理论上最适合 B2B 画像，但需先确认竞品覆盖、筛选和授权"},
];

const codebook = [
  {field:"country_confidence",value:"High",definition:"正文或个人资料明确写出国家/城市；平台资料未独立验证时需在 geo_evidence 说明",decision_rule:"可进入国家核心样本，但仍保留来源偏差"},
  {field:"country_confidence",value:"Medium",definition:"本地 storefront/community 加另一条弱证据（如城市/币种/昵称）",decision_rule:"只用于假设和定性主题，不做强国家结论"},
  {field:"country_confidence",value:"Low",definition:"只有 storefront、语言或 regionCode 等单一弱信号",decision_rule:"不得计入国家高置信样本；只能进入假设池"},
  {field:"country_confidence",value:"Unknown",definition:"无法归属国家，或只有阿语/英语等跨国信号",decision_rule:"放 Global/Unknown 或排除"},
  {field:"scope_class",value:"Core",definition:"直接 agent/workspace/browser-agent 任务，或其关键执行/成本链路",decision_rule:"进入 Cowork 反馈主题分析"},
  {field:"scope_class",value:"Adjacent",definition:"一般 AI 产品、账单、客服等与 Cowork 相邻但非核心任务",decision_rule:"单独分析，不与核心成功率合并"},
  {field:"success_status",value:"Success",definition:"端到端完成且结果可直接使用",decision_rule:"必须能从正文判断实际结果"},
  {field:"success_status",value:"Partial",definition:"只完成部分步骤，或能力有效但需明显补救/受限",decision_rule:"记录失败/限制阶段"},
  {field:"success_status",value:"Failed",definition:"核心目标未完成、结果不可用或任务中断",decision_rule:"同时编码 failure_stage 与人工接管"},
  {field:"inclusion_status",value:"Included",definition:"国家证据与反馈内容都满足最低门槛",decision_rule:"至少含具体产品、可识别任务、实际结果/摩擦"},
  {field:"inclusion_status",value:"Hypothesis only",definition:"内容可编码，但地理归属只有 Low/Medium",decision_rule:"保留主题，不做 UAE 总体推断"},
  {field:"routing",value:"04 competitor feedback",definition:"具体竞品+工作任务+实际结果/摩擦",decision_rule:"进入反馈库"},
  {field:"routing",value:"05 country demand",definition:"表达工作需求/痛点，但不一定使用具体竞品",decision_rule:"转入国家公开需求库"},
  {field:"access",value:"Conditional",definition:"需要凭证、许可或条款评估",decision_rule:"不得因公开可见就默认批量抓取"},
];

const rawHeaders = ["feedback_id","product","product_scope","source_channel","source_name","source_url","source_item_hint","author_alias","published_at","published_at_raw","date_confidence","captured_at","query_language","content_language","geo_claim","country_iso3_candidate","geo_evidence","country_confidence","rating","author_context","task_summary","outcome_summary","friction_summary","pricing_signal","switching_signal","sentiment","capture_mode","original_text","original_text_translation_cn","evidence_excerpt","inclusion_status","exclusion_reason","duplicate_group","researcher_note"];
const codedHeaders = ["feedback_id","product","product_tier","source_type","source_name","source_url","published_at","captured_at","country_or_region","country_iso3","country_confidence","geo_evidence","query_language","content_language","user_role","company_size","job_to_be_done","trigger","input_or_connected_tools","expected_output","actual_result","success_status","failure_stage","manual_interventions","time_or_latency","setup_difficulty","reliability","control_and_approval","privacy_and_trust","pricing_or_usage_limit","current_alternative","retention_churn_or_switching_signal","sentiment","evidence_excerpt","inclusion_status","scope_class","date_confidence","source_bias_note","researcher_note"];

function rowsFromObjects(items, headers) {
  return items.map((item) => headers.map((header) => item[header] ?? null));
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function toCsv(items, headers) {
  return [headers.join(","), ...items.map((item) => headers.map((h) => csvEscape(item[h])).join(","))].join("\n") + "\n";
}

function columnName(index) {
  let result = "";
  let n = index + 1;
  while (n > 0) {
    const r = (n - 1) % 26;
    result = String.fromCharCode(65 + r) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

const palette = {
  navy: "#17324D",
  teal: "#0E7490",
  aqua: "#D9F0F4",
  sky: "#EAF5F8",
  sand: "#F4E8CF",
  cream: "#FBF7EE",
  orange: "#F97316",
  red: "#B42318",
  redLight: "#FDE8E7",
  green: "#13795B",
  greenLight: "#E4F3EC",
  yellow: "#F7C948",
  gray: "#667085",
  lightGray: "#EAECF0",
  white: "#FFFFFF",
};

function styleTitle(sheet, range, title) {
  range.merge();
  range.values = [[title]];
  range.format = {
    fill: palette.navy,
    font: { bold: true, color: palette.white, size: 18 },
    verticalAlignment: "center",
    rowHeight: 34,
  };
}

function styleTable(sheet, startRow, headers, dataRowCount, tableName) {
  const endCol = columnName(headers.length - 1);
  const headerRange = sheet.getRange(`A${startRow}:${endCol}${startRow}`);
  headerRange.format = {
    fill: palette.teal,
    font: { bold: true, color: palette.white },
    wrapText: true,
    verticalAlignment: "center",
    rowHeight: 32,
    borders: { preset: "outside", style: "thin", color: palette.navy },
  };
  if (dataRowCount > 0) {
    const full = sheet.getRange(`A${startRow}:${endCol}${startRow + dataRowCount}`);
    sheet.tables.add(full.address, true, tableName).style = "TableStyleMedium2";
    const body = sheet.getRange(`A${startRow + 1}:${endCol}${startRow + dataRowCount}`);
    body.format = { verticalAlignment: "top", wrapText: true };
  }
  sheet.freezePanes.freezeRows(startRow);
  sheet.showGridLines = false;
}

function setWidths(sheet, widths) {
  for (const [col, width] of Object.entries(widths)) sheet.getRange(`${col}:${col}`).format.columnWidth = width;
}

await fs.mkdir(pilotDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(renderDir, { recursive: true });

const languageHeaders = Object.keys(languageScope[0]);
const sourceHeaders = ["channel","access_status","public_access","machine_access","auth_or_rights","raw_found","coded_rows","high_geo_rows","dimensions_observed","geo_strength","main_bias","pilot_recommendation","pilot_test_outcome","source_url"];
const queryHeaders = Object.keys(queryLog[0]);
const coverageHeaders = Object.keys(dimensionCoverage[0]);
const codebookHeaders = Object.keys(codebook[0]);

await Promise.all([
  fs.writeFile(path.join(pilotDir, "01-country-language-scope.csv"), toCsv(languageScope, languageHeaders), "utf8"),
  fs.writeFile(path.join(pilotDir, "03-query-log.csv"), toCsv(queryLog, queryHeaders), "utf8"),
  fs.writeFile(path.join(pilotDir, "04-raw-feedback.csv"), toCsv(rawFeedback, rawHeaders), "utf8"),
  fs.writeFile(path.join(pilotDir, "05-coded-feedback.csv"), toCsv(codedFeedback, codedHeaders), "utf8"),
  fs.writeFile(path.join(pilotDir, "06-dimension-coverage.csv"), toCsv(dimensionCoverage, coverageHeaders), "utf8"),
  fs.writeFile(path.join(pilotDir, "08-codebook.csv"), toCsv(codebook, codebookHeaders), "utf8"),
]);

const workbook = Workbook.create();
workbook.comments.setSelf({ displayName: "User" });

// Create all sheets before any cross-sheet formulas.
const summary = workbook.worksheets.add("Pilot Summary");
const languageSheet = workbook.worksheets.add("Country & Language");
const feasibilitySheet = workbook.worksheets.add("Source Feasibility");
const querySheet = workbook.worksheets.add("Query Log");
const rawSheet = workbook.worksheets.add("Raw Feedback");
const codedSheet = workbook.worksheets.add("Coded Feedback");
const coverageSheet = workbook.worksheets.add("Coverage Matrix");
const codebookSheet = workbook.worksheets.add("Codebook");

// Country & Language.
styleTitle(languageSheet, languageSheet.getRange("A1:L1"), "阿联酋（ARE）国家—语言检索边界");
languageSheet.getRange("A2:L2").merge();
languageSheet.getRange("A2").values = [["规则：语言、storefront、regionCode 均不等于用户国家；国家归属单独记录证据与置信度。"]];
languageSheet.getRange("A2:L2").format = { fill: palette.sand, font: { color: palette.navy, italic: true }, wrapText: true, rowHeight: 28 };
languageSheet.getRange(`A4:${columnName(languageHeaders.length - 1)}${4 + languageScope.length}`).values = [languageHeaders, ...rowsFromObjects(languageScope, languageHeaders)];
styleTable(languageSheet, 4, languageHeaders, languageScope.length, "CountryLanguageTable");
setWidths(languageSheet, {A:11,B:12,C:22,D:24,E:12,F:13,G:12,H:32,I:52,J:30,K:48,L:13,M:46});
languageSheet.getRange(`A5:M${4 + languageScope.length}`).format.rowHeight = 54;
languageSheet.getRange("A10:L10").merge();
languageSheet.getRange("A10").values = [["Middle East guardrail：Saudi / UAE / Qatar / Kuwait / Bahrain / Oman 等必须分别设置 ISO3、国家锚点与语种组合；Arabic 只能作为 query_language，不能作为 country。"]];
languageSheet.getRange("A10:L10").format = { fill: palette.redLight, font: { color: palette.red, bold: true }, wrapText: true, rowHeight: 40 };

// Raw Feedback.
styleTitle(rawSheet, rawSheet.getRange("A1:AH1"), "Raw Feedback｜20 条发现记录（含排除与分流）");
rawSheet.getRange("A2:AH2").merge();
rawSheet.getRange("A2").values = [["original_text 保存可核验的最短原文证据片段，original_text_translation_cn 为中文翻译；空白表示未可靠取得，不用研究员转述冒充原话。"]];
rawSheet.getRange("A2:AH2").format = { fill: palette.sand, font: { color: palette.navy }, wrapText: true, rowHeight: 30 };
rawSheet.getRange(`A4:AH${4 + rawFeedback.length}`).values = [rawHeaders, ...rowsFromObjects(rawFeedback, rawHeaders)];
styleTable(rawSheet, 4, rawHeaders, rawFeedback.length, "RawFeedbackTable");
setWidths(rawSheet, {A:23,B:18,C:21,D:18,E:22,F:46,G:42,H:20,I:13,J:20,K:14,L:13,M:12,N:13,O:24,P:13,Q:38,R:14,S:9,T:28,U:35,V:38,W:38,X:34,Y:34,Z:12,AA:30,AB:42,AC:42,AD:42,AE:23,AF:32,AG:16,AH:38});
rawSheet.getRange(`A5:AH${4 + rawFeedback.length}`).format.rowHeight = 82;

// Coded Feedback.
styleTitle(codedSheet, codedSheet.getRange("A1:AM1"), "Coded Feedback｜13 条可编码记录");
codedSheet.getRange("A2:AM2").merge();
codedSheet.getRange("A2").values = [["7 条 High geo 进入 UAE 核心/相邻样本；6 条 App Store Low/Medium geo 只作为待验证主题假设。"]];
codedSheet.getRange("A2:AM2").format = { fill: palette.aqua, font: { color: palette.navy, bold: true }, wrapText: true, rowHeight: 28 };
codedSheet.getRange(`A4:AM${4 + codedFeedback.length}`).values = [codedHeaders, ...rowsFromObjects(codedFeedback, codedHeaders)];
styleTable(codedSheet, 4, codedHeaders, codedFeedback.length, "CodedFeedbackTable");
setWidths(codedSheet, {A:23,B:18,C:14,D:18,E:18,F:46,G:13,H:13,I:25,J:11,K:14,L:38,M:12,N:12,O:34,P:14,Q:40,R:30,S:38,T:38,U:42,V:14,W:26,X:30,Y:28,Z:24,AA:34,AB:34,AC:30,AD:34,AE:30,AF:38,AG:12,AH:42,AI:18,AJ:12,AK:14,AL:38,AM:38});
codedSheet.getRange(`A5:AM${4 + codedFeedback.length}`).format.rowHeight = 78;

// Query Log.
styleTitle(querySheet, querySheet.getRange("A1:M1"), "Query Log｜可复现检索与漏斗");
querySheet.getRange("A2:M2").merge();
querySheet.getRange("A2").values = [["记录 exact_query、国家锚点、时间窗、候选数、编码数和错国/错语种原因；搜索摘要不是原始证据。"]];
querySheet.getRange("A2:M2").format = { fill: palette.sand, font: { color: palette.navy }, wrapText: true, rowHeight: 28 };
querySheet.getRange(`A4:M${4 + queryLog.length}`).values = [queryHeaders, ...rowsFromObjects(queryLog, queryHeaders)];
styleTable(querySheet, 4, queryHeaders, queryLog.length, "QueryLogTable");
setWidths(querySheet, {A:15,B:20,C:22,D:14,E:56,F:26,G:28,H:22,I:14,J:13,K:20,L:34,M:48});
querySheet.getRange(`A5:M${4 + queryLog.length}`).format.rowHeight = 48;

// Source Feasibility with formula-derived pilot counts.
styleTitle(feasibilitySheet, feasibilitySheet.getRange("A1:N1"), "Source Feasibility｜渠道可抓性与能拿到的字段");
feasibilitySheet.getRange("A2:N2").merge();
feasibilitySheet.getRange("A2").values = [["raw_found / coded_rows / high_geo_rows 从 Raw Feedback 与 Coded Feedback 公式汇总；可访问不等于允许批量抓取。"]];
feasibilitySheet.getRange("A2:N2").format = { fill: palette.aqua, font: { color: palette.navy, bold: true }, wrapText: true, rowHeight: 28 };
const sourceBaseHeaders = ["channel","access_status","public_access","machine_access","auth_or_rights"];
const sourceTailHeaders = ["dimensions_observed","geo_strength","main_bias","pilot_recommendation","pilot_test_outcome","source_url"];
const sourceRows = sourceFeasibility.map((s) => [s.channel,s.access_status,s.public_access,s.machine_access,s.auth_or_rights,null,null,null,s.dimensions_observed,s.geo_strength,s.main_bias,s.pilot_recommendation,s.pilot_test_outcome,s.source_url]);
feasibilitySheet.getRange(`A4:N${4 + sourceRows.length}`).values = [sourceHeaders, ...sourceRows];
for (let row = 5; row <= 4 + sourceRows.length; row++) {
  feasibilitySheet.getRange(`F${row}`).formulas = [[`=COUNTIF('Raw Feedback'!$D$5:$D$100,A${row})`]];
  feasibilitySheet.getRange(`G${row}`).formulas = [[`=COUNTIF('Coded Feedback'!$E$5:$E$100,A${row})`]];
  feasibilitySheet.getRange(`H${row}`).formulas = [[`=COUNTIFS('Coded Feedback'!$E$5:$E$100,A${row},'Coded Feedback'!$K$5:$K$100,"High")`]];
}
styleTable(feasibilitySheet, 4, sourceHeaders, sourceRows.length, "SourceFeasibilityTable");
setWidths(feasibilitySheet, {A:23,B:20,C:34,D:34,E:34,F:12,G:12,H:14,I:46,J:32,K:40,L:46,M:42,N:50});
feasibilitySheet.getRange(`F5:H${4 + sourceRows.length}`).format.numberFormat = "0";
feasibilitySheet.getRange(`A5:N${4 + sourceRows.length}`).format.rowHeight = 72;

// Coverage Matrix.
styleTitle(coverageSheet, coverageSheet.getRange("A1:W1"), "Coverage Matrix｜0–3 字段覆盖评分");
coverageSheet.getRange("A2:W2").merge();
coverageSheet.getRange("A2").values = [["0=通常拿不到；1=偶发/弱；2=部分可拿；3=稳定可拿。评分是本轮渠道能力判断，不是市场评分。"]];
coverageSheet.getRange("A2:W2").format = { fill: palette.sand, font: { color: palette.navy }, wrapText: true, rowHeight: 28 };
coverageSheet.getRange(`A4:W${4 + dimensionCoverage.length}`).values = [coverageHeaders, ...rowsFromObjects(dimensionCoverage, coverageHeaders)];
styleTable(coverageSheet, 4, coverageHeaders, dimensionCoverage.length, "CoverageMatrixTable");
setWidths(coverageSheet, {A:21,B:28,C:10,D:10,E:10,F:10,G:13,H:11,I:13,J:12,K:14,L:14,M:15,N:14,O:15,P:14,Q:13,R:14,S:13,T:15,U:16,V:14,W:50});
coverageSheet.getRange(`C5:V${4 + dimensionCoverage.length}`).format.numberFormat = "0";
coverageSheet.getRange(`C5:V${4 + dimensionCoverage.length}`).conditionalFormats.add("colorScale", { colors: [palette.redLight, palette.sand, palette.greenLight], thresholds: ["min", "50%", "max"] });
coverageSheet.getRange(`A5:W${4 + dimensionCoverage.length}`).format.rowHeight = 42;

// Codebook.
styleTitle(codebookSheet, codebookSheet.getRange("A1:D1"), "Codebook｜国家、范围、纳入与成功状态");
codebookSheet.getRange(`A3:D${3 + codebook.length}`).values = [codebookHeaders, ...rowsFromObjects(codebook, codebookHeaders)];
styleTable(codebookSheet, 3, codebookHeaders, codebook.length, "CodebookTable");
setWidths(codebookSheet, {A:24,B:24,C:70,D:62});
codebookSheet.getRange(`A4:D${3 + codebook.length}`).format.rowHeight = 36;

// Summary dashboard.
styleTitle(summary, summary.getRange("A1:H1"), "UAE 竞品反馈示意包｜渠道可抓性 × 数据维度 × 地理可信度");
summary.getRange("A2:H2").merge();
summary.getRange("A2").values = [["Pilot country: United Arab Emirates (ARE) · Core query languages: Arabic + English · Capture date: 2026-09-03"]];
summary.getRange("A2:H2").format = { fill: palette.sky, font: { color: palette.navy }, rowHeight: 24 };
summary.getRange("A4:B4").merge(); summary.getRange("C4:D4").merge(); summary.getRange("E4:F4").merge(); summary.getRange("G4:H4").merge();
summary.getRange("A4").values = [["发现记录"]]; summary.getRange("C4").values = [["可编码记录"]]; summary.getRange("E4").values = [["High geo"]]; summary.getRange("G4").values = [["Core Cowork"]];
summary.getRange("A5:B6").merge(); summary.getRange("C5:D6").merge(); summary.getRange("E5:F6").merge(); summary.getRange("G5:H6").merge();
summary.getRange("A5").formulas = [["=COUNTA('Raw Feedback'!$A$5:$A$100)"]];
summary.getRange("C5").formulas = [["=COUNTA('Coded Feedback'!$A$5:$A$100)"]];
summary.getRange("E5").formulas = [["=COUNTIF('Coded Feedback'!$K$5:$K$100,\"High\")"]];
summary.getRange("G5").formulas = [["=COUNTIF('Coded Feedback'!$AJ$5:$AJ$100,\"Core\")"]];
summary.getRange("A4:H4").format = { fill: palette.teal, font: { bold: true, color: palette.white }, horizontalAlignment: "center" };
summary.getRange("A5:H6").format = { fill: palette.aqua, font: { bold: true, color: palette.navy, size: 24 }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: palette.teal } };
summary.getRange("A8:H8").merge(); summary.getRange("A8").values = [["本轮最重要的渠道判断"]];
summary.getRange("A8:H8").format = { fill: palette.navy, font: { bold: true, color: palette.white }, rowHeight: 24 };
const keyFindings = [
  ["1", "Trustpilot", "最稳定获得 profile-country、任务、价格/积分、客服、流失；但主动评价/投诉偏差明显。"],
  ["2", "Apple App Store", "最容易拿量与发现主题；UAE storefront 不能证明作者在 UAE，只能 Low/Medium geo。"],
  ["3", "Reddit", "命中率最低，但明确自述 Dubai 的个案可同时覆盖本地上下文、任务链路和替代订阅。"],
  ["4", "Arabic search", "阿语结果大量混入 Saudi/Egypt/Iraq/全球内容；语言必须和国家证据分栏。"],
  ["5", "API reality", "YouTube 需 key，Product Hunt 需 token；Apple/Google 开发者评论 API 不能导出竞争对手评论。"],
];
summary.getRange("A9:H13").values = keyFindings.map(([n,c,f]) => [n,c,f,null,null,null,null,null]);
for (let row = 9; row <= 13; row++) summary.getRange(`C${row}:H${row}`).merge();
summary.getRange("A9:H13").format = { fill: palette.cream, wrapText: true, verticalAlignment: "center", rowHeight: 42, borders: { preset: "inside", style: "thin", color: palette.lightGray } };
summary.getRange("A9:A13").format = { font: { bold: true, color: palette.orange, size: 14 }, horizontalAlignment: "center" };
summary.getRange("B9:B13").format = { font: { bold: true, color: palette.navy } };
summary.getRange("A15:H15").merge(); summary.getRange("A15").values = [["高置信样本出现的可行动主题（不是总体占比）"]];
summary.getRange("A15:H15").format = { fill: palette.navy, font: { bold: true, color: palette.white }, rowHeight: 24 };
summary.getRange("A16:B16").merge(); summary.getRange("C16:D16").merge(); summary.getRange("E16:F16").merge(); summary.getRange("G16:H16").merge();
summary.getRange("A16").values = [["Failed"]]; summary.getRange("C16").values = [["Pricing/limits"]]; summary.getRange("E16").values = [["Switching signal"]]; summary.getRange("G16").values = [["Positive retention"]];
summary.getRange("A17:B18").merge(); summary.getRange("C17:D18").merge(); summary.getRange("E17:F18").merge(); summary.getRange("G17:H18").merge();
summary.getRange("A17").formulas = [["=COUNTIFS('Coded Feedback'!$K$5:$K$100,\"High\",'Coded Feedback'!$V$5:$V$100,\"Failed\")"]];
summary.getRange("C17").formulas = [["=COUNTIFS('Coded Feedback'!$K$5:$K$100,\"High\",'Coded Feedback'!$AD$5:$AD$100,\"<>\")"]];
summary.getRange("E17").formulas = [["=COUNTIFS('Coded Feedback'!$K$5:$K$100,\"High\",'Coded Feedback'!$AF$5:$AF$100,\"<>\")"]];
summary.getRange("G17").formulas = [["=COUNTIFS('Coded Feedback'!$K$5:$K$100,\"High\",'Coded Feedback'!$AG$5:$AG$100,\"Positive\")"]];
summary.getRange("A16:H16").format = { fill: palette.teal, font: { bold: true, color: palette.white }, horizontalAlignment: "center" };
summary.getRange("A17:H18").format = { fill: palette.sky, font: { bold: true, color: palette.navy, size: 20 }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: palette.teal } };
summary.getRange("A20:H20").merge(); summary.getRange("A20").values = [["使用边界"]];
summary.getRange("A20:H20").format = { fill: palette.red, font: { bold: true, color: palette.white } };
summary.getRange("A21:H23").merge();
summary.getRange("A21").values = [["这是渠道与字段能力试跑，不是 UAE 市场规模或偏好统计。High geo 也只是来源中的明确国家资料/自述，未独立验证身份；App Store Low/Medium 样本不得并入高置信占比。正式扩样前应先做双人编码校准，再设每个产品×渠道×语言的配额。"]];
summary.getRange("A21:H23").format = { fill: palette.redLight, font: { color: palette.red }, wrapText: true, verticalAlignment: "center", rowHeight: 26 };
setWidths(summary, {A:10,B:20,C:15,D:15,E:15,F:15,G:16,H:16});
summary.freezePanes.freezeRows(2);
summary.showGridLines = false;

// Conditional formatting for key status columns.
rawSheet.getRange(`R5:R${4 + rawFeedback.length}`).conditionalFormats.add("containsText", { text: "High", format: { fill: palette.greenLight, font: { color: palette.green, bold: true } } });
rawSheet.getRange(`R5:R${4 + rawFeedback.length}`).conditionalFormats.add("containsText", { text: "Low", format: { fill: palette.redLight, font: { color: palette.red } } });
codedSheet.getRange(`K5:K${4 + codedFeedback.length}`).conditionalFormats.add("containsText", { text: "High", format: { fill: palette.greenLight, font: { color: palette.green, bold: true } } });
codedSheet.getRange(`V5:V${4 + codedFeedback.length}`).conditionalFormats.add("containsText", { text: "Failed", format: { fill: palette.redLight, font: { color: palette.red, bold: true } } });
codedSheet.getRange(`V5:V${4 + codedFeedback.length}`).conditionalFormats.add("containsText", { text: "Success", format: { fill: palette.greenLight, font: { color: palette.green, bold: true } } });

// Comments for audit-critical assumptions.
workbook.comments.addThread({ cell: summary.getRange("E5") }, "High geo means explicit source profile/body location evidence; it is not independent identity verification.");
workbook.comments.addThread({ cell: languageSheet.getRange("D5") }, "Arabic is a query language, never a substitute for country attribution.");

// Export source-feasibility CSV after formula-independent data population.
const sourceCsvItems = sourceFeasibility.map((s) => ({
  ...s,
  raw_found: rawFeedback.filter((row) => row.source_channel === s.channel).length,
  coded_rows: codedFeedback.filter((row) => row.source_name === s.channel).length,
  high_geo_rows: codedFeedback.filter((row) => row.source_name === s.channel && row.country_confidence === "High").length,
}));
await fs.writeFile(path.join(pilotDir, "02-source-feasibility.csv"), toCsv(sourceCsvItems, sourceHeaders), "utf8");

const summaryInspect = await workbook.inspect({ kind: "table", range: "Pilot Summary!A1:H23", include: "values,formulas", tableMaxRows: 25, tableMaxCols: 10, maxChars: 7000 });
const feasibilityInspect = await workbook.inspect({ kind: "table", range: "Source Feasibility!A1:N16", include: "values,formulas", tableMaxRows: 18, tableMaxCols: 14, maxChars: 9000 });
const originalTextInspect = await workbook.inspect({ kind: "table", range: "Raw Feedback!AA4:AH10", include: "values,formulas", tableMaxRows: 8, tableMaxCols: 8, maxChars: 7000 });
const errorInspect = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan", maxChars: 5000 });
console.log(JSON.stringify({ summaryInspect: summaryInspect.ndjson, feasibilityInspect: feasibilityInspect.ndjson, originalTextInspect: originalTextInspect.ndjson, errorInspect: errorInspect.ndjson }));

for (const sheetName of ["Pilot Summary","Country & Language","Source Feasibility","Query Log","Raw Feedback","Coded Feedback","Coverage Matrix","Codebook"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  const safeName = sheetName.replaceAll(" ", "-").replaceAll("&", "and");
  await fs.writeFile(path.join(renderDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const outputPath = path.join(outputDir, "uae-competitor-feedback-pilot.xlsx");
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(JSON.stringify({ outputPath, renderDir, rawCount: rawFeedback.length, codedCount: codedFeedback.length }));
