import os
import json
from openai import OpenAI
from typing import Dict, Any

class AIHelper:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 OPENROUTER_API_KEY 或 OPENAI_API_KEY 环境变量")
        
        # 初始化 OpenAI 客户端，支持 OpenRouter
        base_url = "https://api.openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else "https://api.openai.com/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/your-repo",  # 你的应用来源
                "X-Title": "Weather Bot",  # 你的应用名称
                "Authorization": f"Bearer {self.api_key}"
            } if os.getenv("OPENROUTER_API_KEY") else {}
        )

    async def process_natural_language(self, text: str) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125" if not os.getenv("OPENROUTER_API_KEY") else "openai/gpt-3.5-turbo",
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
                max_tokens=150
            )
            return json.loads(response.choices[0].message.content)
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
                model="gpt-3.5-turbo-0125" if not os.getenv("OPENROUTER_API_KEY") else "openai/gpt-3.5-turbo",
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
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API 调用出错: {str(e)}")
            return "抱歉，我在分析天气数据时遇到了问题。"

    async def process_weather_query(self, query: str) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125" if not os.getenv("OPENROUTER_API_KEY") else "openai/gpt-3.5-turbo",
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
                max_tokens=150
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
                model="gpt-3.5-turbo-0125" if not os.getenv("OPENROUTER_API_KEY") else "openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """你是一个友好的天气助手。
基于提供的天气数据，生成一个自然、友好的回复。
回复应该简洁明了，重点关注用户感兴趣的信息。"""
                    },
                    {"role": "user", "content": f"请基于这些天气数据生成回复：{weather_info}"}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成回复时出错: {str(e)}")
