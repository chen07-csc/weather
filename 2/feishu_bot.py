from fastapi import FastAPI, Request, HTTPException
import httpx
import json
import os
import openai
from config import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    OPENAI_API_KEY,
    WEATHER_API_KEY
)

app = FastAPI()

# 设置 OpenAI API key 和代理
openai.api_key = OPENAI_API_KEY
http_proxy = os.getenv("HTTP_PROXY", "")
https_proxy = os.getenv("HTTPS_PROXY", "")

if http_proxy or https_proxy:
    proxies = {
        "http": http_proxy,
        "https": https_proxy or http_proxy
    }
else:
    proxies = None

# 获取环境变量，用于 Railway 部署
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

async def get_feishu_token():
    """获取飞书 access token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    try:
        async with httpx.AsyncClient(proxies=proxies) as client:
            response = await client.post(url, json=data, headers=headers)
            return response.json()["tenant_access_token"]
    except Exception as e:
        print(f"获取飞书 token 时出错: {str(e)}")
        raise

async def send_feishu_message(token: str, chat_id: str, msg_type: str, content: str):
    """发送飞书消息"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    msg_content = {"text": content} if msg_type == "text" else content
    data = {
        "receive_id": chat_id,
        "msg_type": msg_type,
        "content": json.dumps(msg_content)
    }
    
    try:
        async with httpx.AsyncClient(proxies=proxies) as client:
            await client.post(url, json=data, headers=headers)
    except Exception as e:
        print(f"发送飞书消息时出错: {str(e)}")
        raise

async def get_weather(city: str) -> dict:
    """获取天气信息"""
    url = (
        f"http://api.openweathermap.org/data/2.5/weather?q={city}"
        f"&appid={WEATHER_API_KEY}&units=metric&lang=zh_cn"
    )
    
    try:
        async with httpx.AsyncClient(proxies=proxies) as client:
            response = await client.get(url)
            data = response.json()
            
            if "main" not in data:
                return {"error": f"未找到 {city} 的天气信息"}
                
            return {
                "city": city,
                "temperature": f"{data['main']['temp']} °C",
                "description": data["weather"][0]["description"],
                "humidity": f"{data['main']['humidity']}%",
                "wind_speed": f"{data['wind']['speed']} m/s"
            }
    except Exception as e:
        print(f"获取天气信息时出错: {str(e)}")
        return {"error": f"获取天气信息时出错: {str(e)}"}

async def process_natural_language(text: str) -> dict:
    """使用 OpenAI 处理自然语言查询"""
    try:
        client = openai.OpenAI(
            http_client=httpx.Client(proxies=proxies) if proxies else None
        )
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """你是一个天气查询助手。
请分析用户的查询，提取以下信息：
1. 城市名称
2. 查询意图（天气、温度、降水等）
3. 是否询问出行建议

请用 JSON 格式返回，格式如下：
{
    "city": "城市名称",
    "query_type": ["天气", "温度", ...],  # 查询类型
    "need_travel_advice": true/false,  # 是否需要出行建议
    "original_query": "原始查询"  # 保存原始查询用于天气服务
}"""},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"处理自然语言时出错: {str(e)}")
        # 如果 AI 处理失败，返回基本的解析结果
        return {
            "city": text.replace("天气", "").strip(),
            "query_type": ["天气"],
            "need_travel_advice": "出行" in text or "适合" in text,
            "original_query": text
        }

async def analyze_weather_for_outing(weather_data: dict) -> str:
    """使用 OpenAI 分析天气是否适合出行"""
    try:
        client = openai.OpenAI(
            http_client=httpx.Client(proxies=proxies) if proxies else None
        )
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """你是一个天气分析助手。
请根据提供的天气数据，分析今天是否适合出行，并给出建议。
考虑以下因素：
1. 温度是否适宜
2. 是否有降水
3. 风速是否适宜
4. 其他可能影响出行的天气因素

请用简洁友好的语气回复。"""},
                {"role": "user", "content": f"请分析这些天气数据，告诉我是否适合出行：{json.dumps(weather_data, ensure_ascii=False)}"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 调用出错: {str(e)}")
        return "抱歉，我在分析天气数据时遇到了问题。"

@app.post("/webhook")
async def handle_webhook(request: Request):
    """处理飞书 webhook 消息"""
    try:
        body = await request.json()
        
        # 处理飞书的 URL 验证
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}
        
        # 处理消息事件
        if body.get("header", {}).get("event_type") == "im.message.receive_v1":
            event = body.get("event", {})
            message_type = event.get("message", {}).get("message_type")
            
            if message_type == "text":
                # 获取消息内容
                content = json.loads(event["message"]["content"])
                text = content.get("text", "").strip()
                chat_id = event["message"]["chat_id"]
                
                try:
                    # 获取飞书 token
                    token = await get_feishu_token()
                    
                    # 首先处理自然语言查询
                    query_info = await process_natural_language(text)
                    
                    # 获取天气数据
                    weather_data = await get_weather(query_info["city"])
                    
                    if "error" in weather_data:
                        await send_feishu_message(
                            token, 
                            chat_id, 
                            "text", 
                            f"抱歉，{weather_data['error']}"
                        )
                        return {"status": "ok"}
                    
                    # 如果用户询问了出行建议，使用 OpenAI 分析
                    response_text = f"{query_info['city']}的天气：\n温度：{weather_data['temperature']}\n天气：{weather_data['description']}\n湿度：{weather_data['humidity']}\n风速：{weather_data['wind_speed']}"
                    
                    if query_info.get("need_travel_advice"):
                        analysis = await analyze_weather_for_outing(weather_data)
                        response_text = f"{response_text}\n\n出行建议：\n{analysis}"
                    
                    # 发送回复
                    await send_feishu_message(token, chat_id, "text", response_text)
                
                except Exception as e:
                    error_msg = f"处理消息时出错：{str(e)}"
                    print(error_msg)
                    await send_feishu_message(token, chat_id, "text", error_msg)
        
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"启动服务，监听 {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT) 
