---
name: campus-radar
description: >
  监控全国范围校园招聘中新开放的正式校招岗位，目标岗位方向/届别/招聘季节/是否含实习
  均由 config.json 配置驱动，可用于任意行业方向。首次使用时会主动向用户提问确认这些
  设置，不预设任何默认方向。去重后生成日报并导出 Excel 追踪表。当需要手动触发一次
  监控、检查监控状态、或修改监控方向/关键词/公司范围时使用此技能。
version: "2.0.0"
user_invocable: true
metadata:
  author: campus-radar
  version: "2.0.0"
---

# 秋招岗位监控

目录约定（不要写死用户名、家目录或安装位置）：

```
SKILL_DIR=.
```

执行本文件中的命令时，以当前这份 `SKILL.md` 所在目录作为工作目录，并使用相对于该目录的路径。所有配置、状态、脚本和参考文档都从这里解析，禁止使用发布者机器上的绝对路径或固定技能 ID。

- 配置：`$SKILL_DIR/config.json`（目标届别/季节/岗位方向/是否含实习/关键词，全部在这里改，不需要碰代码或其他文档；首次使用时该文件可能不存在或 `onboarded` 为 `false`，见第 0 步）、`$SKILL_DIR/config.example.json`（未初始化时的模板，不要直接改这个文件）
- 状态：`$SKILL_DIR/state/seen_postings.json`
- 脚本：`$SKILL_DIR/scripts/dedupe.py`、`$SKILL_DIR/scripts/digest.py`、`$SKILL_DIR/scripts/export_excel.py`、`$SKILL_DIR/scripts/add_posting.py`（手动录入岗位）
- 参考文档：`$SKILL_DIR/references/sources.md`（数据源与兜底策略）、
  `$SKILL_DIR/references/keyword-filters.md`（岗位方向/实习/届别过滤逻辑，具体关键词读 config.json）、
  `$SKILL_DIR/references/industry-map.md`（行业搜索覆盖方案，确保不漏行业）、
  `$SKILL_DIR/references/digest-format.md`（日报格式，仅供理解 `digest.py` 输出，不需要手写格式化逻辑）。

如果本次运行是定时任务（无人值守）：**不要**使用 AskUserQuestion 或以任何方式等待用户输入；遇到不确定情况一律按本文件和 references 中的默认策略自主处理，并在最终回复里如实说明做了什么假设。（第 0 步的初始化提问例外——那一步专门规定了无人值守场景下应该怎么做，见下文。）

## 执行步骤

### 0. 首次使用初始化（仅当尚未完成初始化时触发）

读取 `$SKILL_DIR/config.json`；如果这个文件不存在，先把 `$SKILL_DIR/config.example.json` 复制一份成 `$SKILL_DIR/config.json`。

检查 `onboarded` 字段：

- **如果 `onboarded` 不是 `true`，且当前是有用户在场的交互式会话**（不是无人值守的定时任务）：这是用户第一次使用这个技能，此时**不要**凭空瞎猜方向直接开始搜索，必须先通过对话（优先用 AskUserQuestion 等提问工具，没有就直接用文字提问）向用户确认这几个找工作的人最关心的问题：
  1. **目标届别**——比如"2027届"，也可以是社招/无届别限制。
  2. **想投递的行业/岗位方向**——用大白话描述就行，比如"技术开发，前端后端都要"、"市场营销"、"财务"、"不限方向"。不需要用户自己列关键词——拿到回答后，由你自己根据这个行业方向的常见细分职能，归纳出一组合理的 `positive_keywords`（覆盖该方向常见的岗位名称/职能词）、可选的 `fuzzy_keywords`（比如笼统的"管理培训生"）、以及几个明显不相关方向作为 `negative_keywords` 兜底。
  3. **要不要包含实习岗位**——只要正式校招，还是也要看实习/实习转正。
  4. **对应的招聘季节**——比如"2026秋招"还是"2026春招"，用于生成 `target_season_label`；并据此推算一个合理的 `season_end_date`（这一季大概什么时候结束、该归档重来，秋招一般到次年2月左右，春招一般到当年7月左右，不需要再单独问用户，除非用户主动想自定义）。

   问完之后，把这些信息写进 `$SKILL_DIR/config.json`（`target_grad_year`、`target_season_label`、`season_end_date`、`job_category_label`、`include_internships`、`job_filter.positive_keywords`/`fuzzy_keywords`/`negative_keywords`），并把 `onboarded` 设为 `true`。`job_filter.intern_exclusion_keywords` 和 `job_filter.formal_recruit_keywords` 这两组是通用的，`config.example.json` 里已经有合理默认值，一般不需要改。**然后按 `references/industry-map.md` 中的方案生成行业搜索地图，写入 `config.json` 的 `industry_map` 字段**——根据用户选择的岗位方向，列出所有相关行业（不要遗漏制造业、传统行业中的嵌入式/技术岗），为每个 positive_keyword 生成同义词列表，并生成各行业的代表公司。写完后用一段话跟用户确认一遍设置摘要，再继续往下执行第 1 步。

