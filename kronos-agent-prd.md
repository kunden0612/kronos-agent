# 项目需求说明书：Hermes-Kronos 智能金融预测系统

> **文档版本**：v2.0  
> **编写日期**：2026年4月30日  
> **项目名称**：Hermes-Kronos 智能金融预测系统  
> **项目类型**：AI Agent + 金融预测模型融合应用  
> **核心定位**：自进化 Agent + 金融 K 线基础模型 → 端到端智能金融预测平台

---

## 1. 项目概述

### 1.1 项目背景

金融市场数据具备高噪声、非平稳、多尺度等独特特征，传统量化分析工具难以同时满足「智能化交互」与「专业级预测」的双重要求。本项目融合两大前沿开源技术：

| 技术组件 | 来源 | 核心能力 |
|---------|------|---------|
| **Hermes Agent** | Nous Research | 自进化 AI 智能体框架——内置技能自动学习、持久记忆、多平台接入、定时任务、子 Agent 并行委派 |
| **Kronos 模型** | 清华大学 (shiyu-coder) | 首个面向金融 K 线图的开源基础模型——专用分词器 + 自回归 Transformer，支持零样本预测与微调，AAAI 2026 接收 |

**融合价值**：Hermes 提供自然语言理解、任务规划与工具调用能力，Kronos 提供专业级金融时序预测能力。两者结合可构建「对话即预测」的端到端系统——用户用自然语言描述需求，Agent 自动规划任务、调用模型、解读结果、生成可视化报告。

### 1.2 项目目标

| 维度 | 目标 |
|------|------|
| **核心功能** | 实现 Hermes Agent 通过 Tool Calling 调用 Kronos 模型，完成多资产、多周期金融预测 |
| **用户体验** | 提供美观、响应式前端界面，支持 K 线图叠加预测、交互式图表与自然语言对话 |
| **智能进化** | 利用 Hermes 的技能自学习与持久记忆，系统随使用持续优化预测流程与用户偏好适配 |
| **架构设计** | 模块化微服务架构，Hermes 与 Kronos 独立部署、松耦合协作，支持水平扩展 |
| **可扩展性** | 预留 MCP 工具接口与 Skill 插件机制，支持接入其他预测模型或数据源 |

### 1.3 目标用户

| 用户画像 | 核心需求 | 使用场景 |
|---------|---------|---------|
| 个人投资者 | 快速获取走势预测、低门槛操作 | 「预测茅台下周走势」「BTC 明天会跌吗」 |
| 量化研究员 | 批量回测、模型微调、因子分析 | 「用 Kronos-base 跑 A 股日频 Top-K 策略回测」 |
| 金融分析师 | 生成专业报告、多资产对比 | 「生成沪深 300 成分股批量预测报告」 |
| 运维管理员 | 模型管理、资源监控、权限控制 | 「查看 GPU 利用率」「切换 Kronos-base 模型」 |

---

## 2. 核心技术解析

### 2.1 Hermes Agent 架构

Hermes Agent 是 Nous Research 开发的自进化 AI 智能体，核心特性：

