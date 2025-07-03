from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uvicorn
import json
import re

from mcp_client import MCPClient
from feishu_bot import FeishuBot
from config import FEISHU_VERIFICATION_TOKEN

app = FastAPI()
mcp_client = MCPClient()
feishu_bot = FeishuBot()

def is_weather_query(text: str) -> bool:
    """
    判断是否是天气查询
    """
    weather_keywords = [
        "天气", "气温", "温度", "下雨", "下雪",
        "冷不冷", "热不热", "多少度", "weather"
    ]
    return any(keyword in text for keyword in weather_keywords)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Weather Bot is running"}

@app.post("/webhook/feishu")
async def feishu_webhook(request: Request):
    # 验证签名
    event_header = request.headers.get("X-Lark-Request-Timestamp")
    if not event_header:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # 获取请求体
    body = await request.body()
    event = json.loads(body)
    
    # 处理 URL 验证
    if event.get("type") == "url_verification":
        if event.get("token") != FEISHU_VERIFICATION_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"challenge": event.get("challenge")}
    
    # 处理消息事件
    if event.get("type") == "im.message.receive_v1":
        event_data = event.get("event", {})
        message = event_data.get("message", {})
        
        if message.get("message_type") != "text":
            return JSONResponse(content={"status": "ok"})
            
        try:
            # 解析消息内容
            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "").strip()
            
            # 判断是否是天气查询
            if is_weather_query(text):
                # 获取并发送天气信息
                weather_stream = mcp_client.stream_weather(text)
                await feishu_bot.send_weather_stream(
                    message.get("sender", {}).get("sender_id", {}).get("open_id"),
                    weather_stream
                )
            else:
                # 如果不是天气查询，发送帮助信息
                help_message = (
                    "👋 你好！我是天气助手，可以帮你查询天气信息。\n"
                    "🌤️ 你可以这样问我：\n"
                    "• 北京天气怎么样？\n"
                    "• 上海今天冷不冷？\n"
                    "• 广州下雨吗？\n"
                    "• 查询深圳天气\n"
                )
                await feishu_bot.send_message(
                    message.get("sender", {}).get("sender_id", {}).get("open_id"),
                    help_message
                )
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 