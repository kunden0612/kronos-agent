# Hermes-Kronos 智能金融预测系统 - Product Requirement Document

## Overview
- **Summary**: 融合 Hermes Agent（自进化智能体）与 Kronos 模型（金融 K 线基础模型）的端到端智能金融预测系统，用户通过自然语言描述需求，Agent 自动规划任务、调用模型、解读结果、生成可视化报告。
- **Purpose**: 解决传统量化分析工具智能化交互不足、专业级预测困难的问题，提供低门槛、高智能的金融预测体验
- **Target Users**: 个人投资者、量化研究员、金融分析师、运维管理员

## Goals
- 实现 Hermes Agent 通过 Tool Calling 调用 Kronos 模型，完成多资产、多周期金融预测
- 提供美观、响应式前端界面，支持 K 线图叠加预测、交互式图表与自然语言对话
- 利用 Hermes 的技能自学习与持久记忆，系统随使用持续优化预测流程与用户偏好适配
- 模块化微服务架构，Hermes 与 Kronos 独立部署、松耦合协作，支持水平扩展
- 预留 MCP 工具接口与 Skill 插件机制，支持接入其他预测模型或数据源

## Non-Goals (Out of Scope)
- 直接提供交易执行功能，仅提供预测与分析
- 提供投资建议承诺，所有预测结果均附免责声明
- Kronos-large 模型（未开源）的完整实现
- 支持实时交易所数据（仅支持公开数据源延迟数据）

## Background & Context
项目融合两大前沿开源技术：
- **Hermes Agent**（Nous Research，MIT License）：自进化 AI 智能体框架，具备技能自动学习、持久记忆、多平台接入、定时任务、子 Agent 并行委派等特性
- **Kronos**（清华大学 shiyu-coder，MIT License）：首个面向金融 K 线图的开源基础模型，采用专用分词器 + 自回归 Transformer 架构，支持零样本预测与微调，已被 AAAI 2026 接收
- 两大组件通过 REST API 与 Tool Calling 机制集成，提供「对话即预测」的端到端体验

## Functional Requirements
- **FR-1**: 自然语言预测 - 用户通过文本输入预测需求，支持多轮上下文理解
- **FR-2**: 金融预测核心 - 支持多资产（A股/美股/加密货币）、多周期、多模型选择的预测功能
- **FR-3**: 可视化展示 - K 线图叠加预测、交互式图表、AI 解读卡片
- **FR-4**: 批量与定时 - 支持批量多资产预测、Cron 定时任务
- **FR-5**: Hermes 自进化 - 预测技能自动创建、用户偏好记忆、Honcho 用户建模
- **FR-6**: 用户管理 - 认证、授权、历史记录管理
- **FR-7**: 管理端功能 - 数据接入管理、模型运维、系统监控

## Non-Functional Requirements
- **NFR-1**: 性能 - 单次预测延迟 < 3s (Kronos-mini) / < 8s (Kronos-base)，首屏加载 < 2s
- **NFR-2**: 可靠性 - 系统可用性 99.9%，预测成功率 > 95%
- **NFR-3**: 安全性 - HTTPS/WSS 加密、JWT 认证、RBAC 权限、速率限制、全量审计日志
- **NFR-4**: 可扩展性 - 模块化设计、支持新模型/数据源/平台接入
- **NFR-5**: 可用性 - 响应式设计、暗色模式支持、完善的风险提示

## Constraints
- **Technical**: Python 3.11+ / React 18+ / TypeScript 5，使用 Docker Compose 开发环境
- **Business**: 所有预测必须附带「不构成投资建议」免责声明，不提供交易功能
- **Dependencies**: Hermes Agent、Kronos、AkShare/YFinance/CCXT 数据源、PostgreSQL/TimescaleDB/Redis/MinIO

## Assumptions
- Kronos 模型在 HuggingFace 上可公开获取（NeoQuasar/Kronos-*）
- 用户有基础金融知识，理解预测结果的局限性
- 有可用的 GPU 资源用于 Kronos 模型推理（可选，CPU 也可运行 mini 模型）
- 数据源（AkShare/YFinance/CCXT）服务稳定可用

## Acceptance Criteria

### AC-1: 核心预测流程
- **Given**: 用户已登录系统
- **When**: 用户输入「预测贵州茅台未来5个交易日的走势，用Kronos-base模型」
- **Then**: 
  - Hermes 正确识别意图、提取参数
  - 成功调用 Kronos 进行预测
  - 返回结构化预测结果（OHLCV + 置信区间）
  - 生成自然语言解读
  - 前端展示 K 线图 + 预测曲线 + 置信带
  - 显示明确的风险提示
- **Verification**: programmatic + human-judgment
- **Notes**: 单资产预测完成时间 < 8s (base) / < 3s (mini)

### AC-2: 多轮对话支持
- **Given**: 用户已完成一次预测
- **When**: 用户追问「换成日频呢」「跟上次比怎么样」
- **Then**: 
  - Hermes 正确理解上下文
  - 根据历史对话调整预测参数
  - 生成对比分析结果
- **Verification**: programmatic + human-judgment

### AC-3: 批量预测
- **Given**: 用户有多个待预测资产
- **When**: 用户请求批量预测（如「沪深300成分股批量预测」）
- **Then**: 
  - Hermes 委派子 Agent 并行处理
  - Kronos 使用 predict_batch 接口并行推理
  - 10 资产预测完成 < 30s
- **Verification**: programmatic

### AC-4: 定时任务
- **Given**: 用户配置了定时任务
- **When**: Cron 触发时间到达
- **Then**: 
  - 自动执行预测
  - 推送结果到用户配置的平台
- **Verification**: programmatic

### AC-5: 前端交互体验
- **Given**: 用户访问系统
- **When**: 用户进行各项交互（对话、图表操作、参数配置）
- **Then**: 
  - 响应式设计在各断点正常工作
  - K 线图支持缩放、拖拽、十字光标
  - 对话有流式打字效果
  - 首屏加载 < 2s
- **Verification**: human-judgment + programmatic

### AC-6: 模型切换
- **Given**: 系统已加载多个 Kronos 模型
- **When**: 用户选择不同模型（mini/small/base）
- **Then**: 
  - 成功切换模型
  - 预测延迟符合预期
- **Verification**: programmatic

### AC-7: 安全与合规
- **Given**: 用户使用系统
- **When**: 任何预测结果生成
- **Then**: 
  - 所有 API 调用需 JWT 认证
  - 每次预测结果显示明确的风险提示
  - 操作日志完整记录
- **Verification**: programmatic

## Open Questions
- [ ] Hermes Agent 的具体集成方式（是使用官方 SDK 还是自建简化版）
- [ ] 是否需要实现完整的 Honcho 用户建模系统（或简化版）
- [ ] 数据源的选择优先级（AkShare vs Tushare vs 其他）
- [ ] 初始可用的 Kronos 模型（是从 mini 开始还是直接支持 base）
