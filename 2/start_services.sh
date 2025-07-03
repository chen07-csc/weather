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

# 启动飞书机器人服务
python feishu_bot.py &

# 启动天气服务
python weather1.py &

# 等待所有后台进程
wait

# 捕获 Ctrl+C 信号
trap 'kill $MCP_PID $BOT_PID; exit' INT

# 等待进程结束
wait 