```
┌─────────────────────────────────────────────────────────────┐
│                    Hermes Agent Core                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  对话管理器   │  │  技能引擎     │  │  记忆系统     │      │
│  │  (Dialog)    │  │  (Skills)    │  │  (Memory)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│  ┌──────▼─────────────────▼──────────────────▼───────┐      │
│  │              Tool Calling 接口层                   │      │
│  │   40+ 内置工具 + MCP 兼容 + 自定义工具注册         │      │
│  └──────────────────┬───────────────────────────────┘      │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────┐      │
│  │              多平台 Gateway                       │      │
│  │  CLI / Telegram / Discord / Slack / WhatsApp     │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Cron 调度器  │  │  子Agent委派  │  │  Honcho 用户  │      │
│  │  (定时任务)   │  │  (并行执行)   │  │  建模系统     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**关键特性详解**：

| 特性 | 说明 | 本项目应用 |
|------|------|-----------|
| **Skill 系统** | 自主从经验创建技能，使用中自我改进 | 将「Kronos 预测」封装为 Skill，支持预测模板复用 |
| **持久记忆** | FTS5 会话搜索 + LLM 摘要，跨会话召回 | 记住用户偏好资产、风险等级、常用预测参数 |
| **Tool Calling** | 40+ 内置工具 + MCP 兼容 + 自定义注册 | 注册 KronosPredictor 为自定义工具 |
| **Cron 调度** | 内置定时任务，支持自然语言配置 | 「每天开盘前自动预测自选股」 |
| **子 Agent** | 隔离子 Agent 并行处理 | 批量预测多资产时并行委派 |
| **Honcho 建模** | 方言式用户画像构建 | 动态调整预测策略与风险提示风格 |
| **多模型支持** | Nous Portal / OpenRouter / OpenAI / HF 等 | Agent 推理与 Kronos 预测解耦，独立选模型 |
| **多平台 Gateway** | Telegram / Discord / Slack / WhatsApp / CLI | 预测结果推送到用户常用平台 |

### 2.2 Kronos 模型架构

Kronos 是首个面向金融 K 线图的开源基础模型，采用两阶段框架：

```
┌──────────────────────────────────────────────────────────┐
│                    Kronos Pipeline                        │
│                                                          │
│  Stage 1: 专用分词器 (KronosTokenizer)                   │
│  ┌─────────────────────────────────────────────┐        │
│  │  OHLCV 连续数据 → 量化 → 分层离散 Token      │        │
│  │  支持多维度: Open/High/Low/Close/Vol/Amount  │        │
│  └────────────────────┬────────────────────────┘        │
│                       ▼                                  │
│  Stage 2: 自回归 Transformer (Kronos Model)              │
│  ┌─────────────────────────────────────────────┐        │
│  │  Token 序列 → Transformer 解码 → 预测 Token  │        │
│  │  → 反归一化 → OHLCV 预测结果                  │        │
│  └─────────────────────────────────────────────┘        │
│                                                          │
│  输出: pred_df (open, high, low, close, volume, amount)  │
│        + 置信区间 (多路径采样统计)                         │
└──────────────────────────────────────────────────────────┘
```

**模型规格**：

| 模型 | 分词器 | 上下文长度 | 参数量 | 适用场景 |
|------|--------|-----------|--------|---------|
| Kronos-mini | Kronos-Tokenizer-2k | 2048 | 4.1M | 实时推理、轻量部署 |
| Kronos-small | Kronos-Tokenizer-base | 512 | 24.7M | 日常预测、低成本 |
| Kronos-base | Kronos-Tokenizer-base | 512 | 102.3M | 高精度预测、研究 |
| Kronos-large | Kronos-Tokenizer-base | 512 | 499.2M | 极致精度（未开源） |

**核心 API**：

```python
# 单资产预测
predictor = KronosPredictor(model, tokenizer, max_context=512)
pred_df = predictor.predict(
    df=x_df,               # DataFrame: open/high/low/close[/volume/amount]
    x_timestamp=x_ts,      # 历史时间戳
    y_timestamp=y_ts,      # 预测时间戳
    pred_len=120,           # 预测长度
    T=1.0,                  # 温度
    top_p=0.9,              # 核采样
    sample_count=1          # 采样路径数
)

# 批量并行预测
pred_df_list = predictor.predict_batch(
    df_list=[df1, df2, df3],
    x_timestamp_list=[x_ts1, x_ts2, x_ts3],
    y_timestamp_list=[y_ts1, y_ts2, y_ts3],
    pred_len=120, T=1.0, top_p=0.9, sample_count=1
)
```

### 2.3 融合架构：Hermes × Kronos

```
                    ┌─────────────────────┐
                    │   用户自然语言输入    │
                    │ "预测茅台下周走势"    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Hermes Agent      │
                    │                     │
                    │  1. 意图识别         │
                    │     → 金融预测任务    │
                    │  2. 参数提取         │
                    │     → 资产/周期/模型  │
                    │  3. 记忆检索         │
                    │     → 用户偏好/历史   │
                    │  4. Tool Call        │
                    │     → kronos_predict │
                    └──────────┬──────────┘
                               │ RPC / REST
                    ┌──────────▼──────────┐
                    │  Kronos Service     │
                    │                     │
                    │  1. 数据获取         │
                    │     → AkShare/Tushare│
                    │  2. 预处理 & 归一化   │
                    │  3. Tokenize         │
                    │  4. Model Inference  │
                    │  5. Denormalize      │
                    │  6. 置信区间计算      │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  结果融合与响应生成   │
                    │                     │
                    │  • 结构化预测 JSON   │
                    │  • Hermes 自然语言   │
                    │    解读 + 风险提示   │
                    │  • 前端可视化渲染    │
                    └─────────────────────┘
```

---

## 3. 系统架构设计

### 3.1 整体架构

```
┌───────────────────────────────────────────────────────────────┐
│                      前端展示层 (Frontend)                     │
│                                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  对话面板    │ │  K线图面板   │ │  管理面板    │            │
│  │  ChatView   │ │  ChartView  │ │  AdminView  │            │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │
│         └───────────────┼───────────────┘                    │
│                         ▼                                     │
│  React 18 + TypeScript + Zustand + Ant Design + TailwindCSS  │
│  ECharts 5 (K线图) + AntV G2 (辅助图表)                       │
│  WebSocket (实时推送) + Axios (REST API)                       │
└─────────────────────────┬─────────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼─────────────────────────────────────┐
│                      API 网关层 (Gateway)                      │
│                                                               │
│  FastAPI + Uvicorn                                           │
│  JWT 认证 / 请求限流 / API 版本管理 / 日志审计                │
│  WebSocket 连接管理 / 任务状态推送                             │
└─────────────────────────┬─────────────────────────────────────┘
                          │ 内部 gRPC / Redis 消息队列
