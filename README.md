# 📡 Campus Radar

> *让找工作不再靠手动刷网站 — AI 驱动的校招岗位雷达*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Cross--platform-lightgrey" alt="Platform">
  <a href="https://github.com/xiaoxiaobaijiangjun/campus-radar"><img src="https://img.shields.io/github/stars/xiaoxiaobaijiangjun/campus-radar?style=social" alt="Stars"></a>
</p>

---

## 🚀 快速开始

### 前置要求

- **Python 3.10+**
- **pip install openpyxl**（或 `pip install -r requirements.txt`）
- 一个支持 Agent / WebSearch 的 AI 助手（WorkBuddy、OpenCode、Cursor、Windsurf 等）

### 安装

```bash
git clone https://github.com/xiaoxiaobaijiangjun/campus-radar.git
cd campus-radar
pip install -r requirements.txt
```

### 初始化

把项目目录告诉 AI，说：

> 「帮我安装 campus-radar 技能并初始化」

AI 会问你：目标届别、岗位方向、是否看实习、招聘季节。回答完自动开始第一次搜索。

---

## 💬 日常使用

| 你说的话 | AI 做什么 |
|---------|----------|
| **跑一次监控** | 手动执行完整搜索 → 推送日报 + 更新 Excel |
| **每天自动运行** | 创建定时任务，到点自动搜索 |
| **把方向改成 XX** | 更新 config.json 关键词 |
| **加一个方向，看 XX 方向的岗位** | 创建第二份配置，独立监控新方向 |
| **有多少岗位了** | 读取 state 汇报统计 |
| **手动加一个岗位** | 运行 add_posting.py 交互录入 |

每次运行后自动更新 Excel 追踪表（每个方向独立生成 `{方向}_岗位追踪.xlsx`），你可以在 Excel 里手动标记投递状态，选状态后整行自动变色。

### 📝 手动录入岗位

自己找到的岗位（小公司、内推、招聘会等）也能统一进追踪表：

```bash
# 交互模式 — 逐项输入，支持连续添加
python3 scripts/add_posting.py --state state/seen_postings.json --config config.json

# 命令行模式 — 快速添加单条
python3 scripts/add_posting.py --state state/seen_postings.json --config config.json \
  --company "XXX科技" --title "软件开发工程师" --city "深圳"

# 批量导入 — 从 JSON 文件一次导入多条
python3 scripts/add_posting.py --state state/seen_postings.json --config config.json \
  --import my_postings.json
```

手动添加的岗位和自动发现的岗位统一管理，同样走去重逻辑，同样出现在 Excel 追踪表中。

---

## ✨ 核心特性

- 🔍 **多源并行发现** — 牛客网、公司公众号/官网、51job/智联/猎聘、实习僧，4 路同时搜索
- 🏭 **行业覆盖** — 初始化时自动生成行业搜索地图，确保不遗漏制造业/传统行业中的岗位
- 🧠 **智能去重** — 公司+岗位+URL 三元组哈希，同一条不会重复出现
- 🎯 **关键词过滤** — 正向/模糊/负向三级体系 + 同义词扩展，适配任意行业方向
- ⏰ **截止日期追踪** — 日报中自动显示截止倒计时提醒
- ⭐ **匹配度评分** — 按关键词命中数 ⭐~⭐⭐⭐⭐⭐
- 🔗 **网申入口直达** — 尽量找官方投递链接，省去二次搜索
- 📊 **Excel 追踪表** — 投递状态下拉菜单 + 整行条件格式变色
- 📦 **季节自动归档** — 招聘季结束自动封存，开启新一季
- 🧩 **多方向监控** — 可同时监控多行业，独立配置互不干扰

## 📊 Excel 追踪表

输出文件 `{方向}_岗位追踪.xlsx`（如监控产品方向则生成 `产品_岗位追踪.xlsx`），包含：

| 列 | 说明 |
|---|---|
| 公司 / 岗位 / 城市 / 亮点 | 基础信息 |
| 匹配度 | ⭐~⭐⭐⭐⭐⭐ |
| 来源链接 / 投递入口 | 蓝色可点击超链接 |
| 面经参考 | 牛客网面经搜索链接，可替换 |
| **投递状态** | **下拉菜单**：未投递 → 已投递 → 笔试中 → 面试中 → 已offer / 已挂 / 不感兴趣 |

**选状态后整行自动变色**（Excel 条件格式，实时生效）：

`未投递` ⬜ → `已投递` 🟨 → `笔试中` 🟦 → `面试中` 🟪 → `已offer` 🟩 → `已挂` 🟥 → `不感兴趣` ⬛

每次更新时保留你手动编辑的投递状态和面经链接。

---

## 🗺️ 工作流程

```
config.json  →  4 子 Agent 并行搜索  →  关键词过滤  →  dedupe.py 去重  →  核实新公司 (≤5家)
                                                                              │
                                                                              ▼
                                                                    ┌──────────────────┐
                                                                    │ 渲染日报 +  Excel │
                                                                    │ digest.py        │
                                                                    │ export_excel.py  │
                                                                    └──────────────────┘
```

## 🌐 数据源

| 优先级 | 来源 | 类型 |
|--------|------|------|
| 1 | 牛客网 (nowcoder.com) | 应届生一手讨论区 |
| 2 | 公司招聘公众号 + 官网 | 🥇 一手信息源 |
| 3 | 51job / 智联 / 猎聘校园 | 结构化平台 |
| 4 | 秋招汇总帖 + 实习僧 | 覆盖面广，二手转载 |

---

## ⚙️ 配置

`config.example.json` 是模板，首次使用时 AI 自动生成 `config.json`（不会被提交到 git）：

```json
{
  "onboarded": false,
  "target_grad_year": "",
  "target_season_label": "",
  "job_category_label": "",
  "industry_map": null,
  "job_filter": {
    "positive_keywords": [],
    "fuzzy_keywords": [],
    "negative_keywords": []
  }
}
```

## 🧩 多方向监控

一个方向一套配置、一份 Excel，互不干扰。比如你已经在监控「技术开发」方向，想再监控一个「产品」方向：

```bash
# 1. 复制一份配置，改关键词
cp config.example.json config_hardware.json
# 修改 config_hardware.json 中的 job_category_label 和关键词

# 2. 单独跑硬件方向的搜索 + 去重
python3 scripts/dedupe.py \
  --state state/seen_postings_hardware.json \
  --config config_hardware.json --output new_only_hardware.json

# 3. 生成产品方向的独立 Excel（产出 `产品_岗位追踪.xlsx`）
python3 scripts/export_excel.py \
  --state state/seen_postings_hardware.json \
  --config config_hardware.json
```

每个方向都走完整流程：独立配置 → 独立去重 → 独立 Excel → 独立日报。想监控几个方向都行。

---

## 📁 项目结构

```
campus-radar/
├── SKILL.md                # AI 执行步骤（核心）
├── config.example.json     # 配置模板
├── requirements.txt
├── scripts/
│   ├── dedupe.py           # 去重 + 状态管理
│   ├── digest.py           # 日报渲染
│   ├── export_excel.py     # Excel 导出（条件格式/下拉菜单）
│   └── add_posting.py      # 手动录入岗位
├── references/             # 参考文档
│   ├── sources.md          # 数据源策略
│   ├── keyword-filters.md  # 过滤逻辑
│   ├── industry-map.md     # 行业搜索覆盖方案
│   └── digest-format.md    # 日报格式
└── state/                  # 运行时状态（自动生成）
    └── .gitkeep
```

---

## 📄 License

MIT
