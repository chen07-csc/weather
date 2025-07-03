#!/bin/bash

# 检查环境变量是否设置
if [ -z "$OPENAI_API_KEY" ]; then
    echo "错误: 请设置 OPENAI_API_KEY 环境变量"
    exit 1
fi

if [ -z "$WEATHER_API_KEY" ]; then
    echo "错误: 请设置 WEATHER_API_KEY 环境变量"
    exit 1
fi

if [ -z "$FEISHU_APP_ID" ] || [ -z "$FEISHU_APP_SECRET" ]; then
    echo "错误: 请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量"
    exit 1
fi

# 设置 MCP URL
export MCP_URL="http://localhost:8000"

# 启动 MCP 天气服务（在后台运行）
echo "启动 MCP 天气服务..."
python3 weather1.py &

# 等待几秒钟确保 MCP 服务启动
sleep 3

# 启动飞书机器人服务
echo "启动飞书机器人服务..."
python3 feishu_bot.py

# 等待用户按 Ctrl+C
echo "Services are running. Press Ctrl+C to stop..."
wait $MCP_PID $BOT_PID

# 捕获 Ctrl+C 信号
trap 'kill $MCP_PID $BOT_PID; exit' INT

# 等待进程结束
wait 