┌─────────────────────────▼─────────────────────────────────────┐
│                    核心业务层 (Core Services)                   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │            Hermes Agent 服务 (独立进程)                │   │
│  │                                                       │   │
│  │  • 对话管理 / 意图解析 / 上下文追踪                    │   │
│  │  • Skill 调度: kronos_predict / kronos_batch / ...    │   │
│  │  • 记忆检索: 用户偏好 / 历史预测 / 风险画像            │   │
│  │  • Cron 调度: 定时预测 / 定期报告                     │   │
│  │  • 子 Agent 委派: 批量并行预测                        │   │
│  │  • Honcho 用户建模: 动态适配交互风格                   │   │
│  └────────────────────────┬──────────────────────────────┘   │
│                           │ Tool Calling (自定义工具)          │
│  ┌────────────────────────▼──────────────────────────────┐   │
│  │            Kronos 预测服务 (GPU 进程)                  │   │
│  │                                                       │   │
│  │  • 模型加载/热切换: mini / small / base               │   │
│  │  • KronosPredictor 封装                               │   │
│  │  • 数据预处理: 归一化 / 时间对齐 / 缺失值处理          │   │
│  │  • 推理引擎: 单资产 / 批量并行 (predict_batch)         │   │
│  │  • 后处理: 反归一化 / 置信区间 / 异常值过滤            │   │
│  │  • 微调管理: Qlib 数据准备 / 分词器微调 / 模型微调     │   │
│  └────────────────────────┬──────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼──────────────────────────────┐   │
│  │            数据服务 (独立服务)                         │   │
│  │                                                       │   │
│  │  • 行情数据: AkShare(A股) / YFinance(美股) / CCXT(加密)│   │
│  │  • 缓存层: Redis 7 + RedisJSON (分钟级行情缓存)       │   │
│  │  • 持久化: PostgreSQL 15 + TimescaleDB (时序存储)      │   │
│  │  • 向量检索: pgvector (Hermes 记忆检索)                │   │
│  │  • 文件存储: MinIO (模型文件 / 报告 / 回测数据)        │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────────┐
│                    基础设施层 (Infrastructure)                  │
│                                                               │
│  Docker Compose / Kubernetes                                  │
│  NVIDIA GPU Runtime (Kronos 推理)                              │
│  Prometheus + Grafana (监控告警)                               │
│  Nginx (反向代理 / SSL / 静态资源)                             │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 Hermes-Kronos 交互流程