- **如果 `onboarded` 不是 `true`，但当前是无人值守的定时任务运行**：说明用户还没有完成初始化设置。不要凭空猜测方向瞎跑一通。直接在最终回复里如实说明"这个技能还没有完成初始化设置，请先手动运行一次、回答几个方向设置问题后再启用定时任务"，然后结束本次运行，不要往下执行发现流程。

- **如果 `onboarded` 已经是 `true`**：跳过这一步，直接进入第 1 步。

### 1. 读取配置

读取 `$SKILL_DIR/config.json`，获取 `target_grad_year`、`target_season_label`、`job_category_label`、`include_internships`、`job_filter`、`industry_map`（行业搜索地图）等参数。如果 `industry_map` 不存在（旧版配置），仅按关键词搜索。下文所有 `{job_category_label}`、`{target_grad_year}` 均指代这里读到的实际值。

### 2. 并行发现（4 个子 agent）

先读 `$SKILL_DIR/references/sources.md`，按其中的来源分组，用 Agent 工具在**同一条消息里并行**发起 4 个子任务（general-purpose 类型，需要能用 Skill/WebSearch/WebFetch 等联网工具）：

1. 牛客网 求职/校招板块
2. 公司招聘微信公众号 + 官网详情（搜索"XX招聘"公众号发布的秋招公告，跳转官网核实岗位）—— 这是中国大陆校招信息发布的一手链路，优先级高
3. 51job校园招聘 + 智联招聘校园 + 猎聘校园官方频道（合并一个子任务）
4. 门户/公众号"秋招名单/时间表"汇总贴 + 实习僧(shixiseng.com)（WebSearch 发现新公司名单）

每个子 agent 的 prompt 必须：
- 显式包含「必须加载 web-access skill 并遵循指引」这句话。
- 用目标性措辞下达任务，把 config.json 里的 `job_category_label`、`target_grad_year` 实际值代入（例如："调研牛客网上有哪些{job_category_label}方向的{target_grad_year}届秋招正式岗位，覆盖全国范围"），不要指定具体方法动词（不要写"用WebSearch搜索"之类）。
- **如果 config.json 中有 `industry_map`，必须将其中的行业列表和关键词同义词完整代入子 agent prompt**。明确告知子 agent："该方向不仅出现在科技公司，还分布在以下行业中：{industry_list}。请按行业逐个搜索，不要只搜科技/互联网公司。" 同时附上 `keyword_synonyms` 中的同义词列表，让子 agent 用同义词扩展搜索范围。
- 要求返回结构化列表，字段：`company`（公司名称）、`title`（职位名称）、`city`（工作城市，无法判断写"未注明"）、`highlight`（岗位亮点，一句话）、`source_url`（原始链接，保留完整参数）、`apply_url`（该岗位的官方网申/投递入口链接，如 campus.xxx.com/apply/xxx；若找到了公司的校招官网主页但没找到岗位详情页，可以用官网主页；完全找不到时留空字符串）、`deadline`（网申截止日期，格式 YYYY-MM-DD；如果招聘信息中提到了截止日期就填，没提到就留空）、`source_platform`（来源栏目名称）。
- 说明：若该来源当天无法访问或没有相关信息，直接如实汇报为空，不要反复重试同一种方式。
- **显式禁止子 agent 再自行派发下一层子 agent**（写清楚"必须自己直接完成调研，不得再调用 Agent 工具委托其他子 agent"）。实测发现子 agent 会倾向于"逐个公司开子任务核实"，导致任务树无限展开、耗时和成本失控。正确做法是用该平台自身的搜索/筛选/关键词功能一次性检索，而不是一家家公司点开核实。
- 给每个子 agent 一个明确的范围上限提示，例如"最多深入核实10-15家最相关的公司，覆盖面比逐一核实的精确度更重要"，避免无限深挖单一路径。
- **额外要求：对每个岗位，除了找到信息来源链接外，还要尽力找到该公司的官方网申/投递入口**（公司的官方校招网站上的岗位详情页或投递页面）。`apply_url` 字段尽量填官方投递页面，不要填第三方聚合平台的链接。

