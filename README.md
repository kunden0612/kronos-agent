# Hermes-Kronos - 智能金融预测系统

融合 Hermes Agent（自进化智能体）与 Kronos 模型（金融 K 线基础模型）的端到端智能金融预测系统。

## 项目概述

本项目提供以下功能：
- **自然语言预测**: 用户通过文本输入预测需求
- **多资产支持**: A股、美股、加密货币
- **K线可视化**: 历史数据与预测结果的图表展示
- **批量预测**: 支持多资产并行预测
- **定时任务**: 基于 Cron 的预测任务调度

## 项目结构

```
kronos-agent/
├── frontend/          # 前端代码 (待开发)
├── backend/           # 后端 API 网关 (待开发)
├── kronos/            # Kronos 预测服务
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── models/   # 数据模型
│   │   ├── services/ # 业务逻辑
│   │   └── config.py # 配置
│   ├── tests/        # 测试
│   ├── Dockerfile
│   └── requirements.txt
├── docs/              # 文档
├── scripts/           # 辅助脚本
├── .trae/            # Trae 规范文档
│   └── specs/
│       ├── spec.md
│       ├── tasks.md
│       └── checklist.md
├── docker-compose.yml # Docker Compose 配置
└── README.md
```

## 技术栈

### Kronos 预测服务
- **FastAPI**: Web 框架
- **PyTorch**: 深度学习框架（预留，当前为简化版）
- **Pandas/Numpy**: 数据处理
- **AkShare**: A股数据
- **yfinance**: 美股数据
- **ccxt**: 加密货币数据

### 基础设施
- **PostgreSQL/TimescaleDB**: 时序数据库
- **Redis**: 缓存
- **MinIO**: 对象存储
- **Docker Compose**: 容器编排

## 快速开始

### 环境要求

- Docker
- Docker Compose

### 启动服务

```bash
docker compose up -d --build
```

这将启动以下服务：

- **PostgreSQL/TimescaleDB**: 端口 5432
- **Redis**: 端口 6379
- **MinIO**: 端口 9000 (API) 和 9001 (控制台)
- **Kronos Service**: 端口 8001

### 服务访问

- **Backend API 文档**: http://localhost:8000/docs
- **Kronos API 文档**: http://localhost:8001/docs
- **MinIO 控制台**: http://localhost:9001 (默认凭据: minioadmin / minioadmin)
- **PostgreSQL**: localhost:5432 (默认凭据: kronos / kronos)
- **Redis**: localhost:6379

### API 测试

#### Backend API（推荐使用）
1. 访问 Swagger UI: http://localhost:8000/docs
2. 测试聊天: POST `/api/v1/chat`

示例聊天请求：
```json
{
  "message": "预测茅台未来5天的走势"
}
```

#### Kronos API（直接调用）
1. 访问 Swagger UI: http://localhost:8001/docs
2. 测试健康检查: GET `/api/v1/health`
3. 测试预测: POST `/api/v1/predict`

示例预测请求：
```json
{
  "symbol": "AAPL",
  "pred_len": 5,
  "lookback": 100
}
```

## 开发指南

### 本地运行 Kronos 服务

```bash
cd kronos
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 运行测试

```bash
cd kronos
python tests/test_basic.py
```

## API 接口

### 预测相关
- `POST /api/v1/predict` - 单资产预测
- `POST /api/v1/predict/batch` - 批量预测
- `GET /api/v1/models` - 查看已加载模型
- `POST /api/v1/models/load` - 加载模型
- `POST /api/v1/models/unload` - 卸载模型

### 系统相关
- `GET /api/v1/health` - 健康检查
- `GET /` - 服务信息

## 免责声明

⚠️ **重要提示**: 本系统提供的预测结果基于历史数据与机器学习模型生成，**不构成任何投资建议**。金融市场有风险，投资需谨慎。用户应独立判断并承担投资风险。

## 开发进度

- ✅ Task 1: 项目脚手架与基础设施搭建
- ✅ Task 2: Kronos 预测服务核心实现
- ✅ Task 3: 简化版 Hermes Agent 与 Tool Calling
- ✅ Task 4: API 网关与身份认证
- ✅ Task 5-6: 前端基础框架与路由 / K 线图与预测可视化
- 🔄 Task 7-15: 对话界面 / 数据持久化 / 批量预测 / 定时任务 / 高级功能 / 预测技能自学习 / 管理端基础功能 / 测试文档部署优化

## License

MIT