```
用户: "预测贵州茅台未来5个交易日的走势，用Kronos-base模型"

  ┌─ Hermes Agent ──────────────────────────────────────────────┐
  │                                                             │
  │  1. 意图解析                                                 │
  │     intent: financial_prediction                            │
  │     asset: 600519.SH (贵州茅台)                             │
  │     period: 5 trading days                                  │
  │     model: Kronos-base                                      │
  │                                                             │
  │  2. 记忆检索                                                 │
  │     → 用户偏好: 日频预测, sample_count=5, 关注波动率         │
  │     → 历史预测: 上次预测茅台时 lookback=400                  │
  │                                                             │
  │  3. Tool Call: kronos_predict                               │
  │     {                                                       │
  │       "symbol": "600519.SH",                                │
  │       "model_name": "Kronos-base",                          │
  │       "lookback": 400,                                      │
  │       "pred_len": 5,                                        │
  │       "freq": "daily",                                      │
  │       "sample_count": 5,                                    │
  │       "T": 1.0,                                             │
  │       "top_p": 0.9                                          │
  │     }                                                       │
  │                                                             │
  └─────────────────────────┬───────────────────────────────────┘
                            │
  ┌─ Kronos Service ────────▼───────────────────────────────────┐
  │                                                             │
  │  4. 数据获取                                                 │
  │     → AkShare: 获取 600519.SH 最近 400 个交易日 OHLCV       │
  │     → Redis 缓存检查 → 命中则跳过远程获取                    │
  │                                                             │
  │  5. 预处理                                                   │
  │     → 数据校验 / 缺失值填充 / 时间对齐                       │
  │     → 构造 x_df, x_timestamp, y_timestamp                   │
  │                                                             │
  │  6. 推理                                                     │
  │     → KronosTokenizer.encode(ohlcv) → tokens                │
  │     → Kronos.forward(tokens) → pred_tokens                  │
  │     → KronosTokenizer.decode(pred_tokens) → raw_pred        │
  │     → 反归一化 → pred_df (5×6 DataFrame)                    │
  │     → 5 次采样 → 均值 + 置信区间                             │
  │                                                             │
  │  7. 返回结构化结果                                           │
  │     {                                                       │
  │       "predictions": [...],   // 5 日 OHLCV + 置信区间      │
  │       "confidence": {...},    // 采样统计                    │
  │       "model_info": {...},    // 模型版本/参数               │
  │       "data_range": {...}     // 输入数据范围                 │
  │     }                                                       │
  │                                                             │
  └─────────────────────────┬───────────────────────────────────┘
                            │
  ┌─ 结果融合 ──────────────▼───────────────────────────────────┐
  │                                                             │
  │  8. Hermes 自然语言解读                                     │
  │     → 趋势判断: "预计未来5日呈温和上行趋势"                  │
  │     → 关键价位: "支撑位 1850，压力位 1920"                   │
  │     → 波动分析: "日均波动率约 1.8%，置信区间 ±2.3%"         │
  │     → 风险提示: "⚠️ 模型基于历史数据，不构成投资建议"       │
  │                                                             │
  │  9. 技能沉淀 (自动)                                         │
  │     → Skill: kronos_predict_600519_daily                    │
  │     → 记忆: 用户偏好更新                                    │
  │                                                             │
  │  10. 前端渲染                                                │
  │     → K线图叠加预测曲线 + 置信带                             │
  │     → 趋势解读卡片                                          │
  │     → 风险提示横幅                                          │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

---

## 4. 功能需求

### 4.1 用户端功能

#### 4.1.1 智能对话交互（Hermes 驱动）

| 功能点 | 详细描述 | 优先级 |
|--------|---------|--------|
| 自然语言预测 | 用户通过文本输入预测需求，如「预测茅台下周走势」「BTC 24h 预测」 | P0 |
| 多轮上下文理解 | 支持追问、修正、对比分析：「换成日频呢」「跟上次比怎么样」 | P0 |
| 意图路由 | Hermes 自动识别预测/回测/报告/管理等意图，分发到对应 Skill | P0 |
| 个性化偏好 | 基于 Honcho 用户建模，自动适配预测参数与风险提示风格 | P1 |
| 历史会话管理 | 跨会话检索历史预测记录，FTS5 全文搜索 + LLM 摘要 | P1 |
| 语音输入 | 支持语音消息转录为文本（Hermes Gateway 语音转写） | P2 |

#### 4.1.2 金融预测功能（Kronos 驱动）

| 功能点 | 详细描述 | 优先级 |
|--------|---------|--------|
| 资产支持 | A 股 (AkShare)、美股 (YFinance)、加密货币 (CCXT) | P0 |
| 多周期预测 | 分钟级 / 小时级 / 日级 / 周级，Kronos-mini 支持上下文 2048 | P0 |
| 多指标输出 | OHLCV 价格预测 + 波动率 + 置信区间（多路径采样统计） | P0 |
| 模型切换 | 用户可选择 mini / small / base，平衡速度与精度 | P0 |
| 批量预测 | Hermes 子 Agent 并行委派，Kronos predict_batch GPU 并行 | P1 |
| 定时预测 | Hermes Cron 调度：每天开盘前自动推送到 Telegram/微信 | P1 |
| 回测验证 | 集成 Qlib 回测流程，Top-K 策略 + 累计收益曲线 | P2 |
| 模型微调 | 用户上传自有数据微调分词器与预测器（torchrun 多 GPU） | P2 |

#### 4.1.3 可视化展示

| 功能点 | 详细描述 | 优先级 |
|--------|---------|--------|
| K 线图叠加预测 | ECharts K 线主图 + 预测曲线 + 置信带（半透明区域） | P0 |
| 交互式图表 | 缩放 / 拖拽 / 指标切换 / 多子图联动（ECharts dataZoom） | P0 |
| 多资产对比 | 多条预测曲线同图对比，支持归一化坐标 | P1 |
| 技术指标叠加 | MA / MACD / RSI / BOLL 等常用技术指标 | P1 |
| 报告导出 | PDF / Excel 格式的预测分析报告一键导出 | P1 |
| 实时推送 | WebSocket 推送预测进度与结果，K 线图实时更新 | P1 |

#### 4.1.4 系统管理

| 功能点 | 详细描述 | 优先级 |
|--------|---------|--------|
| 用户认证 | 邮箱/手机号注册登录，支持 OAuth2 第三方授权 | P0 |
| 权限控制 | 普通用户 / 专业用户 / 管理员三级权限体系 | P1 |
| 模型管理 | 查看已加载模型、切换模型版本、触发微调任务 | P2 |
| 资源监控 | GPU 使用率、请求延迟、预测成功率等指标看板 | P2 |

### 4.2 Hermes 自进化功能

| 功能点 | 详细描述 | 优先级 |
|--------|---------|--------|
| 预测技能自动创建 | 用户完成一次复杂预测后，Hermes 自动将流程封装为 Skill | P1 |
| 技能自我改进 | Skill 在使用中自我优化（参数调优 / 提示词改进） | P2 |
| 预测偏好记忆 | 跨会话记住用户常用资产、风险等级、预测周期 | P1 |
| 用户画像建模 | Honcho 方言式建模，动态调整解读风格与风险提示力度 | P2 |
| 预测定时化 | 用户说「每天早上 9 点预测自选股」→ 自动创建 Cron 任务 | P1 |

### 4.3 管理端功能

| 功能模块 | 核心能力 |
|---------|---------|
| **数据接入管理** | 配置数据源 (AkShare/YFinance/CCXT)、设置更新频率、监控数据质量 |
| **模型运维** | Kronos 模型版本管理、热加载/卸载、A/B 测试配置、微调任务管理 |
| **Hermes 运维** | Skill 管理、Cron 任务监控、记忆库管理、Gateway 平台状态 |
| **用户运营** | 用户行为分析、使用统计、反馈收集、A/B 测试 |
| **系统监控** | 服务健康检查、GPU 利用率、异常告警 (Prometheus + Grafana) |

---

## 5. API 设计

### 5.1 核心 API 列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/chat` | 发送对话消息，Hermes 处理 | JWT |
| POST | `/api/v1/predict` | 直接调用 Kronos 预测（绕过对话） | JWT |
| POST | `/api/v1/predict/batch` | 批量预测多资产 | JWT |
| GET | `/api/v1/predict/{task_id}` | 查询预测任务状态与结果 | JWT |
| GET | `/api/v1/predict/history` | 获取历史预测记录 | JWT |
| GET | `/api/v1/models` | 获取已加载模型列表 | JWT |
| POST | `/api/v1/models/load` | 加载指定模型 | Admin |
| POST | `/api/v1/models/unload` | 卸载模型释放 GPU | Admin |
| POST | `/api/v1/finetune` | 提交微调任务 | Admin |
| GET | `/api/v1/finetune/{task_id}` | 查询微调任务状态 | Admin |
| WS | `/ws/v1/stream` | WebSocket 实时推送 | JWT |
| GET | `/api/v1/auth/login` | 用户登录 | Public |
| POST | `/api/v1/auth/register` | 用户注册 | Public |

