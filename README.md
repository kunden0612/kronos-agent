# Hermes-Kronos - 智能金融预测系统

基于 **Hermes Agent**（NousResearch 自进化智能体）与 **Kronos 模型**（金融 K 线基础模型）的端到端智能金融预测系统。

## 🎯 核心特性

- **真正的 Hermes Agent 集成**: 使用 NousResearch 的 Hermes-agent 框架完整能力
- **自然语言预测**: 通过对话描述需求，Agent 自动调用 Kronos 模型
- **多资产支持**: A股、美股、加密货币
- **自进化学习**: Hermes Agent 的技能自动学习与持久记忆
- **K线可视化**: 预测结果叠加置信区间
- **批量预测**: 多资产并行分析
- **定时任务**: Cron 驱动的自动化预测
- **完整工具调用**: 继承 Hermes 的全部工具能力

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    React Frontend (Port 3000)                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  - Login/Register                                        │   │
│   │  - Chat Interface                                        │   │
│   │  - K-line Visualization                                  │   │
│   │  - WebSocket Streaming                                   │   │
│   └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬────────────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼────────────────────────────────────────┐
│              FastAPI Backend Gateway (Port 8000)                 │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  - JWT Authentication                                      │   │
│   │  - Hermes AIAgent Integration                             │   │
│   │  - Kronos Tools Registration                              │   │
│   │  - Session Management                                     │   │
│   │  - Streaming Responses                                    │   │
│   └─────────────────────────────────────────────────────────────┘   │
└────┬──────────────────────┬───────────────────────────────────────┘
     │                      │
┌────▼────────┐     ┌──────▼──────────────────────────────┐
│  Kronos     │     │         Hermes Agent Container     │
│  Service    │◄───│  - AIAgent with full capabilities   │
│  (Port 8001)│     │  - Tool calling loop              │
└─────────────┘     │  - Memory management              │
     │              │  - Context compression            │
┌────▼─────────────┐│  - Subagent delegation           │
│  Data Sources    ││  - Skill learning                │
│  - AkShare       ││  - Session DB                    │
│  - YFinance      │└──────────────────────────────────┘
│  - CCXT          │
└──────────────────┘
```

## 🧠 Hermes Agent 完整集成

本项目使用真正的 **Hermes-agent** 框架（NousResearch 开源），继承其全部核心能力。

### 核心能力

| 能力 | 描述 |
|------|------|
| **AIAgent** | 完整的对话循环实现 |
| **Tool Calling** | 自动工具调用与结果整合 |
| **持久记忆** | 跨会话记忆管理 |
| **技能学习** | 自动技能创建与改进 |
| **子 Agent 委派** | 并行处理复杂任务 |
| **定时任务** | Cron 驱动的自动化 |
| **上下文压缩** | 智能上下文管理 |
| **流式响应** | Token-by-token 流式输出 |

### Kronos 工具注册

遵循 Hermes 的 `tools/registry.py` 模式注册自定义工具：

```python
registry.register(
    name="kronos_predict",
    toolset="kronos",
    schema={...},
    handler=kronos_predict_tool,
    check_fn=check_kronos_requirements,
    requires_env=[],
)
```

### 配置模型

编辑 `backend/.env`:

```bash
HERMES_PROVIDER=openrouter
HERMES_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=your-key
```

## 📁 项目结构

```
kronos-agent/
├── frontend/              # React 前端
│   ├── src/
│   │   ├── pages/        # Login, Home
│   │   ├── services/     # API 客户端
│   │   └── store/        # Zustand 状态
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/      # API 路由
│   │   ├── core/        # 配置、安全
│   │   ├── models/      # Pydantic 模型
│   │   ├── services/    # Hermes Agent 服务
│   │   │   └── hermes_agent_service.py  # 完整 Hermes 集成
│   │   └── tools/       # Kronos 工具
│   └── requirements.txt
├── kronos/               # Kronos 预测服务
│   ├── app/
│   │   ├── api/v1/      # 预测 API
│   │   ├── models/      # 数据模型
│   │   └── services/    # 数据获取、预测
│   └── requirements.txt
├── docker-compose.yml     # 容器编排
└── README.md
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/kunden0612/kronos-agent.git
cd kronos-agent
git checkout dev-2026-04-30
```

### 2. 配置环境

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，配置您的 API keys
```

### 3. 启动服务

```bash
docker compose up -d --build
```

### 4. 访问应用

- 前端界面: http://localhost:3000
- 后端 API 文档: http://localhost:8000/docs
- Kronos 服务: http://localhost:8001/docs

## 💬 使用示例

注册并登录后，尝试以下对话：

```
用户: 预测茅台未来5天的走势
Hermes: 正在调用 kronos_predict 工具...

[图表显示预测结果]

预测解读：茅台股价未来5个交易日预计呈温和上涨趋势，
平均波动率约为2.5%，建议关注成交量变化。

⚠️ 风险提示：模型基于历史数据与机器学习生成，
不构成投资建议。市场有风险，投资需谨慎。
```

## 🔧 开发

### 本地运行后端

```bash
cd backend
pip install -r requirements.txt
export HERMES_AGENT_PATH=/workspace/hermes-agent
uvicorn app.main:app --reload --port 8000
```

### 本地运行 Kronos 服务

```bash
cd kronos
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 本地运行前端

```bash
cd frontend
npm install
npm run dev
```

## 📋 API 接口

### 聊天接口
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat` | POST | Hermes Agent 对话 |
| `/api/v1/chat/conversation` | POST | 完整对话流程 |
| `/api/v1/chat/stream` | WebSocket | 流式响应 |

### Agent 管理
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/agent/initialize` | POST | 初始化 Agent |
| `/api/v1/agent/capabilities` | GET | 获取能力信息 |
| `/api/v1/agent/tools` | GET | 获取工具列表 |
| `/api/v1/agent/tools/{tool_name}` | POST | 直接调用工具 |
| `/api/v1/agent/session` | POST | 创建会话 |
| `/api/v1/agent/session/{id}` | GET/DELETE | 获取/删除会话 |

### 预测接口
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/predict` | POST | 直接调用 Kronos 预测 |
| `/api/v1/predict/batch` | POST | 批量预测 |

### 认证接口
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/register` | POST | 用户注册 |
| `/api/v1/login` | POST | 用户登录 |
| `/api/v1/users/me` | GET | 获取当前用户 |

## 🛠️ 技术栈

### 后端
- **Hermes-agent**: NousResearch 自进化智能体框架
- **FastAPI**: 现代 Python Web 框架
- **Pydantic**: 数据验证

### 前端
- **React 18**: 用户界面
- **TypeScript**: 类型安全
- **Ant Design**: UI 组件库
- **ECharts**: 数据可视化
- **Zustand**: 状态管理

### 预测服务
- **PyTorch**: 深度学习（预留）
- **AkShare**: A股数据
- **YFinance**: 美股数据
- **CCXT**: 加密货币

### 基础设施
- **Docker Compose**: 容器编排
- **PostgreSQL/TimescaleDB**: 数据库
- **Redis**: 缓存
- **MinIO**: 对象存储

## ⚠️ 免责声明

**重要提示**: 本系统提供的预测结果基于历史数据与机器学习模型生成，**不构成任何投资建议**。金融市场有风险，投资需谨慎。用户应独立判断并承担投资风险。

## 📚 文档

- [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs/)
- [Kronos 模型 GitHub](https://github.com/shiyu-coder/Kronos)
- [API 文档](http://localhost:8000/docs)（启动后访问）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
