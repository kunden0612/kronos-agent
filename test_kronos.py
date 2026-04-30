"""Kronos Agent 完整测试套件"""

import sys
import logging
import tempfile
import shutil
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kronos-test')

def test_memory_system():
    """测试记忆系统"""
    print("\n" + "="*50)
    print("测试 1: 记忆系统 (Memory System)")
    print("="*50)
    
    try:
        from kronos.app import KronosAgent
        
        # 初始化代理
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "session_id": "test-session-1",
                "kronos_home": temp_dir
            }
            
            agent = KronosAgent(config).initialize()
            
            # 测试 1.1: 添加记忆
            print("\n[测试 1.1] 添加记忆")
            result = agent.handle_tool_call("memory_add", {
                "content": "测试记忆内容 - Kronos Agent 能力验证",
                "tags": ["test", "kronos"],
                "importance": "high"
            })
            print(f"结果: {result}")
            
            # 测试 1.2: 搜索记忆
            print("\n[测试 1.2] 搜索记忆")
            result = agent.handle_tool_call("memory_search", {
                "query": "kronos"
            })
            print(f"结果: {result}")
            
            # 测试 1.3: 列出记忆
            print("\n[测试 1.3] 列出所有记忆")
            result = agent.handle_tool_call("memory_list", {})
            print(f"结果: {result}")
            
            # 测试 1.4: 添加项目
            print("\n[测试 1.4] 添加项目")
            result = agent.handle_tool_call("project_add", {
                "name": "Kronos Test Project",
                "path": "/test/path",
                "description": "测试项目",
                "tags": ["test", "project"]
            })
            print(f"结果: {result}")
            
            # 测试 1.5: 设置用户偏好
            print("\n[测试 1.5] 设置用户偏好")
            result = agent.handle_tool_call("set_preference", {
                "key": "theme",
                "value": "dark",
                "category": "ui"
            })
            print(f"结果: {result}")
            
            # 测试 1.6: 获取偏好
            print("\n[测试 1.6] 获取偏好")
            result = agent.handle_tool_call("get_preference", {
                "key": "theme",
                "category": "ui"
            })
            print(f"结果: {result}")
            
            # 测试 1.7: 获取代理状态
            print("\n[测试 1.7] 获取代理状态")
            result = agent.handle_tool_call("agent_status", {})
            print(f"结果: {result}")
            
            # 测试 1.8: 列出工具类别
            print("\n[测试 1.8] 列出工具类别")
            result = agent.handle_tool_call("list_categories", {})
            print(f"结果: {result}")
            
            agent.shutdown()
            print("\n✅ 记忆系统测试通过！")
            return True
            
    except Exception as e:
        logger.error(f"记忆系统测试失败: {e}", exc_info=True)
        print(f"❌ 记忆系统测试失败: {e}")
        return False


def test_skill_system():
    """测试技能系统"""
    print("\n" + "="*50)
    print("测试 2: 技能系统 (Skill System)")
    print("="*50)
    
    try:
        from kronos.app import KronosAgent
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "session_id": "test-session-2",
                "kronos_home": temp_dir
            }
            
            agent = KronosAgent(config).initialize()
            
            # 测试 2.1: 创建技能
            print("\n[测试 2.1] 创建技能")
            result = agent.handle_tool_call("skill_create", {
                "name": "Test Skill",
                "description": "测试技能 - Kronos Agent",
                "content": "这是一个测试技能的内容，说明如何使用。",
                "tags": ["test", "skill", "kronos"]
            })
            print(f"结果: {result}")
            
            # 测试 2.2: 搜索技能
            print("\n[测试 2.2] 搜索技能")
            result = agent.handle_tool_call("skill_search", {
                "query": "Test"
            })
            print(f"结果: {result}")
            
            # 测试 2.3: 列出技能
            print("\n[测试 2.3] 列出技能")
            result = agent.handle_tool_call("skill_list", {})
            print(f"结果: {result}")
            
            # 测试 2.4: 生成技能（从任务）
            print("\n[测试 2.4] 从任务生成技能")
            result = agent.handle_tool_call("skill_generate", {
                "task": "完成一个自动化测试",
                "solution": "运行 test_kronos.py 脚本即可",
                "name": "Automated Testing"
            })
            print(f"结果: {result}")
            
            # 测试 2.5: 技能状态检查
            print("\n[测试 2.5] 检查技能状态")
            result = agent.handle_tool_call("skill_status", {})
            print(f"结果: {result}")
            
            agent.shutdown()
            print("\n✅ 技能系统测试通过！")
            return True
            
    except Exception as e:
        logger.error(f"技能系统测试失败: {e}", exc_info=True)
        print(f"❌ 技能系统测试失败: {e}")
        return False