### 5.2 核心 API 示例

**POST /api/v1/predict 请求体**：

```json
{
  "symbol": "600519.SH",
  "model_name": "Kronos-base",
  "lookback": 400,
  "pred_len": 5,
  "freq": "daily",
  "sample_count": 5,
  "T": 1.0,
  "top_p": 0.9
}
```

**POST /api/v1/predict 响应体**：

```json
{
  "task_id": "pred_20260430_001",
  "status": "completed",
  "symbol": "600519.SH",
  "model": "Kronos-base",
  "predictions": [
    {
      "timestamp": "2026-05-06",
      "open": 1865.2, "high": 1883.5, "low": 1851.3, "close": 1876.8,
      "volume": 32500.0,
      "confidence": { "low_95": 1832.1, "high_95": 1921.5 }
    }
  ],
  "interpretation": "预计未来5个交易日呈温和上行趋势，日均波动率约1.8%...",
  "risk_warning": "⚠️ 模型基于历史数据与机器学习生成，不构成投资建议",
  "created_at": "2026-04-30T14:30:00+08:00",
  "duration_ms": 2350
}
```

### 5.3 WebSocket 推送协议

```json
// 预测进度推送
{ "type": "progress", "task_id": "pred_001", "step": "data_fetch", "progress": 0.2 }
{ "type": "progress", "task_id": "pred_001", "step": "preprocessing", "progress": 0.4 }
{ "type": "progress", "task_id": "pred_001", "step": "inference", "progress": 0.7 }
{ "type": "completed", "task_id": "pred_001", "result": { ... } }

// 对话流式推送
{ "type": "chat_delta", "content": "根据Kronos-base模型预测，" }
{ "type": "chat_delta", "content": "贵州茅台未来5日..." }
{ "type": "chat_done", "task_id": "pred_001" }
```

---

## 6. 技术栈选型

### 6.1 前端技术栈

```yaml
框架: React 18 + TypeScript 5
构建: Vite 6 + pnpm
状态管理: Zustand
UI 组件: Ant Design 5 + TailwindCSS 4
K 线图: ECharts 5 (K线图 + dataZoom + markArea)
辅助图表: AntV G2 (回测曲线 / 统计图表)
实时通信: WebSocket (native) + React Query (REST)
路由: React Router 7
代码规范: ESLint + Prettier + Husky
测试: Vitest + React Testing Library + Playwright (E2E)
```

### 6.2 后端技术栈

```yaml
API 网关: Python 3.11 + FastAPI + Uvicorn
Agent 框架: Hermes Agent (Nous Research, MIT License)
预测模型: Kronos (shiyu-coder, MIT License)
  - 分词器: NeoQuasar/Kronos-Tokenizer-base
  - 模型: NeoQuasar/Kronos-mini / Kronos-small / Kronos-base
数据层:
  - 缓存: Redis 7 + RedisJSON (行情缓存)
  - 时序库: PostgreSQL 15 + TimescaleDB (K线存储)
  - 向量库: pgvector (Hermes 记忆检索)
  - 对象存储: MinIO (模型文件 / 报告)
任务队列: Celery 5 + Redis Broker (异步预测任务)
微调框架: Qlib (Microsoft) + PyTorch + torchrun
数据源: AkShare (A股) / YFinance (美股) / CCXT (加密货币)
```

### 6.3 基础设施

```yaml
容器化: Docker Compose (开发) / Kubernetes (生产)
GPU: NVIDIA Runtime + CUDA 12.x
反向代理: Nginx (SSL + 静态资源 + WebSocket)
监控: Prometheus + Grafana + AlertManager
日志: Loki + Promtail (日志聚合)
CI/CD: GitHub Actions
```

---

## 7. 数据模型设计

