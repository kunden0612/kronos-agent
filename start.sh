#!/bin/bash

echo "===================================="
echo "  Hermes-Kronos"
echo "  智能金融预测系统"
echo "===================================="
echo ""

cd "$(dirname "$0")"

echo "正在启动 Docker Compose 服务..."
docker compose up -d --build

echo ""
echo "===================================="
echo "  服务启动中，请稍候..."
echo "===================================="

for i in {1..20}; do
    echo -ne "  等待服务启动进度 ${i}%...\r"
    sleep 2
done

echo ""
echo ""
echo "===================================="
echo "  服务访问地址："
echo "===================================="
echo "  前端界面: http://localhost:3000"
echo "  后端API文档: http://localhost:8000/docs"
echo "  Kronos服务: http://localhost:8001/docs"
echo ""
echo "  默认凭据："
echo "  MinIO: minioadmin / minioadmin"
echo "  PostgreSQL: kronos / kronos"
echo ""
echo "  使用说明："
echo "  1. 访问 http://localhost:3000"
echo "  2. 注册账号并登录"
echo "  3. 开始对话，比如："
echo "     \"预测茅台未来5天的走势"
echo ""
echo "  4. 查看预测结果和图表"
echo ""
echo "  免责声明：本系统仅供学习交流使用，不构成投资建议！"
echo "===================================="