def test_cron_system():
    """测试定时任务系统"""
    print("\n" + "="*50)
    print("测试 3: 定时任务系统 (Cron System)")
    print("="*50)
    
    try:
        from kronos.app import KronosAgent
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "session_id": "test-session-3",
                "kronos_home": temp_dir
            }
            
            agent = KronosAgent(config).initialize()
            
            # 测试 3.1: 验证 cron 表达式
            print("\n[测试 3.1] 验证 Cron 表达式")
            result = agent.handle_tool_call("cron_validate", {
                "cron_expr": "0 9 * * *"
            })
            print(f"结果: {result}")
            
            # 测试 3.2: 添加 cron 任务
            print("\n[测试 3.2] 添加 Cron 任务")
            result = agent.handle_tool_call("cron_add", {
                "name": "Daily Report",
                "command": "echo 'Daily Report' >> /tmp/report.txt",
                "cron_expr": "0 9 * * *",
                "description": "每日报告任务",
                "tags": ["report", "daily"]
            })
            print(f"结果: {result}")
            
            # 测试 3.3: 列出任务
            print("\n[测试 3.3] 列出所有 Cron 任务")
            result = agent.handle_tool_call("cron_list", {})
            print(f"结果: {result}")
            
            agent.shutdown()
            print("\n✅ 定时任务系统测试通过！")
            return True
            
    except Exception as e:
        logger.error(f"定时任务系统测试失败: {e}", exc_info=True)
        print(f"❌ 定时任务系统测试失败: {e}")
        return False


def test_subagent_system():
    """测试子智能体系统"""
    print("\n" + "="*50)
    print("测试 4: 子智能体系统 (Subagent System)")
    print("="*50)
    
    try:
        from kronos.app import KronosAgent
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "session_id": "test-session-4",
                "kronos_home": temp_dir
            }
            
            agent = KronosAgent(config).initialize()
            
            # 测试 4.1: 单个子智能体任务
            print("\n[测试 4.1] 单个子智能体任务")
            result = agent.handle_tool_call("delegate_task", {
                "goal": "执行一个简单的测试任务"
            })
            print(f"结果: {result}")
            
            # 测试 4.2: 列出子智能体
            print("\n[测试 4.2] 列出当前子智能体")
            result = agent.handle_tool_call("list_subagents", {})
            print(f"结果: {result}")
            
            # 测试 4.3: 暂停/恢复子智能体生成
            print("\n[测试 4.3] 暂停/恢复子智能体生成")
            result = agent.handle_tool_call("pause_subagents", {})
            print(f"暂停结果: {result}")
            
            result = agent.handle_tool_call("resume_subagents", {})
            print(f"恢复结果: {result}")
            
            agent.shutdown()
            print("\n✅ 子智能体系统测试通过！")
            return True
            
    except Exception as e:
        logger.error(f"子智能体系统测试失败: {e}", exc_info=True)
        print(f"❌ 子智能体系统测试失败: {e}")
        return False


def test_browser_system():
    """测试浏览器控制工具"""
    print("\n" + "="*50)
    print("测试 5: 浏览器控制 (Browser Tool)")
    print("="*50)
    
    try:
        from kronos.app import KronosAgent
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "session_id": "test-session-5",
                "kronos_home": temp_dir
            }
            
            agent = KronosAgent(config).initialize()
            
            # 测试 5.1: 导航到 URL
            print("\n[测试 5.1] 浏览器导航")
            result = agent.handle_tool_call("browser_navigate", {
                "url": "https://example.com"
            })
            print(f"结果: {result}")
            
            # 测试 5.2: 页面快照
            print("\n[测试 5.2] 页面快照")
            result = agent.handle_tool_call("browser_snapshot", {})
            print(f"结果: {result}")
            
            # 测试 5.3: 控制台
            print("\n[测试 5.3] 浏览器控制台")
            result = agent.handle_tool_call("browser_console", {
                "expression": "document.title"
            })
            print(f"结果: {result}")
            
            agent.shutdown()
            print("\n✅ 浏览器控制测试通过！")
            return True
            
    except Exception as e:
        logger.error(f"浏览器控制测试失败: {e}", exc_info=True)
        print(f"❌ 浏览器控制测试失败: {e}")
        return False


def test_integration():
    """集成测试 - 所有系统一起工作"""
    print("\n" + "="*50)
    print("测试 6: 集成测试 (Integration Test)")
    print("="*50)
    
    try:
        from kronos.app import KronosAgent
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "session_id": "integration-test",
                "kronos_home": temp_dir
            }
            
            agent = KronosAgent(config).initialize()
            
            # 显示完整能力
            print("\n[集成测试 1] 显示代理能力")
            result = agent.handle_tool_call("agent_capabilities", {})
            print(f"结果: {result}")
            
            # 最终状态检查
            print("\n[集成测试 2] 最终状态")
            result = agent.handle_tool_call("agent_status", {})
            print(f"结果: {result}")
            
            agent.shutdown()
            print("\n✅ 集成测试通过！")
            return True
            
    except Exception as e:
        logger.error(f"集成测试失败: {e}", exc_info=True)
        print(f"❌ 集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  Kronos Agent 完整测试套件")
    print("="*60)
    print(f"\nPython 版本: {sys.version}")
    print(f"当前目录: {Path.cwd()}")
    
    results = []
    
    # 执行所有测试
    results.append(("记忆系统", test_memory_system()))
    results.append(("技能系统", test_skill_system()))
    results.append(("定时任务", test_cron_system()))
    results.append(("子智能体", test_subagent_system()))
    results.append(("浏览器控制", test_browser_system()))
    results.append(("集成测试", test_integration()))
    
    # 总结
    print("\n" + "="*60)
    print("  测试结果总结")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:20s} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*60)
    print(f"  总计: {len(results)} | 通过: {passed} | 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！Kronos Agent 部署成功！")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {failed} 个测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