### 7.1 核心数据表

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',  -- user / pro / admin
    preferences JSONB DEFAULT '{}',    -- Hermes 用户偏好
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 预测记录表
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    model_name VARCHAR(30) NOT NULL,    -- Kronos-mini/small/base
    freq VARCHAR(10) NOT NULL,           -- 1min/5min/1h/1d/1w
    lookback INT NOT NULL,
    pred_len INT NOT NULL,
    params JSONB NOT NULL,               -- T, top_p, sample_count
    status VARCHAR(20) DEFAULT 'pending', -- pending/running/completed/failed
    result JSONB,                        -- 预测结果
    interpretation TEXT,                 -- Hermes 自然语言解读
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- K 线数据表 (TimescaleDB hypertable)
CREATE TABLE kline_data (
    symbol VARCHAR(20) NOT NULL,
    freq VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    amount DOUBLE PRECISION DEFAULT 0
);
SELECT create_hypertable('kline_data', 'timestamp');

-- Hermes 记忆表 (pgvector)
CREATE TABLE hermes_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    memory_type VARCHAR(30),  -- preference / prediction / skill / profile
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cron 定时任务表
CREATE TABLE cron_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    schedule VARCHAR(100) NOT NULL,      -- cron 表达式
    task_config JSONB NOT NULL,           -- 预测参数
    platform VARCHAR(20),                 -- 推送平台
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 微调任务表
CREATE TABLE finetune_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    base_model VARCHAR(30) NOT NULL,
    dataset_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB,
    metrics JSONB,                         -- 训练指标
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 8. 前端页面设计

### 8.1 页面结构

```
┌───────────────────────────────────────────────────────────┐
│  Header: Logo + 导航 + 用户头像                            │
├───────────┬───────────────────────────────────────────────┤
│           │                                               │
│  侧边栏    │              主内容区                          │
│           │                                               │
│  ▸ 对话    │  ┌─────────────────────────────────────┐     │
│  ▸ 预测    │  │                                     │     │
│  ▸ 回测    │  │         K 线图 + 预测曲线             │     │
│  ▸ 报告    │  │         (ECharts 交互式)              │     │
│  ▸ 设置    │  │                                     │     │
│           │  └─────────────────────────────────────┘     │
│           │                                               │
│           │  ┌──────────────────┐ ┌──────────────────┐   │
│           │  │ 预测结果卡片      │ │ 置信区间卡片      │   │
│           │  │ OHLCV + 趋势     │ │ 采样统计 + 区间   │   │
│           │  └──────────────────┘ └──────────────────┘   │
│           │                                               │
│           │  ┌─────────────────────────────────────┐     │
│           │  │  AI 解读 (Hermes 自然语言)           │     │
│           │  │  "预计温和上行，支撑位1850..."        │     │
│           │  │  ⚠️ 风险提示                        │     │
│           │  └─────────────────────────────────────┘     │
│           │                                               │
│           │  ┌─────────────────────────────────────┐     │
│           │  │  对话输入框                           │     │
│           │  │  💬 输入预测需求...            [发送] │     │
│           │  └─────────────────────────────────────┘     │
└───────────┴───────────────────────────────────────────────┘
```

### 8.2 核心页面清单

| 页面 | 路由 | 功能 |
|------|------|------|
| 首页/对话 | `/` | 自然语言对话 + K 线图 + AI 解读 |
| 预测中心 | `/predict` | 手动配置预测参数 + 高级选项 |
| 历史记录 | `/history` | 历史预测记录 + 搜索 + 导出 |
| 回测分析 | `/backtest` | Qlib 回测 + 策略对比 + 收益曲线 |
| 定时任务 | `/cron` | Cron 任务管理 + 推送配置 |
| 模型管理 | `/models` | 模型加载/卸载/微调 (Admin) |
| 系统监控 | `/monitor` | GPU / 延迟 / 成功率看板 (Admin) |
| 登录/注册 | `/auth` | 用户认证 |

### 8.3 前端设计规范

```yaml
配色方案:
  主色: "#1677FF" (Ant Design Blue)
  涨色: "#CF1322" (中国红 - 涨)
  跌色: "#3F8600" (绿 - 跌)
  背景: "#F5F5F5" (浅灰)
  卡片: "#FFFFFF" (白)
  暗色模式: 支持

字体:
  中文: "PingFang SC" / "Microsoft YaHei" / "Noto Sans SC"
  英文/数字: "JetBrains Mono" (数据展示) / "Inter" (UI)
  图表数字: "Roboto Mono"

布局:
  响应式断点: 768px / 1024px / 1440px
  侧边栏可折叠
  K 线图占主内容区 60% 高度
  对话面板可切换为独立全屏模式

交互:
  K 线图: 鼠标拖拽缩放 / 十字光标 / 指标切换
  对话: 流式打字效果 / Markdown 渲染 / 代码块高亮
  预测: 实时进度条 / 完成后动画过渡
  响应时间: 首屏 < 2s / 交互 < 100ms
```

---

## 9. Hermes 自定义工具注册

### 9.1 Kronos 工具定义

Hermes 通过 Tool Calling 机制调用 Kronos，需注册以下自定义工具：

