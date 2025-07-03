import os
import json
from openai import OpenAI
import httpx
from typing import Dict, Any
from config import DEEPSEEK_API_KEY

class AIHelper:
    def __init__(self):
        # 初始化 DeepSeek 客户端
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")
        proxies = None
        if http_proxy or https_proxy:
            proxies = {
                "http": http_proxy,
                "https": https_proxy or http_proxy
            }
        
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",  # 使用官方推荐的 base URL
            http_client=httpx.AsyncClient(
                proxies=proxies,
                timeout=30.0,
                verify=False if os.getenv("SKIP_VERIFY", "").lower() == "true" else True
            ) if proxies or os.getenv("SKIP_VERIFY", "").lower() == "true" else None
        )

    async def process_natural_language(self, text: str) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",  # 使用官方推荐的模型名称
                messages=[
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
}"""
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=150,
                stream=False  # 明确指定不使用流式响应
            )
            return json.loads(response.choices[0].message.content)
        except httpx.ConnectError as e:
            print(f"连接错误: {str(e)}. 请检查网络连接和代理设置。")
            return {
                "city": text.replace("天气", "").strip(),
                "query_type": ["天气"],
                "need_travel_advice": "出行" in text or "适合" in text,
                "original_query": text
            }
        except Exception as e:
            print(f"处理自然语言时出错: {str(e)}")
            return {
                "city": text.replace("天气", "").strip(),
                "query_type": ["天气"],
                "need_travel_advice": "出行" in text or "适合" in text,
                "original_query": text
            }

    async def analyze_weather_for_outing(self, weather_data: dict) -> str:
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": """你是一个天气分析助手。
请根据提供的天气数据，分析今天是否适合出行，并给出建议。
考虑以下因素：
1. 温度是否适宜
2. 是否有降水
3. 风速是否适宜
4. 其他可能影响出行的天气因素

请用简洁友好的语气回复。"""
                    },
                    {"role": "user", "content": f"请分析这些天气数据，告诉我是否适合出行：{json.dumps(weather_data, ensure_ascii=False)}"}
                ],
                temperature=0.7,
                max_tokens=200,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"DeepSeek API 调用出错: {str(e)}")
            return "抱歉，我在分析天气数据时遇到了问题。"

    async def process_weather_query(self, query: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": """你是一个天气查询助手。
请分析用户的查询，提取以下信息：
1. 是否是天气查询
2. 城市名称
3. 用户关注的天气信息（如温度、湿度、风速等）
请用 JSON 格式返回结果。"""
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=150,
                stream=False
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "is_weather_query": result.get("is_weather_query", False),
                "city": result.get("city", ""),
                "focus": result.get("focus", ["天气"])
            }
        except Exception as e:
            print(f"AI 处理查询时出错: {str(e)}")
            return {"is_weather_query": False, "city": "", "focus": []}

    async def generate_weather_response(self, weather_data: Dict[str, Any]) -> str:
        try:
            weather_info = json.dumps(weather_data, ensure_ascii=False)
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": """你是一个友好的天气助手。
基于提供的天气数据，生成一个自然、友好的回复。
回复应该简洁明了，重点关注用户感兴趣的信息。"""
                    },
                    {"role": "user", "content": f"请基于这些天气数据生成回复：{weather_info}"}
                ],
                temperature=0.7,
                max_tokens=150,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成回复时出错: {str(e)}")
            return f"{weather_data['city']}的天气：气温 {weather_data['temperature']}，{weather_data['description']}，湿度 {weather_data['humidity']}，风速 {weather_data['wind_speed']}"