等待 4 个子 agent 全部返回。某个子 agent 为空或失败不影响其余结果的处理——继续往下走，不要中断整体流程。

### 3. 合并 + 过滤

把 4 份结构化列表合并成一个数组。读 `$SKILL_DIR/references/keyword-filters.md` 了解过滤逻辑，按 `config.json` 的 `job_filter` 字段执行：
- 命中 `positive_keywords` 任一 → 保留。
- 命中 `fuzzy_keywords`、但未注明具体方向 → 保留，标题末尾加 `[方向待确认]`。
- 命中 `intern_exclusion_keywords`（含"实习转正"）→ 排除，无论是否也命中 `formal_recruit_keywords`；**但如果 `config.json` 的 `include_internships` 为 `true`，这一条整体跳过，实习岗位正常保留**。
- 明确写出早于 `target_grad_year` 的届别 → 排除。
- 其余按 `references/keyword-filters.md` 中的规则处理。
- 地域不过滤，`city` 字段照抄原文。

把过滤后的候选列表写成 JSON 数组文件，例如 `$SKILL_DIR/candidates.json`（字段同第 2 步，含 `apply_url` 和 `deadline`）��

### 4. 去重

运行：

```
python3 $SKILL_DIR/scripts/dedupe.py \
  --input $SKILL_DIR/candidates.json \
  --state $SKILL_DIR/state/seen_postings.json \
  --config $SKILL_DIR/config.json \
  --output $SKILL_DIR/new_only.json
```

这一步会原地更新 `state/seen_postings.json`（新岗位写入、已见岗位刷新 `last_confirmed`、过季自动归档），并把真正新增的岗位输出到 `--output` 指定的文件。

### 5. 核实新公司 + 捕获网申入口（可选，有上限）

在 `$SKILL_DIR/new_only.json` 中，找出"公司此前从未出现过"的记录（即该公司在 `state/seen_postings.json` 里除了这条新记录外没有其他历史岗位）。最多取 5 家这样的新公司，为每家发起一个子 agent（同样要求"必须加载 web-access skill 并遵循指引"，目标是"在该公司官方校园招聘官网核实这个岗位是否存在，若存在返回权威链接和网申投递入口"）。

子 agent 的 prompt 须额外包含：**除了核实岗位是否存在外，还要尽力找到该岗位的官方网申/投递入口链接（如 campus.xxx.com/apply/xxx），返回时用 `apply_url` 字段携带。如果找到了比当前 `source_url` 更精准的官方岗位详情页，也一并更新 `source_url`。**

若核实到官方链接或网申入口，直接编辑 `$SKILL_DIR/new_only.json` 和 `state/seen_postings.json` 中对应记录的 `source_url`/`source_platform`/`apply_url` 字段。若核实过程中发现该岗位实际届别不符合目标届别（例如页面明确写着更早的届别），应从 `$SKILL_DIR/new_only.json` 和 `state/seen_postings.json` 中移除该记录，不计入本次新增。核实失败（官网打不开、找不到对应信息）或该公司超过 5 家上限的，保留原聚合帖链接不变，`apply_url` 留空，不需要额外说明。

### 6. 渲染日报

