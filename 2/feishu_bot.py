from fastapi import FastAPI, Request, HTTPException
import httpx
import json
import os
from openai import AsyncOpenAI
import asyncio
from typing import Optional
from config import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    OPENAI_API_KEY,
    WEATHER_API_KEY
)

app = FastAPI()

# 初始化 OpenAI Async 客户端（支持 OpenRouter）
client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY") or OPENAI_API_KEY,
    base_url="https://api.openrouter.ai/api/v1",
    timeout=30.0,
    default_headers={
        "HTTP-Referer": "https://github.com/your-repo",  # 你的应用来源
        "X-Title": "Weather Bot",  # 你的应用名称
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY') or OPENAI_API_KEY}"
    }
)

# 获取环境变量，用于 Railway 部署
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# 重试配置
MAX_RETRIES = 5
RETRY_DELAY = 2  # 秒

async def retry_async(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func(*args)
        except Exception as e:
            last_error = e
            print(f"第 {attempt + 1} 次尝试失败: {str(e)}")
            if attempt < max_retries - 1:
                retry_delay = delay * (2 ** attempt)
                print(f"等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
    raise last_error

async def get_feishu_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    async with httpx.AsyncClient(timeout=30.0) as client_http:
        response = await client_http.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()["tenant_access_token"]

async def send_feishu_message(token: str, chat_id: str, msg_type: str, content: str):
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
    async with httpx.AsyncClient(timeout=30.0) as client_http:
        response = await client_http.post(url, json=data, headers=headers)
        response.raise_for_status()

async def get_weather(city: str) -> dict:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?q={city}"
        f"&appid={WEATHER_API_KEY}&units=metric&lang=zh_cn"
    )
    async with httpx.AsyncClient(timeout=30.0) as client_http:
        response = await client_http.get(url)
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

async def call_openai_with_retry(messages: list, max_tokens: int = 150) -> Optional[str]:
    async def _call():
        response = await client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    return await retry_async(_call)

async def process_natural_language(text: str) -> dict:
    messages = [
        {"role": "system", "content": """你是一个天气查询助手。
请分析用户的查询，提取以下信息：
1. 城市名称
2. 查询意图（天气、温度、降水等）
3. 是否询问出行建议

请用 JSON 格式返回，格式如下：
{
    "city": "城市名称",
    "query_type": ["天气", "温度", ...],
    "need_travel_advice": true/false,
    "original_query": "原始查询"
}"""}, 
        {"role": "user", "content": text}
    ]
    try:
        response_text = await call_openai_with_retry(messages)
        return json.loads(response_text)
    except Exception as e:
        print(f"处理自然语言时出错: {str(e)}")
        return {
            "city": text.replace("天气", "").strip(),
            "query_type": ["天气"],
            "need_travel_advice": "出行" in text or "适合" in text,
            "original_query": text
        }

async def analyze_weather_for_outing(weather_data: dict) -> str:
    messages = [
        {"role": "system", "content": """你是一个天气分析助手。
请根据提供的天气数据，分析今天是否适合出行，并给出建议。
考虑以下因素：
1. 温度是否适宜
2. 是否有降水
3. 风速是否适宜
4. 其他可能影响出行的天气因素

请用简洁友好的语气回复。"""}, 
        {"role": "user", "content": f"请分析这些天气数据，告诉我是否适合出行：{json.dumps(weather_data, ensure_ascii=False)}"}
    ]
    try:
        response_text = await call_openai_with_retry(messages, max_tokens=200)
        return response_text
    except Exception as e:
        print(f"OpenAI API 调用出错: {str(e)}")
        return "抱歉，我在分析天气数据时遇到了问题。"

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        body = await request.json()
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}
        if body.get("header", {}).get("event_type") == "im.message.receive_v1":
            event = body.get("event", {})
            message_type = event.get("message", {}).get("message_type")
            if message_type == "text":
                content = json.loads(event["message"]["content"])
                text = content.get("text", "").strip()
                chat_id = event["message"]["chat_id"]
                token = await get_feishu_token()
                query_info = await process_natural_language(text)
                weather_data = await get_weather(query_info["city"])
                if "error" in weather_data:
                    await send_feishu_message(token, chat_id, "text", f"抱歉，{weather_data['error']}")
                    return {"status": "ok"}
                response_text = (
                    f"{query_info['city']}的天气：\n温度：{weather_data['temperature']}\n天气：{weather_data['description']}"
                    f"\n湿度：{weather_data['humidity']}\n风速：{weather_data['wind_speed']}"
                )
                if query_info.get("need_travel_advice"):
                    analysis = await analyze_weather_for_outing(weather_data)
                    response_text = f"{response_text}\n\n出行建议：\n{analysis}"
                await send_feishu_message(token, chat_id, "text", response_text)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"启动服务，监听 {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