```json
[
  {
    "name": "kronos_predict",
    "description": "调用 Kronos 模型预测指定资产的未来走势",
    "parameters": {
      "type": "object",
      "properties": {
        "symbol": { "type": "string", "description": "资产代码，如 600519.SH, BTC/USDT" },
        "model_name": { "type": "string", "enum": ["Kronos-mini", "Kronos-small", "Kronos-base"] },
        "lookback": { "type": "integer", "description": "历史回看窗口长度", "default": 400 },
        "pred_len": { "type": "integer", "description": "预测长度（K线根数）" },
        "freq": { "type": "string", "enum": ["1min", "5min", "15min", "1h", "1d", "1w"] },
        "sample_count": { "type": "integer", "description": "采样路径数（越多置信区间越窄）", "default": 5 },
        "T": { "type": "number", "description": "采样温度", "default": 1.0 },
        "top_p": { "type": "number", "description": "核采样概率", "default": 0.9 }
      },
      "required": ["symbol", "pred_len", "freq"]
    }
  },
  {
    "name": "kronos_batch_predict",
    "description": "批量预测多个资产，使用 Hermes 子 Agent 并行委派 + Kronos predict_batch",
    "parameters": {
      "type": "object",
      "properties": {
        "symbols": { "type": "array", "items": { "type": "string" } },
        "model_name": { "type": "string", "enum": ["Kronos-mini", "Kronos-small", "Kronos-base"] },
        "lookback": { "type": "integer", "default": 400 },
        "pred_len": { "type": "integer" },
        "freq": { "type": "string" },
        "sample_count": { "type": "integer", "default": 5 }
      },
      "required": ["symbols", "pred_len", "freq"]
    }
  },
  {
    "name": "kronos_list_models",
    "description": "查看当前已加载的 Kronos 模型列表",
    "parameters": { "type": "object", "properties": {} }
  },
  {
    "name": "kronos_finetune",
    "description": "提交 Kronos 微调任务（需要 Admin 权限）",
    "parameters": {
      "type": "object",
      "properties": {
        "base_model": { "type": "string" },
        "dataset_path": { "type": "string" },
        "epochs": { "type": "integer", "default": 10 },
        "batch_size": { "type": "integer", "default": 32 }
      },
      "required": ["base_model", "dataset_path"]
    }
  }
]
```

### 9.2 Hermes Skill 封装

将高频预测场景封装为 Hermes Skill：

```yaml
# skill: kronos_daily_report
name: kronos_daily_report
description: 每日开盘前自动预测用户自选股并推送报告
trigger: cron("0 9 * * 1-5")  # 工作日 9:00
steps:
  - 记忆检索: 获取用户自选股列表
  - 批量预测: kronos_batch_predict(symbols=自选股, pred_len=5, freq=1d)
  - 生成报告: Hermes 生成自然语言解读
  - 推送: 发送到用户配置的平台 (Telegram/微信/邮件)
```

---

## 10. 非功能性需求

### 10.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 单次预测延迟 | < 3s (Kronos-mini) / < 8s (Kronos-base) | GPU 推理 |
| 批量预测 (10 资产) | < 30s (Kronos-small) | predict_batch 并行 |
| API 响应时间 | < 200ms (P95) | 不含模型推理 |
| 首屏加载 | < 2s | 前端首屏渲染 |
| WebSocket 延迟 | < 100ms | 推送延迟 |
| 并发支持 | 100+ 并发预测 | 水平扩展 |

### 10.2 可靠性指标

| 指标 | 目标值 |
|------|--------|
| 系统可用性 | 99.9% |
| 数据持久性 | 99.999% |
| 预测成功率 | > 95% |
| 故障恢复时间 | < 5min (自动) |

### 10.3 安全需求

| 需求 | 实现方式 |
|------|---------|
| 传输加密 | HTTPS + WSS，TLS 1.3 |
| 认证授权 | JWT + OAuth2，RBAC 权限模型 |
| 数据加密 | AES-256 静态加密，API Key 加密存储 |
| 速率限制 | API 网关层限流 (100 req/min/user) |
| 审计日志 | 全量操作日志记录，保留 90 天 |
| 风险提示 | 每次预测结果必须附带「不构成投资建议」免责声明 |

### 10.4 可扩展性

| 维度 | 设计 |
|------|------|
| 模型扩展 | 支持加载 Kronos-large 或其他时序模型，热加载无需重启 |
| 数据源扩展 | 数据服务抽象层，新增数据源只需实现 Adapter 接口 |
| Agent 能力扩展 | Hermes Skill 生态 + MCP 工具集成 + agentskills.io 标准 |
| 平台扩展 | Hermes Gateway 支持 Telegram/Discord/Slack/WhatsApp/微信 |
| 存储扩展 | TimescaleDB 分区 + MinIO 对象存储 + Redis 集群 |

---

## 11. 部署架构

### 11.1 开发环境 (Docker Compose)

