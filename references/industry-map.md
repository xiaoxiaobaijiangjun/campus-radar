# 行业搜索覆盖方案

## 问题

不同岗位方向散布在不同行业中。如果只按关键词搜索，会漏掉大量岗位——嵌入式不仅在科技公司，还在半导体、汽车、航天、新能源等行业中。每个用户的方向不同，不能写死行业列表。

## 方案：行业搜索地图

在初始化阶段（Step 0），AI 根据用户选择的岗位方向，**动态生成一张「行业搜索地图」**，写入 `config.json` 的 `industry_map` 字段。后续每次搜索时，子 agent 同时使用关键词和行业地图，确保覆盖面。

### 行业地图结构

```json
{
  "industry_map": {
    "industries": [
      {
        "name": "半导体/芯片",
        "search_hint": "芯片设计、晶圆制造、封测、EDA",
        "example_companies": ["中芯国际", "华虹半导体", "士兰微", "北方华创"]
      },
      {
        "name": "汽车/新能源汽车",
        "search_hint": "整车厂、Tier1供应商、自动驾驶",
        "example_companies": ["比亚迪", "博世", "理想", "蔚来"]
      }
    ],
    "keyword_synonyms": {
      "嵌入式": ["MCU", "单片机", "ARM", "Cortex-M", "RTOS", "FreeRTOS", "BSP", "固件", "底层开发", "驱动开发"],
      "STM32": ["GD32", "HAL库", "标准外设库", "CubeMX", "寄存器"]
    },
    "search_queries": [
      "嵌入式 2027届秋招 半导体",
      "MCU 校园招聘 芯片公司",
      "单片机开发 校招 汽车电子"
    ]
  }
}
```

### 生成逻辑（在 Step 0 初始化时执行）

当用户说出岗位方向后，AI 按以下逻辑生成行业地图：

1. **确定相关行业**：根据岗位方向，列出该方向通常出现的所有行业。不要遗漏——宁可多列也不要漏。
   - 示例：嵌入式 → 半导体、汽车、机器人、航天航空、新能源、智能制造、广电通信、消费电子、医疗器械、物联网、军工国防
   - 示例：后端 → 互联网、金融科技、电商、社交内容、企业服务、游戏、云计算、智能出行
   - 示例：产品经理 → 互联网、金融科技、电商、企业服务、SaaS、智能硬件

2. **扩展关键词同义词**：为每个 `positive_keyword` 生成同义词/近义词/缩写。
   - "嵌入式" → MCU、单片机、ARM、RTOS、BSP、固件、底层开发
   - "Java" → JVM、Spring、Spring Boot、MyBatis、JPA
   - "产品经理" → PM、产品策划、产品运营

3. **生成搜索查询组合**：关键词 × 行业 的交叉组合，用于子 agent 搜索。
   - "{关键词} {届别}秋招 {行业名}"
   - "{同义词} 校园招聘 {行业提示}"

4. **列出各行业代表公司**：每个行业 3-5 家代表公司名，子 agent 搜索时可以定向访问这些公司的官网。

### 子 agent 使用方式

Step 2 的 4 个子 agent 分工调整为：

| 子 agent | 搜索策略 | 覆盖面 |
|----------|---------|--------|
| **Agent 1** | 关键词搜索聚合平台（牛客网等） | 按关键词广搜 |
| **Agent 2** | 行业地图中的代表公司官网 | 按行业定点搜 |
| **Agent 3** | 招聘平台（51job/智联/猎聘） | 按关键词+行业交叉搜 |
| **Agent 4** | 秋招汇总贴 + 实习僧 + 公众号 | 按行业发现新公司 |

每个子 agent 的 prompt 必须包含：
- `config.json` 的 `positive_keywords` 实际值
- `industry_map.keyword_synonyms` 的同义词列表
- `industry_map.industries` 的行业列表和代表公司

### 个性化与广度的平衡

| 偏好 | 处理方式 |
|------|---------|
| 用户想看更多岗位 | 行业地图多列行业，同义词多扩展 |
| 用户只要精准匹配 | `negative_keywords` 更严格，行业地图只列核心行业 |
| 用户方向较窄（如只看嵌入式） | 行业地图覆盖广，但关键词过滤严 |
| 用户方向较宽（如不限方向） | 不生成行业地图，按常规搜索 |

### 灵活性

- 行业地图在 `config.json` 中，用户可以手动增删行业或公司
- 每次 Step 0 初始化时 AI 自动生成，不需要用户自己列
- 如果某行业后续发现新公司，子 agent 在 Step 5 核实时可以建议将其加入地图
- 换季归档时（`maybe_archive_season`），行业地图保留不清理

### 配置示例

初始化后，`config.json` 会增加 `industry_map` 字段：

```json
{
  "job_category_label": "嵌入式",
  "job_filter": {
    "positive_keywords": ["嵌入式", "STM32", "FreeRTOS"]
  },
  "industry_map": {
    "industries": [
      {"name": "半导体/芯片", "search_hint": "芯片设计、晶圆、封测", "example_companies": ["中芯国际", "士兰微"]},
      {"name": "汽车/新能源车", "search_hint": "整车、Tier1、智驾", "example_companies": ["比亚迪", "博世"]},
      {"name": "机器人", "search_hint": "工业/服务/协作机器人", "example_companies": ["大疆", "新松"]},
      {"name": "航天航空", "search_hint": "央企、军工、航电", "example_companies": ["航天科工", "中航光电"]},
      {"name": "新能源/储能", "search_hint": "光伏、风电、储能", "example_companies": ["阳光电源", "远景能源"]},
      {"name": "智能制造", "search_hint": "工业控制、自动化", "example_companies": ["汇川", "中控技术"]},
      {"name": "广电通信", "search_hint": "通信设备、广电", "example_companies": ["中兴", "海格通信"]},
      {"name": "消费电子", "search_hint": "手机、耳机、IoT", "example_companies": ["华为", "韶音"]},
      {"name": "医疗器械", "search_hint": "医疗设备、诊断", "example_companies": ["迈瑞医疗"]},
      {"name": "物联网/智能家居", "search_hint": "AIoT、智能家居", "example_companies": ["乐鑫", "涂鸦"]}
    ],
    "keyword_synonyms": {
      "嵌入式": ["MCU", "单片机", "ARM", "Cortex-M", "RTOS", "FreeRTOS", "BSP", "固件", "底层开发", "驱动开发"],
      "STM32": ["GD32", "HAL库", "标准外设库", "CubeMX"]
    }
  }
}
```
