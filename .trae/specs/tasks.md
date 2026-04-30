# Hermes-Kronos 智能金融预测系统 - The Implementation Plan (Decomposed and Prioritized Task List)

## [x] Task 1: 项目脚手架与基础设施搭建
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 初始化项目目录结构（frontend/backend/hermes/kronos/）
  - 创建 Docker Compose 配置文件
  - 配置开发环境与基础依赖
  - 初始化 Git 仓库与 CI/CD 基础配置
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic`: `docker compose up` 可成功启动所有基础服务
  - `programmatic`: 目录结构符合规范，基础依赖可正常安装
  - `human-judgement`: 代码结构清晰，符合工程规范
- **Notes**: 本阶段仅启动 PostgreSQL/Redis/MinIO 等基础设施，暂不启动业务服务

## [x] Task 2: Kronos 预测服务核心实现
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 实现 Kronos 模型加载与推理接口
  - 集成 AkShare/YFinance/CCXT 数据源
  - 实现数据预处理与后处理（归一化/反归一化）
  - 实现置信区间计算（多路径采样统计）
  - 封装 REST API 端点
- **Acceptance Criteria Addressed**: AC-1, AC-6
- **Test Requirements**:
  - `programmatic`: `/api/v1/predict` 端点可正常响应并返回有效预测结果
  - `programmatic`: 支持 Kronos-mini/small/base 模型切换
  - `programmatic`: 支持 A 股/美股/加密货币多资产预测
  - `programmatic`: 单资产预测延迟 < 8s (base) / < 3s (mini)
- **Notes**: 优先实现 Kronos-mini 模型以降低资源需求，后续再支持其他模型

## [x] Task 3: 简化版 Hermes Agent 与 Tool Calling
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现简化版 Agent 框架（考虑到复杂度，暂不使用完整 Hermes SDK）
  - 实现意图识别与参数提取（使用 OpenAI/本地 LLM）
  - 注册 Kronos 相关自定义工具
  - 实现多轮对话上下文管理
  - 实现自然语言解读生成
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic`: 自然语言输入可正确转换为 Kronos API 调用
  - `programmatic`: 多轮对话可正确保持上下文
  - `human-judgement`: 自然语言解读内容合理、清晰
- **Notes**: 为降低复杂度，先实现简化版 Agent，待验证后再考虑集成完整 Hermes

## [x] Task 4: API 网关与身份认证
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 实现 FastAPI 网关层
  - JWT 身份认证与授权
  - 请求限流与日志审计
  - WebSocket 连接管理
  - API 版本管理
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic`: 未认证请求被拒绝
  - `programmatic`: JWT 认证正常工作
  - `programmatic`: 速率限制生效
  - `programmatic`: WebSocket 连接可正常建立与通信
- **Notes**: 参考 spec.md 中的 API 设计规范

## [x] Task 5: 前端基础框架与路由
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 初始化 React + TypeScript + Vite 项目
  - 配置 Zustand 状态管理
  - 配置 Ant Design + TailwindCSS
  - 实现基础路由结构（/auth, /, /predict, /history）
  - 实现登录/注册页面
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - programmatic: 前端项目可正常构建与启动
  - human-judgement: 页面布局美观、响应式设计正常
  - programmatic: 路由切换正常
- **Notes**: 使用 npm 作为包管理器

## [x] Task 6: K 线图与预测可视化
- **Priority**: P0
- **Depends On**: Task 5
- **Description**: 
  - 集成 ECharts 5 实现 K 线图
  - 实现预测曲线叠加与置信带显示
  - 支持缩放/拖拽/十字光标等交互
  - 实现预测结果卡片（OHLCV + 置信区间）
- **Acceptance Criteria Addressed**: AC-1, AC-5
- **Test Requirements**:
  - programmatic: K 线图可正确加载与显示历史数据
  - programmatic: 预测曲线与置信带可正确渲染
  - human-judgement: 图表交互流畅、视觉效果良好
- **Notes**: 参考 spec.md 中的设计规范

## [x] Task 7: 对话界面与流式交互
- **Priority**: P0
- **Depends On**: Task 6
- **Description**: 
  - 实现对话面板 UI
  - 集成 API 实现聊天响应
  - 实现 Markdown 渲染与代码高亮
  - 实现对话历史管理
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-5
- **Test Requirements**:
  - programmatic: 对话消息可正常发送与接收
  - human-judgement: 交互流畅自然
  - programmatic: 完整预测流程可端到端完成
- **Notes**: 实现核心对话体验，支持完整的「自然语言→预测→可视化」流程

## [ ] Task 8: 数据持久化与历史记录
- **Priority**: P1
- **Depends On**: Task 4
- **Description**: 
  - 实现 PostgreSQL 数据库表（用户表、预测记录表等）
  - 实现 TimescaleDB 超表（K 线数据存储）
  - 实现 Redis 缓存（行情数据、用户会话）
  - 实现历史预测记录的增删改查 API
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic`: 数据库表创建成功
  - `programmatic`: 预测记录可正确存储与查询
  - `programmatic`: Redis 缓存正常工作