```
python3 $SKILL_DIR/scripts/digest.py render \
  --new $SKILL_DIR/new_only.json \
  --state $SKILL_DIR/state/seen_postings.json \
  --config $SKILL_DIR/config.json \
  --date $(date +%F)
```

### 7. 更新 Excel 岗位追踪表

运行导出脚本，将所有已发现岗位（含本次新增）写入/更新到 Excel 文件中。该脚本会保留用户在 Excel 中手动编辑的「投递状态」和「面经参考」列，其余列从 state 数据刷新。

```
python3 $SKILL_DIR/scripts/export_excel.py \
  --state $SKILL_DIR/state/seen_postings.json \
  --config $SKILL_DIR/config.json
```

Excel 文件默认输出到 `$SKILL_DIR/{job_category_label}_岗位追踪.xlsx`（如 `嵌入式_岗位追踪.xlsx`），包含以下列：

| 列 | 说明 |
|---|---|
| 序号 / 公司 / 岗位名称 / 城市 / 岗位亮点 | 基础信息 |
| 匹配度 | 根据正向关键词命中数自动评分（⭐~⭐⭐⭐⭐⭐） |
| 来源链接 / 投递入口 | 可点击的蓝色超链接 |
| 面经参考 | 自动生成牛客网面经搜索链接，用户可替换为具体面经帖 |
| 来源平台 / 首次发现 / 最后确认 | 追踪信息 |
| **投递状态** | **用户手动编辑**：未投递/已投递/笔试中/面试中/已offer/已挂/不感兴趣，选状态后整行自动变色 |

投递状态列使用单元格下拉菜单（数据验证），选择状态后通过 Excel 条件格式实现整行自动变色。无列头筛选按钮。

### 8. 输出最终回复

最终回复内容 = `digest.py render` 的 stdout 输出，原样输出即可，不需要额外包装。如果有新增岗位，在日报末尾附上一句提示用户查看更新后的 Excel 文件路径。

无论有没有新增岗位，都必须正常输出一份日报（`digest.py render` 已经处理了"无新增"分支），不要空手结束任务。

## 多岗位方向监控

如果需要同时监控多个方向（如嵌入式 + 硬件 + 物联网），按以下步骤操作：

1. 复制一份 `config.json`，命名为 `config_{方向}.json`（如 `config_hardware.json`）
2. 修改其中的 `job_category_label`、`job_filter.positive_keywords`/`fuzzy_keywords`/`negative_keywords`
3. 运行时指定对应的 config 和 state 文件：

```
python3 scripts/dedupe.py --input candidates_hardware.json --state state/seen_postings_hardware.json --config config_hardware.json --output new_only_hardware.json
python3 scripts/export_excel.py --state state/seen_postings_hardware.json --config config_hardware.json
```

每个方向会生成独立的 Excel 文件（如 `硬件_岗位追踪.xlsx`）和独立的 state 文件，互不干扰。

## 手动录入岗位

用户自己找到的岗位（小公司、内推、线下招聘会等）也可以加入追踪表，和自动发现的岗位统一管理。

### 交互模式（推荐）

```
python3 $SKILL_DIR/scripts/add_posting.py \
  --state $SKILL_DIR/state/seen_postings.json \
  --config $SKILL_DIR/config.json
```

会逐项提示输入：公司名称、岗位名称、城市、亮点、链接、截止日期等。输入完一条问是否继续，可以连续添加。`来源平台` 默认为「手动添加」，也可以改成「内推」「招聘会」等。

### 命令行模式（单条快速添加）

```
python3 scripts/add_posting.py \
  --state state/seen_postings.json --config config.json \
  --company "某某科技" --title "嵌入式工程师" --city "深圳" \
  --highlight "STM32方向" --apply-url "https://campus.xxx.com/apply" \
  --deadline "2026-09-30" --source-platform "内推"
```

### 批量导入

准备一个 JSON 文件（格式同 candidates.json），一次导入多条：

```
python3 scripts/add_posting.py \
  --state state/seen_postings.json --config config.json \
  --import my_postings.json
```

### 去重

手动添加的岗位同样走去重逻辑（公司名+岗位名），重复的会自动跳过。添加后运行 `export_excel.py` 即可在 Excel 中看到新添加的岗位。
