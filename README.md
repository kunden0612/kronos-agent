# Kronos Agent

基于 Hermes Agent 核心能力的智能代理系统。

## ✅ 已实现功能

1. **持久记忆系统** - 跨会话记住用户偏好、项目和环境
2. **自动技能创建** - 解决难题时自动创建可重用的技能文档，兼容 agentskills.io 标准
3. **定时自动化任务** - 内置 Cron 调度器，支持每日报告、夜间备份等自动化任务
4. **并行子智能体** - 为并行工作流生成隔离的子智能体
5. **完整浏览器控制** - 网页导航、页面提取、浏览器自动化

## 🚀 快速开始

### 安装依赖

```bash
cd kronos-agent
pip install -r requirements.txt
```

### 运行测试

```bash
python test_kronos.py
```

### 使用示例

```python
from kronos.app import KronosAgent

# 初始化代理
agent = KronosAgent().initialize()

# 使用工具
result = agent.handle_tool_call("memory_add", {
    "content": "重要的项目信息",
    "tags": ["project", "important"]
})

# 完成后关闭代理
agent.shutdown()
```

## 📦 项目结构

```
kronos-agent/
├── kronos/
│   └── app/
│       ├── __init__.py       # 主入口和工具注册
│       ├── memory.py       # 持久记忆系统
│       ├── skills.py       # 技能管理系统
│       ├── cron.py         # 定时任务调度器
│       ├── subagent.py   # 并行子智能体
│       └── browser.py      # 浏览器控制工具
├── requirements.txt        # 项目依赖
└── test_kronos.py      # 完整测试套件
```

## 🧪 测试结果

| 模块            | 状态 |
|----------------|------|
| 记忆系统         | ✅ 通过 |
| 技能系统         | ✅ 通过 |
| 定时任务         | ✅ 通过 |
| 子智能体         | ✅ 通过 |
| 浏览器控制        | ✅ 通过 |
| 集成测试         | ✅ 通过 |

所有 6 个核心模块测试全部通过！

## 📜 许可证

MIT License