```yaml
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
  
  api-gateway:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [redis, postgres]
  
  hermes-agent:
    build: ./hermes
    volumes: ["./hermes/skills:/app/skills", "./hermes/memories:/app/memories"]
    depends_on: [api-gateway, kronos-service]
  
  kronos-service:
    build: ./kronos
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: ["gpu"]
    volumes: ["./models:/app/models"]
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  postgres:
    image: timescale/timescaledb:latest-pg15
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
  
  minio:
    image: minio/minio
    ports: ["9000:9000"]
    command: server /data

volumes:
  pgdata:
```

### 11.2 生产环境 (Kubernetes)

```
Ingress (Nginx) → Service Mesh (Istio)
  ├── Frontend Pod (3 replicas, Nginx 静态)
  ├── API Gateway Pod (3 replicas, FastAPI)
  ├── Hermes Agent Pod (2 replicas, 有状态)
  ├── Kronos Service Pod (2 replicas, GPU Node)
  ├── Celery Worker Pod (3 replicas, 异步任务)
  ├── Redis Cluster (3 master + 3 slave)
  ├── PostgreSQL + TimescaleDB (Primary + Replica)
  └── MinIO (4 nodes, 分布式)
```

---

## 12. 开发里程碑

| 阶段 | 时间 | 交付物 | 验收标准 |
|------|------|--------|---------|
| **M1: 基础框架** | 第 1-3 周 | 项目脚手架 + Docker Compose + CI/CD | 本地 `docker compose up` 一键启动 |
| **M2: Kronos 集成** | 第 4-6 周 | Kronos Service + 数据获取 + 预测 API | 单资产预测 API 可用，延迟 < 8s |
| **M3: Hermes 集成** | 第 7-9 周 | Hermes Agent + Tool Calling + 记忆系统 | 自然语言触发预测，多轮对话 |
| **M4: 前端 V1** | 第 10-13 周 | 对话界面 + K 线图 + 预测结果展示 | 用户可通过对话完成完整预测流程 |
| **M5: 高级功能** | 第 14-17 周 | 批量预测 + Cron 定时 + 报告导出 + 回测 | 批量 10 资产 < 30s，Cron 准时推送 |
| **M6: 生产化** | 第 18-20 周 | K8s 部署 + 监控 + 压测 + 安全审计 | 100 并发稳定，99.9% 可用性 |

---

## 13. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Kronos 预测准确率不达预期 | 中 | 高 | 提供多模型选择，支持用户微调；明确风险提示 |
| GPU 资源不足 | 中 | 中 | Kronos-mini 轻量方案；模型动态加载/卸载；推理请求排队 |
| Hermes Agent 稳定性 | 低 | 高 | Agent 进程独立部署，故障自动重启；降级为直接 API 调用 |
| 数据源不稳定 | 中 | 中 | Redis 多级缓存；多数据源热备 (AkShare + Tushare) |
| 合规风险 | 中 | 极高 | 每次预测附免责声明；不提供直接交易功能；数据脱敏 |

---

## 附录

### A. 参考文档

| 文档 | 链接 |
|------|------|
| Hermes Agent 官方文档 | https://hermes-agent.nousresearch.com/docs/ |
| Hermes Agent GitHub | https://github.com/NousResearch/hermes-agent |
| Kronos 论文 (AAAI 2026) | https://arxiv.org/abs/2508.02739 |
| Kronos GitHub | https://github.com/shiyu-coder/Kronos |
| Kronos 实时演示 | https://shiyu-coder.github.io/Kronos-demo/ |
| Kronos HuggingFace | https://huggingface.co/NeoQuasar |
| Qlib 量化框架 | https://github.com/microsoft/qlib |
| agentskills.io 标准 | https://agentskills.io |
| Honcho 用户建模 | https://github.com/plastic-labs/honcho |

### B. 术语表

| 术语 | 说明 |
|------|------|
| K-line / K 线 | 金融蜡烛图，包含 Open/High/Low/Close/Volume 五维数据 |
| OHLCV | 开盘价、最高价、最低价、收盘价、成交量 |
| Lookback | 模型推理时使用的历史数据窗口长度（K 线根数） |
| pred_len | 预测长度，即模型向前预测的 K 线根数 |
| RankIC | 预测排序相关系数，金融预测核心评估指标 |
| Tool Calling | Agent 调用外部函数的能力，Hermes 核心特性 |
| Skill | Hermes 中的可复用技能单元，支持自动创建与自我改进 |
| Honcho | Hermes 集成的方言式用户建模系统 |
| MCP | Model Context Protocol，工具集成标准 |
| Cron | Hermes 内置的定时任务调度器 |
| KronosTokenizer | Kronos 专用分词器，将 OHLCV 连续数据量化为离散 Token |
| predict_batch | Kronos 批量预测接口，支持多资产 GPU 并行 |

### C. 免责声明

> ⚠️ **重要提示**：本系统提供的预测结果基于历史数据与机器学习模型（Kronos）生成，**不构成任何投资建议**。金融市场具有高度不确定性，模型预测存在偏差与失败的可能。用户应独立判断并承担投资风险。开发团队不对因使用本系统导致的任何直接或间接损失承担责任。

---

*本需求说明书将随项目进展持续迭代，最新版本请查阅项目文档库。*