- **Notes**: 参考 spec.md 中的数据模型设计

## [ ] Task 9: 前端历史记录与导出
- **Priority**: P1
- **Depends On**: Task 8, Task 7
- **Description**: 
  - 实现历史记录页面 UI
  - 实现历史预测搜索与筛选
  - 实现预测结果导出（PDF/Excel）
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic`: 历史记录可正确加载与显示
  - `programmatic`: 搜索与筛选功能正常
  - `human-judgement`: 导出报告格式美观、内容完整
- **Notes**: 优先实现简单的导出功能

## [ ] Task 10: 批量预测与子 Agent
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 实现 Kronos predict_batch 接口
  - 实现简化版子 Agent 并行委派
  - 实现批量预测任务管理
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic`: 批量预测 API 正常工作
  - `programmatic`: 10 资产预测完成 < 30s (Kronos-small)
- **Notes**: 利用 asyncio 或 Celery 实现异步任务

## [ ] Task 11: Cron 定时任务
- **Priority**: P1
- **Depends On**: Task 10
- **Description**: 
  - 实现 Cron 任务管理 API
  - 实现定时任务调度器
  - 实现任务状态监控
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic`: 定时任务可正确创建、编辑、删除
  - `programmatic`: 任务可准时触发执行
- **Notes**: 可以使用 APScheduler 库

## [ ] Task 12: 前端高级功能
- **Priority**: P1
- **Depends On**: Task 7
- **Description**: 
  - 实现预测中心页面（手动配置参数）
  - 实现定时任务管理页面
  - 实现暗色模式
  - 优化响应式体验
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `human-judgement`: 所有页面功能正常、交互流畅
  - `programmatic`: 暗色模式可正常切换
- **Notes**: 完善用户体验

## [ ] Task 13: 预测技能自学习（简化版）
- **Priority**: P2
- **Depends On**: Task 3
- **Description**: 
  - 实现用户偏好记忆存储
  - 实现高频预测场景的模板化
  - 实现预测参数的自动优化建议
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic`: 用户偏好可正确存储与检索
  - `human-judgement`: 系统能根据历史使用提供合理建议
- **Notes**: 简化版实现，暂不做完整的 Hermes Skill 系统

## [ ] Task 14: 管理端基础功能
- **Priority**: P2
- **Depends On**: Task 4
- **Description**: 
  - 实现模型管理 API（加载/卸载/查看）
  - 实现系统监控基础指标
  - 实现管理端页面
- **Acceptance Criteria Addressed**: AC-6, AC-7
- **Test Requirements**:
  - `programmatic`: 模型可正确加载与卸载
  - `human-judgement`: 管理端界面可用
- **Notes**: 仅实现核心管理功能

## [ ] Task 15: 测试、文档与部署优化
- **Priority**: P2
- **Depends On**: All previous tasks
- **Description**: 
  - 编写单元测试与集成测试
  - 编写项目文档（README、部署指南）
  - 优化 Docker Compose 配置
  - 性能优化与安全加固
- **Acceptance Criteria Addressed**: All ACs
- **Test Requirements**:
  - `programmatic`: 核心功能测试覆盖 > 80%
  - `human-judgement`: 文档完整、清晰
  - `programmatic`: 系统可通过 `docker compose up` 一键部署
- **Notes**: 确保项目可交付、可维护
