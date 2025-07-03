import openai
from typing import Dict, Any
import os
import json

class AIHelper:
    def __init__(self):
        # 确保设置了 OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        openai.api_key = self.api_key

    async def process_weather_query(self, query: str) -> Dict[str, Any]:
        """
        使用 OpenAI 分析天气查询
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """你是一个天气查询助手。
请分析用户的查询，提取以下信息：
1. 是否是天气查询
2. 城市名称
3. 用户关注的天气信息（如温度、湿度、风速等）
请用 JSON 格式返回结果。"""},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            # 解析返回的文本为 JSON
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
        """
        使用 OpenAI 生成自然语言天气回复
        """
        try:
            weather_info = json.dumps(weather_data, ensure_ascii=False)
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """你是一个友好的天气助手。
基于提供的天气数据，生成一个自然、友好的回复。
回复应该简洁明了，重点关注用户感兴趣的信息。"""},
                    {"role": "user", "content": f"请基于这些天气数据生成回复：{weather_info}"}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成回复时出错: {str(e)}")
            return f"{weather_data['city']}的天气：气温 {weather_data['temperature']}，{weather_data['description']}，湿度 {weather_data['humidity']}，风速 {weather_data['wind_speed']}" 